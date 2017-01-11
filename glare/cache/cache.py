# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
LRU Cache for Blob Data
"""

import hashlib

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import encodeutils
from oslo_utils import excutils
from oslo_utils import importutils
from oslo_utils import units

from glare.common import exception
from glare.common import utils
from glare.i18n import _, _LE, _LI, _LW

LOG = logging.getLogger(__name__)

blob_cache_opts = [
    cfg.StrOpt('blob_cache_driver', default='sqlite',
               choices=('sqlite', 'xattr'), ignore_case=True,
               help=_("""
The driver to use for blob cache management.
This configuration option provides the flexibility to choose between the
different blob-cache drivers available. a blob-cache driver is responsible
for providing the essential functions of blob-cache like write blobs to/read
blobs from cache, track age and usage of cached blobs, provide a list of
cached blobs, fetch size of the cache, queue blobs for caching and clean up
the cache, etc.
The essential functions of a driver are defined in the base class
``glare.cache.drivers.base.Driver``. All blob-cache drivers (existing
and prospective) must implement this interface. Currently available drivers
are ``sqlite`` and ``xattr``. These drivers primarily differ in the way they
store the information about cached blobs:
    * The ``sqlite`` driver uses a sqlite database (which sits on every glare
    node locally) to track the usage of cached blobs.
    * The ``xattr`` driver uses the extended attributes of files to store this
    information. It also requires a filesystem that sets ``atime`` on the files
    when accessed.
Possible values:
    * sqlite
    * xattr
Related options:
    * None
""")),

    cfg.IntOpt('blob_cache_max_size', default=10 * units.Gi,  # 10 GB
               min=0,
               help=_("""
The upper limit on cache size, in bytes, after which the cache-pruner cleans
up the blob cache.
NOTE: This is just a threshold for cache-pruner to act upon. It is NOT a
hard limit beyond which the blob cache would never grow. In fact, depending
on how often the cache-pruner runs and how quickly the cache fills, the blob
cache can far exceed the size specified here very easily. Hence, care must be
taken to appropriately schedule the cache-pruner and in setting this limit.
Glare caches a blob when it is downloaded. Consequently, the size of the
blob cache grows over time as the number of downloads increases. To keep the
cache size from becoming unmanageable, it is recommended to run the
cache-pruner as a periodic task. When the cache pruner is kicked off, it
compares the current size of blob cache and triggers a cleanup if the blob
cache grew beyond the size specified here. After the cleanup, the size of
cache is less than or equal to size specified here.
Possible values:
    * Any non-negative integer
Related options:
    * None
""")),

    cfg.IntOpt('blob_cache_stall_time', default=86400,  # 24 hours
               min=0,
               help=_("""
The amount of time, in seconds, an incomplete blob remains in the cache.
Incomplete blobs are blobs for which download is in progress. Please see the
description of configuration option ``blob_cache_dir`` for more detail.
Sometimes, due to various reasons, it is possible the download may hang and
the incompletely downloaded blob remains in the ``incomplete`` directory.
This configuration option sets a time limit on how long the incomplete blobs
should remain in the ``incomplete`` directory before they are cleaned up.
Once an incomplete blob spends more time than is specified here, it'll be
removed by cache-cleaner on its next run.
It is recommended to run cache-cleaner as a periodic task on the Glare API
nodes to keep the incomplete blobs from occupying disk space.
Possible values:
    * Any non-negative integer
Related options:
    * None
""")),

    cfg.StrOpt('blob_cache_dir',
               help=_("""
Base directory for blob cache.
This is the location where blob data is cached and served out of. All cached
blobs are stored directly under this directory. This directory also contains
three subdirectories, namely, ``incomplete``, ``invalid`` and ``queue``.
The ``incomplete`` subdirectory is the staging area for downloading blobs. A
blob is first downloaded to this directory. When the blob download is
successful it is moved to the base directory. However, if the download fails,
the partially downloaded blob file is moved to the ``invalid`` subdirectory.
The ``queue``subdirectory is used for queuing blobs for download. This is
used primarily by the cache-prefetcher, which can be scheduled as a periodic
task like cache-pruner and cache-cleaner, to cache blobs ahead of their usage.
Upon receiving the request to cache a blob, Glare touches a file in the
``queue`` directory with the blob id as the file name. The cache-prefetcher,
when running, polls for the files in ``queue`` directory and starts
downloading them in the order they were created. When the download is
successful, the zero-sized file is deleted from the ``queue`` directory.
If the download fails, the zero-sized file remains and it'll be retried the
next time cache-prefetcher runs.
Possible values:
    * A valid path
Related options:
    * ``blob_cache_sqlite_db``
""")),
]

CONF = cfg.CONF
CONF.register_opts(blob_cache_opts)


class BlobCache(object):

    """Provides an LRU cache for blob data."""

    def __init__(self):
        self.init_driver()

    def init_driver(self):
        """
        Create the driver for the cache
        """
        driver_name = CONF.blob_cache_driver
        driver_module = (__name__ + '.drivers.' + driver_name + '.Driver')
        try:
            self.driver_class = importutils.import_class(driver_module)
            LOG.info(_LI("Blob cache loaded driver '%s'."), driver_name)
        except ImportError as import_err:
            LOG.warn(_LW("Blob cache driver "
                         "'%(driver_name)s' failed to load. "
                         "Got error: '%(import_err)s."),
                     {'driver_name': driver_name,
                      'import_err': import_err})

            driver_module = __name__ + '.drivers.sqlite.Driver'
            LOG.info(_LI("Defaulting to SQLite driver."))
            self.driver_class = importutils.import_class(driver_module)
        self.configure_driver()

    def configure_driver(self):
        """
        Configure the driver for the cache and, if it fails to configure,
        fall back to using the SQLite driver which has no odd dependencies
        """
        try:
            self.driver = self.driver_class()
            self.driver.configure()
        except exception.BadDriverConfiguration as config_err:
            driver_module = self.driver_class.__module__
            LOG.warn(_LW("Blob cache driver "
                         "'%(driver_module)s' failed to configure. "
                         "Got error: '%(config_err)s"),
                     {'driver_module': driver_module,
                      'config_err': config_err})
            LOG.info(_LI("Defaulting to SQLite driver."))
            default_module = __name__ + '.drivers.sqlite.Driver'
            self.driver_class = importutils.import_class(default_module)
            self.driver = self.driver_class()
            self.driver.configure()

    def is_cached(self, blob_id):
        """
        Returns True if the blob with the supplied ID has its blob
        file cached.

        :param blob_id: Blob ID
        """
        return self.driver.is_cached(blob_id)

    def is_queued(self, blob_id):
        """
        Returns True if the blob identifier is in our cache queue.

        :param blob_id: blob ID
        """
        return self.driver.is_queued(blob_id)

    def get_cache_size(self):
        """
        Returns the total size in bytes of the blob cache.
        """
        return self.driver.get_cache_size()

    def get_hit_count(self, blob_id):
        """
        Return the number of hits that a blob has

        :param blob_id: Opaque blob identifier
        """
        return self.driver.get_hit_count(blob_id)

    def get_cached_blobs(self):
        """
        Returns a list of records about cached blobs.
        """
        return self.driver.get_cached_blobs()

    def delete_all_cached_blobs(self):
        """
        Removes all cached blob files and any attributes about the blobs
        and returns the number of cached blob files that were deleted.
        """
        return self.driver.delete_all_cached_blobs()

    def delete_cached_blob(self, blob_id):
        """
        Removes a specific cached blob file and any attributes about the blob.

        :param blob_id: blob ID
        """
        self.driver.delete_cached_blob(blob_id)

    def delete_all_queued_blobs(self):
        """
        Removes all queued blob files and any attributes about the blobs
        and returns the number of queued blob files that were deleted.
        """
        return self.driver.delete_all_queued_blobs()

    def delete_queued_blob(self, blob_id):
        """
        Removes a specific queued blob file and any attributes about the blob

        :param blob_id: blob ID
        """
        self.driver.delete_queued_blob(blob_id)

    def prune(self):
        """
        Removes all cached blob files above the cache's maximum
        size. Returns a tuple containing the total number of cached
        files removed and the total size of all pruned blob files.
        """
        max_size = CONF.blob_cache_max_size
        current_size = self.driver.get_cache_size()
        if max_size > current_size:
            LOG.debug("blob cache has free space, skipping prune...")
            return (0, 0)

        overage = current_size - max_size
        LOG.debug("blob cache currently %(overage)d bytes over max "
                  "size. Starting prune to max size of %(max_size)d ",
                  {'overage': overage, 'max_size': max_size})

        total_bytes_pruned = 0
        total_files_pruned = 0
        entry = self.driver.get_least_recently_accessed()
        while entry and current_size > max_size:
            blob_id, size = entry
            LOG.debug("Pruning '%(blob_id)s' to free %(size)d bytes",
                      {'blob_id': blob_id, 'size': size})
            self.driver.delete_cached_blob(blob_id)
            total_bytes_pruned += size
            total_files_pruned += 1
            current_size = current_size - size
            entry = self.driver.get_least_recently_accessed()

        LOG.debug("Pruning finished pruning. "
                  "Pruned %(total_files_pruned)d and "
                  "%(total_bytes_pruned)d.",
                  {'total_files_pruned': total_files_pruned,
                   'total_bytes_pruned': total_bytes_pruned})
        return total_files_pruned, total_bytes_pruned

    def clean(self, stall_time=None):
        """
        Cleans up any invalid or incomplete cached blobs. The cache driver
        decides what that means...
        """
        self.driver.clean(stall_time)

    def queue_blob(self, blob_id):
        """
        This adds a blob to be cache to the queue.
        If the blob already exists in the queue or has already been
        cached, it returns False, True otherwise.

        :param blob_id: blob ID
        """
        return self.driver.queue_blob(blob_id)

    def get_caching_iter(self, blob_id, blob_checksum, blob_iter):
        """
        Returns an iterator that caches the contents of a blob
        while the blob contents are read through the supplied
        iterator.

        :param blob_id: blob ID
        :param blob_checksum: checksum expected to be generated while
                               iterating over blob data
        :param blob_iter: Iterator that will read blob contents
        """
        if not self.driver.is_cacheable(blob_id):
            return blob_iter

        LOG.debug("Tee'ing blob '%s' into cache", blob_id)

        return self.cache_tee_iter(blob_id, blob_iter, blob_checksum)

    def cache_tee_iter(self, blob_id, blob_iter, blob_checksum):
        try:
            current_checksum = hashlib.md5()

            with self.driver.open_for_write(blob_id) as cache_file:
                for chunk in blob_iter:
                    try:
                        cache_file.write(chunk)
                    finally:
                        current_checksum.update(chunk)
                        yield chunk
                cache_file.flush()

                if (blob_checksum and
                        blob_checksum != current_checksum.hexdigest()):
                    msg = _("Checksum verification failed. Aborted "
                            "caching of blob '%s'.") % blob_id
                    raise exception.GlareException(msg)

        except exception.GlareException as e:
            with excutils.save_and_reraise_exception():
                # blob_iter has given us bad, (size_checked_iter has found a
                # bad length), or corrupt data (checksum is wrong).
                LOG.exception(encodeutils.exception_to_unicode(e))
        except Exception as e:
            LOG.exception(_LE("Exception encountered while tee'ing "
                              "blob '%(blob_id)s' into cache: %(error)s. "
                              "Continuing with response.") %
                          {'blob_id': blob_id,
                           'error': encodeutils.exception_to_unicode(e)})

            # If no checksum provided continue responding even if
            # caching failed.
            for chunk in blob_iter:
                yield chunk

    def cache_blob_iter(self, blob_id, blob_iter, blob_checksum=None):
        """
        Cache a blob with supplied iterator.

        :param blob_id: blob ID
        :param blob_iter: Iterator retrieving blob chunks
        :param blob_checksum: Checksum of blob
        :returns: True if blob file was cached, False otherwise
        """
        if not self.driver.is_cacheable(blob_id):
            return False

        for chunk in self.get_caching_iter(blob_id, blob_checksum,
                                           blob_iter):
            pass
        return True

    def cache_blob_file(self, blob_id, blob_file):
        """
        Cache a blob file.

        :param blob_id: blob ID
        :param blob_file: blob file to cache
        :returns: True if blob file was cached, False otherwise
        """
        CHUNKSIZE = 64 * units.Mi

        return self.cache_blob_iter(blob_id,
                                    utils.chunkiter(blob_file, CHUNKSIZE))

    def open_for_read(self, blob_id):
        """
        Open and yield file for reading the blob file for a blob
        with supplied identifier.
        :note Upon successful reading of the blob file, the blob's
              hit count will be incremented.

        :param blob_id: blob ID
        """
        return self.driver.open_for_read(blob_id)

    def get_blob_size(self, blob_id):
        """
        Return the size of the blob file for a blob with supplied
        identifier.

        :param blob_id: blob ID
        """
        return self.driver.get_blob_size(blob_id)

    def get_queued_blobs(self):
        """
        Returns a list of blob IDs that are in the queue. The
        list should be sorted by the time the blob ID was inserted
        into the queue.
        """
        return self.driver.get_queued_blobs()

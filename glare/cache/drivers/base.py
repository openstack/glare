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
Base attribute driver class
"""

import os.path

from oslo_config import cfg
from oslo_log import log as logging

from glare.common import exception
from glare.common import utils
from glare.i18n import _

LOG = logging.getLogger(__name__)

CONF = cfg.CONF


class Driver(object):

    def configure(self):
        """
        Configure the driver to use the stored configuration options
        Any store that needs special configuration should implement
        this method. If the store was not able to successfully configure
        itself, it should raise `exception.BadDriverConfiguration`
        """
        # Here we set up the various file-based blob cache paths
        # that we need in order to find the files in different states
        # of cache management.
        self.set_paths()

    def set_paths(self):
        """
        Creates all necessary directories under the base cache directory
        """

        self.base_dir = CONF.blob_cache_dir
        if self.base_dir is None:
            msg = _('Failed to read %s from config') % 'blob_cache_dir'
            LOG.error(msg)
            driver = self.__class__.__module__
            raise exception.BadDriverConfiguration(driver_name=driver,
                                                   reason=msg)

        self.incomplete_dir = os.path.join(self.base_dir, 'incomplete')
        self.invalid_dir = os.path.join(self.base_dir, 'invalid')
        self.queue_dir = os.path.join(self.base_dir, 'queue')

        dirs = [self.incomplete_dir, self.invalid_dir, self.queue_dir]

        for path in dirs:
            utils.safe_mkdirs(path)

    def get_cache_size(self):
        """
        Returns the total size in bytes of the blob cache.
        """
        raise NotImplementedError

    def get_cached_blobs(self):
        """
        Returns a list of records about cached blobs.
        The list of records shall be ordered by blob ID and shall look like::
            [
                {
                'blob_id': <blob_ID>,
                'hits': INTEGER,
                'last_modified': ISO_TIMESTAMP,
                'last_accessed': ISO_TIMESTAMP,
                'size': INTEGER
                }, ...
            ]
        """
        return NotImplementedError

    def is_cached(self, blob_id):
        """
        Returns True if the blob with the supplied ID has its blob
        file cached.
        :param blob_id: blob ID
        """
        raise NotImplementedError

    def is_cacheable(self, blob_id):
        """
        Returns True if the blob with the supplied ID can have its
        blob file cached, False otherwise.
        :param blob_id: blob ID
        """
        raise NotImplementedError

    def is_queued(self, blob_id):
        """
        Returns True if the blob identifier is in our cache queue.
        :param blob_id: blob ID
        """
        raise NotImplementedError

    def delete_all_cached_blobs(self):
        """
        Removes all cached blob files and any attributes about the blobs
        and returns the number of cached blob files that were deleted.
        """
        raise NotImplementedError

    def delete_cached_blob(self, blob_id):
        """
        Removes a specific cached blob file and any attributes about the blob
        :param blob_id: blob ID
        """
        raise NotImplementedError

    def delete_all_queued_blobs(self):
        """
        Removes all queued blob files and any attributes about the blobs
        and returns the number of queued blob files that were deleted.
        """
        raise NotImplementedError

    def delete_queued_blob(self, blob_id):
        """
        Removes a specific queued blob file and any attributes about the blob
        :param blob_id: blob ID
        """
        raise NotImplementedError

    def queue_blob(self, blob_id):
        """
        Puts a blob identifier in a queue for caching. Return True
        on successful add to the queue, False otherwise...
        :param blob_id: blob ID
        """

    def clean(self, stall_time=None):
        """
        Dependent on the driver, clean up and destroy any invalid or incomplete
        cached blobs
        """
        raise NotImplementedError

    def get_least_recently_accessed(self):
        """
        Return a tuple containing the blob_id and size of the least recently
        accessed cached file, or None if no cached files.
        """
        raise NotImplementedError

    def open_for_write(self, blob_id):
        """
        Open a file for writing the blob file for a blob
        with supplied identifier.
        :param blob_id: blob ID
        """
        raise NotImplementedError

    def open_for_read(self, blob_id):
        """
        Open and yield file for reading the blob file for a blob
        with supplied identifier.
        :param blob_id: blob ID
        """
        raise NotImplementedError

    def get_blob_filepath(self, blob_id, cache_status='active'):
        """
        This crafts an absolute path to a specific entry
        :param blob_id: blob ID
        :param cache_status: Status of the blob in the cache
        """
        if cache_status == 'active':
            return os.path.join(self.base_dir, str(blob_id))
        return os.path.join(self.base_dir, cache_status, str(blob_id))

    def get_blob_size(self, blob_id):
        """
        Return the size of the blob file for a blob with supplied
        identifier.
        :param blob_id: blob ID
        """
        path = self.get_blob_filepath(blob_id)
        return os.path.getsize(path)

    def get_queued_blobs(self):
        """
        Returns a list of blob IDs that are in the queue. The
        list should be sorted by the time the blob ID was inserted
        into the queue.
        """
        raise NotImplementedError

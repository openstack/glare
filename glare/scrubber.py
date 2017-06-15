# Copyright 2010 OpenStack Foundation
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


import eventlet
from oslo_config import cfg
from oslo_log import log as logging

from glare.api.middleware import context
from glare.db.sqlalchemy import api as db_api
from glare.i18n import _

LOG = logging.getLogger(__name__)

scrubber_opts = [
    cfg.IntOpt('scrub_time', default=0, min=0,
               help=_("""
The amount of time, in seconds, to delay artifact scrubbing.
When delayed delete is turned on, an artifact blobs are put into
``pending_delete`` state upon deletion until the scrubber deletes its data.
Typically, soon
after the image is put into ``pending_delete`` state, it is available for
scrubbing. However, scrubbing can be delayed until a later point using this
configuration option. This option denotes the time period an image spends in
``pending_delete`` state before it is available for scrubbing.
It is important to realize that this has storage implications. The larger the
``scrub_time``, the longer the time to reclaim backend storage from deleted
images.
Possible values:
    * Any non-negative integer
Related options:
    * ``delayed_delete``
""")),
    cfg.IntOpt('scrub_pool_size', default=1, min=1,
               help=_("""
The size of thread pool to be used for scrubbing images.
When there are a large number of images to scrub, it is beneficial to scrub
images in parallel so that the scrub queue stays in control and the backend
storage is reclaimed in a timely fashion. This configuration option denotes
the maximum number of images to be scrubbed in parallel. The default value is
one, which signifies serial scrubbing. Any value above one indicates parallel
scrubbing.
Possible values:
    * Any non-zero positive integer
Related options:
    * ``delayed_delete``
""")),
]

scrubber_cmd_opts = [
    cfg.IntOpt('wakeup_time', default=300, min=0,
               help=_("""
Time interval, in seconds, between scrubber runs in daemon mode.
Scrubber can be run either as a cron job or daemon. When run as a daemon, this
configuration time specifies the time period between two runs. When the
scrubber wakes up, it fetches and scrubs all ``pending_delete`` images that
are available for scrubbing after taking ``scrub_time`` into consideration.
If the wakeup time is set to a large number, there may be a large number of
images to be scrubbed for each run. Also, this impacts how quickly the backend
storage is reclaimed.
Possible values:
    * Any non-negative integer
Related options:
    * ``daemon``
    * ``delayed_delete``
"""))
]

scrubber_cmd_cli_opts = [
    cfg.BoolOpt('daemon',
                short='D',
                default=False,
                help=_("""
Run scrubber as a daemon.
This boolean configuration option indicates whether scrubber should
run as a long-running process that wakes up at regular intervals to
scrub images. The wake up interval can be specified using the
configuration option ``wakeup_time``.
If this configuration option is set to ``False``, which is the
default value, scrubber runs once to scrub images and exits. In this
case, if the operator wishes to implement continuous scrubbing of
images, scrubber needs to be scheduled as a cron job.
Possible values:
    * True
    * False
Related options:
    * ``wakeup_time``
"""))
]

CONF = cfg.CONF
CONF.register_opts(scrubber_opts)


class Daemon(object):
    def __init__(self, wakeup_time=300, threads=100):
        LOG.info("Starting Daemon: wakeup_time=%(wakeup_time)s "
                 "threads=%(threads)s",
                 {'wakeup_time': wakeup_time, 'threads': threads})
        self.wakeup_time = wakeup_time
        self.event = eventlet.event.Event()
        # This pool is used for periodic instantiation of scrubber
        self.daemon_pool = eventlet.greenpool.GreenPool(threads)

    def start(self, application):
        self._run(application)

    def wait(self):
        try:
            self.event.wait()
        except KeyboardInterrupt:
            LOG.info("Daemon Shutdown on KeyboardInterrupt")

    def _run(self, application):
        LOG.debug("Running application")
        self.daemon_pool.spawn_n(application.run, self.event)
        eventlet.spawn_after(self.wakeup_time, self._run, application)
        LOG.debug("Next run scheduled in %s seconds", self.wakeup_time)


class Scrubber(object):
    def __init__(self):
        self.context = context.RequestContext()
        self.context.is_admin = True
        self.pool = eventlet.greenpool.GreenPool(CONF.scrub_pool_size)
        self.session = db_api.get_session()

    def run(self, event=None):
        while True:
            artifacts = [af for af in db_api._get_all(
                self.context,
                self.session,
                limit=CONF.scrub_pool_size,
                filters=[('status', None, 'neq', None, 'deleted')])]
            if not artifacts:
                break
            list(self.pool.starmap(self._scrub_artifact, artifacts))

    @staticmethod
    def _parse_blob_value(blob):
        return {
            "id": blob.id,
            "url": blob.url,
            "status": blob.status,
            "external": blob.external,
            "md5": blob.md5,
            "sha1": blob.sha1,
            "sha256": blob.sha256,
            "size": blob.size,
            "content_type": blob.content_type
        }

    def _scrub_artifact(self, af):
        # parse blobs
        blobs = {}
        for blob in af.blobs:
            blob_value = self._parse_blob_value(blob)
            if blob.key_name is not None:
                if blob.name not in blobs:
                    # create new dict
                    blobs[blob.name] = {}
                # insert value in the dict
                blobs[blob.name][blob.key_name] = blob_value
            else:
                # make scalar
                blobs[blob.name] = blob_value

        if blobs:
            # delete blobs one by one
            af._delete_blobs(blobs, context, af)
            LOG.info("Blobs successfully deleted for artifact %s", af.id)
        # delete artifact itself
        db_api.delete(context, af['id'])

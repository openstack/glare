.. _basic-configuration:

Basic Glare Configuration
=========================

Glare has a number of options that you can use to configure the Glare API
server and the various storage backends that Glare can use to store artifact
blobs.

Most configuration is done via configuration files. When starting up a Glare
server, you can specify the configuration file to use
(see :ref:`the documentation on controller Glare server <controlling-servers>`).
If you do **not** specify a configuration file, Glare will look in the following
directories for a configuration file, in order:

* ``~/.glare``
* ``~/``
* ``/etc/glare``
* ``/etc``

The Glare API server configuration file should be named ``glare.conf``.
If you installed Glare via your operating system's package management system, it
is likely that you will have sample configuration files installed in
``/etc/glare``.

In addition, sample configuration files for each server application with
detailed comments are available in the :ref:`Glare Sample Configuration
<sample-configuration>` section.

The PasteDeploy configuration (controlling the deployment of the WSGI
application for each component) may be found by default in
glare-paste.ini alongside the main configuration file, ``glare.conf``.
This pathname for the paste config is configurable, as follows::

  [paste_deploy]
  config_file = /path/to/paste/config


Common Configuration Options in Glare
-------------------------------------

Glare has a few command-line options:

``--verbose``
  Optional. Default: ``False``

  Can be specified on the command line and in configuration files.

  Turns on the INFO level in logging and prints more verbose command-line
  interface printouts.

``--debug``
  Optional. Default: ``False``

  Can be specified on the command line and in configuration files.

  Turns on the DEBUG level in logging.

``--config-file=PATH``
  Optional. Default: See below for default search order.

  Specified on the command line only.

  Takes a path to a configuration file to use when running the program. If this
  CLI option is not specified, then we check to see if the first argument is a
  file. If it is, then we try to use that as the configuration file. If there is
  no file or there were no arguments, we search for a configuration file in the
  following order:

  * ``~/.glare``
  * ``~/``
  * ``/etc/glare``
  * ``/etc``

``--config-dir=DIR``
  Optional. Default: ``None``

  Specified on the command line only.

  Takes a path to a configuration directory from which all \*.conf fragments
  are loaded. This provides an alternative to multiple --config-file options
  when it is inconvenient to explicitly enumerate all the configuration files,
  for example when an unknown number of config fragments are being generated
  by a deployment framework.

  If --config-dir is set, then --config-file is ignored.

  An example usage would be:

    $ glare-api --config-dir=/etc/glare/glare-api.d

    $ ls /etc/glare/glare-api.d
     00-core.conf
     01-swift.conf
     02-ssl.conf
     ... etc.

  The numeric prefixes in the example above are only necessary if a specific
  parse ordering is required (i.e. if an individual config option set in an
  earlier fragment is overridden in a later fragment).

  Note that ``glare-db-manage`` currently loads configuration from
  ``glare.conf``


Configuring Server Startup Options
----------------------------------

You can put the following options in the ``glare.conf`` file, under the
``[DEFAULT]`` section. They enable startup and binding behaviour Glare
server.

``bind_host=ADDRESS``
  The address of the host to bind to.

  Optional. Default: ``0.0.0.0``

``bind_port=PORT``
  The port the server should bind to.

  Optional. Default: ``9494``

``backlog=REQUESTS``
  Number of backlog requests to configure the socket with.

  Optional. Default: ``4096``

``tcp_keepidle=SECONDS``
  Sets the value of TCP_KEEPIDLE in seconds for each server socket.
  Not supported on OS X.

  Optional. Default: ``600``

``client_socket_timeout=SECONDS``
  Timeout for client connections' socket operations.  If an incoming
  connection is idle for this period it will be closed.  A value of `0`
  means wait forever.

  Optional. Default: ``900``

``workers=PROCESSES``
  Number of Glare API worker processes to start. Each worker
  process will listen on the same port. Increasing this value may increase
  performance (especially if using SSL with compression enabled). Typically
  it is recommended to have one worker process per CPU. The value `0`
  will prevent any new worker processes from being created.

  Optional. Default: The number of CPUs available will be used by default.

``max_request_id_length=LENGTH``
  Limits the maximum size of the x-openstack-request-id header which is
  logged. Affects only if context middleware is configured in pipeline.

  Optional. Default: ``64`` (Limited by max_header_line default: 16384)

Configuring SSL Support
~~~~~~~~~~~~~~~~~~~~~~~

``cert_file=PATH``
  Path to the certificate file the server should use when binding to an
  SSL-wrapped socket.

  Optional. Default: not enabled.

``key_file=PATH``
  Path to the private key file the server should use when binding to an
  SSL-wrapped socket.

  Optional. Default: not enabled.

``ca_file=PATH``
  Path to the CA certificate file the server should use to validate client
  certificates provided during an SSL handshake. This is ignored if
  ``cert_file`` and ''key_file`` are not set.

  Optional. Default: not enabled.

Configuring Logging in Glare
----------------------------

There are a number of configuration options in Glare that control how the
server log messages.

``--log-config=PATH``
  Optional. Default: ``None``

  Specified on the command line only.

  Takes a path to a configuration file to use for configuring logging.

Logging Options Available Only in Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will want to place the different logging options in the **[DEFAULT]** section
in your application configuration file. As an example, you might do the following
for the API server, in a configuration file called ``etc/glare.conf``::

  [DEFAULT]
  log_file = /var/log/glare/api.log

``log_file``
  The filepath of the file to use for logging messages from glare service. If
  missing, the default is to output messages to ``stdout``, so if you are running
  Glare server in a daemon mode you should make   sure that the ``log_file``
  option is set appropriately.

``log_dir``
  The filepath of the directory to use for log files. If not specified (the default)
  the ``log_file`` is used as an absolute filepath.

``log_date_format``
  The format string for timestamps in the log output.

  Defaults to ``%Y-%m-%d %H:%M:%S``. See the
  `logging module <http://docs.python.org/library/logging.html>`_ documentation for
  more information on setting this format string.

``log_use_syslog``
  Use syslog logging functionality.

  Defaults to False.

Configuring Enabled Artifact Types
----------------------------------

``enabled_artifact_types``
  Comma-separated list of enabled artifact types that will be available to user.

  Defaults to "heat_templates,heat_environments,murano_packages,tosca_templates,images"

``custom_artifact_types_modules``
  Comma-separated list of custom user python modules with artifact types that will be
  uploaded by Glare dynamically during service startup.
  Note that the module ``glare.objects`` is always enabled, and all artifact types
  placed there can be enabled without specification of this parameter.


Configuring Glare Storage Backends
----------------------------------

There are a number of configuration options in Glare that control how Glare
stores artifact blobs. These configuration options are specified in the
``glare.conf`` configuration file in the section ``[glance_store]``.

.. note::

   Due to technical limitations of glance_store library there is no way to
   define or enable database store globally. Operators have to set it for
   each artifact type in related config sections.

``default_store=STORE``
  Optional. Default: ``file``

  Can only be specified in configuration files.

  Sets the storage backend to use by default when storing artifact blobs in
  Glare.
  Available options for this option are (``file``, ``swift``, ``rbd``,
  ``sheepdog``, ``cinder`` or ``vsphere``). In order to select a default store
  it must also be listed in the ``stores`` list described below.

``stores=STORES``
  Optional. Default: ``file, http``

  A comma separated list of enabled glare stores. Some available options for
  this option are (``filesystem``, ``http``, ``rbd``, ``swift``,
  ``sheepdog``, ``cinder``, ``vmware``)

Configuring the Filesystem Storage Backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``filesystem_store_datadir=PATH``
  Optional. Default: ``/var/lib/glare/artifacts/``

  Can only be specified in configuration files.

  `This option is specific to the filesystem storage backend.`

  Sets the path where the filesystem storage backend writes blob data. Note that
  the filesystem storage backend will attempt to create this directory if it does
  not exist. Ensure that the user that ``glare-api`` runs under has write
  permissions to this directory.

``filesystem_store_file_perm=PERM_MODE``
  Optional. Default: ``0``

  Can only be specified in configuration files.

  `This option is specific to the filesystem storage backend.`

  The required permission value, in octal representation, for the created blob file.
  You can use this value to specify the user of the consuming service as
  the only member of the group that owns the created files. To keep the default value,
  assign a permission value that is less than or equal to 0.  Note that the file owner
  must maintain read permission; if this value removes that permission an error message
  will be logged and the BadStoreConfiguration exception will be raised.  If the Glare
  service has insufficient privileges to change file access permissions, a file will still
  be saved, but a warning message will appear in the Glare log.

Configuring the Filesystem Storage Backend with multiple stores
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``filesystem_store_datadirs=PATH:PRIORITY``
  Optional. Default: ``/var/lib/glare/artifacts/:1``

  Example::

    filesystem_store_datadirs = /var/glare/store
    filesystem_store_datadirs = /var/glare/store1:100
    filesystem_store_datadirs = /var/glare/store2:200

  This option can only be specified in configuration file and is specific
  to the filesystem storage backend only.

  filesystem_store_datadirs option allows administrators to configure
  multiple store directories to save glare artifact blobs in filesystem storage
  backend. Each directory can be coupled with its priority.

.. note::

  * This option can be specified multiple times to specify multiple stores.
  * Either filesystem_store_datadir or filesystem_store_datadirs option must be
    specified in glare.conf
  * Store with priority 200 has precedence over store with priority 100.
  * If no priority is specified, default priority '0' is associated with it.
  * If two filesystem stores have same priority store with maximum free space
    will be chosen to store the artifact blob.
  * If same store is specified multiple times then BadStoreConfiguration
    exception will be raised.

Configuring the Swift Storage Backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``swift_store_auth_address=URL``
  Required when using the Swift storage backend.

  Can only be specified in configuration files.

  Deprecated. Use ``auth_address`` in the Swift back-end configuration file instead.

  `This option is specific to the Swift storage backend.`

  Sets the authentication URL supplied to Swift when making calls to its storage
  system. For more information about the Swift authentication system, please
  see the `Swift auth <https://docs.openstack.org/swift/latest/overview_auth.html>`_
  documentation.

.. note::

  Swift authentication addresses use HTTPS by default. This
  means that if you are running Swift with authentication over HTTP, you need
  to set your ``swift_store_auth_address`` to the full URL, including the ``http://``.

``swift_store_user=USER``
  Required when using the Swift storage backend.

  Can only be specified in configuration files.

  Deprecated. Use ``user`` in the Swift back-end configuration file instead.

  `This option is specific to the Swift storage backend.`

  Sets the user to authenticate against the ``swift_store_auth_address`` with.

``swift_store_key=KEY``
  Required when using the Swift storage backend.

  Can only be specified in configuration files.

  Deprecated. Use ``key`` in the Swift back-end configuration file instead.

  `This option is specific to the Swift storage backend.`

  Sets the authentication key to authenticate against the
  ``swift_store_auth_address`` with for the user ``swift_store_user``.

``swift_store_container=CONTAINER``
  Optional. Default: ``glare``

  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  Sets the name of the container to use for Glare artifact blobs in Swift.

``swift_store_create_container_on_put``
  Optional. Default: ``False``

  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  If true, Glare will attempt to create the container ``swift_store_container``
  if it does not exist.

``swift_store_large_object_size=SIZE_IN_MB``
  Optional. Default: ``5120``

  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  What size, in MB, should Glare start chunking artifact blob files
  and do a large object manifest in Swift? By default, this is
  the maximum object size in Swift, which is 5GB

``swift_store_large_object_chunk_size=SIZE_IN_MB``
  Optional. Default: ``200``

  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  When doing a large object manifest, what size, in MB, should
  Glare write chunks to Swift?  The default is 200MB.

``swift_store_multi_tenant=False``
  Optional. Default: ``False``

  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  If set to True enables multi-tenant storage mode which causes Glare artifact
  blobs to be stored in tenant specific Swift accounts. When set to False Glare
  stores all blobs in a single Swift account.

``swift_store_multiple_containers_seed``
  Optional. Default: ``0``

  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  When set to 0, a single-tenant store will only use one container to store all
  blobs. When set to an integer value between 1 and 32, a single-tenant store
  will use multiple containers to store blobs, and this value will determine
  how many characters from a blob UUID are checked when determining what
  container to place the blob in. The maximum number of containers that will be
  created is approximately equal to 16^N. This setting is used only when
  swift_store_multi_tenant is disabled.

  Example: if this config option is set to 3 and
  swift_store_container = 'glare', then a blob with UUID
  'fdae39a1-bac5-4238-aba4-69bcc726e848' would be placed in the container
  'glare_fda'. All dashes in the UUID are included when creating the container
  name but do not count toward the character limit, so in this example with N=10
  the container name would be 'glare_fdae39a1-ba'.

  When choosing the value for swift_store_multiple_containers_seed, deployers
  should discuss a suitable value with their swift operations team. The authors
  of this option recommend that large scale deployments use a value of '2',
  which will create a maximum of ~256 containers. Choosing a higher number than
  this, even in extremely large scale deployments, may not have any positive
  impact on performance and could lead to a large number of empty, unused
  containers. The largest of deployments could notice an increase in performance
  if swift rate limits are throttling on single container.

.. note::

  If dynamic container creation is turned off, any value for this configuration
  option higher than '1' may be unreasonable as the deployer would have to
  manually create each container.

``swift_store_admin_tenants``
  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  Optional. Default: Not set.

  A list of swift ACL strings that will be applied as both read and
  write ACLs to the containers created by Glare in multi-tenant
  mode. This grants the specified tenants/users read and write access
  to all newly created blob objects. The standard swift ACL string
  formats are allowed, including:

  <tenant_id>:<username>
  <tenant_name>:<username>
  \*:<username>

  Multiple ACLs can be combined using a comma separated list, for
  example: swift_store_admin_tenants = service:glare,*:admin

``swift_store_auth_version``
  Can only be specified in configuration files.

  Deprecated. Use ``auth_version`` in the Swift back-end configuration
  file instead.

  `This option is specific to the Swift storage backend.`

  Optional. Default: ``2``

  A string indicating which version of Swift OpenStack authentication
  to use. See the project
  `python-swiftclient <https://docs.openstack.org/python-swiftclient/latest/>`_
  for more details.

``swift_store_service_type``
  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  Optional. Default: ``object-store``

  A string giving the service type of the swift service to use. This
  setting is only used if swift_store_auth_version is ``2``.

``swift_store_region``
  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  Optional. Default: Not set.

  A string giving the region of the swift service endpoint to use. This
  setting is only used if swift_store_auth_version is ``2``. This
  setting is especially useful for disambiguation if multiple swift
  services might appear in a service catalog during authentication.

``swift_store_endpoint_type``
  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  Optional. Default: ``publicURL``

  A string giving the endpoint type of the swift service endpoint to
  use. This setting is only used if swift_store_auth_version is ``2``.

``swift_store_ssl_compression``
  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  Optional. Default: True.

  If set to False, disables SSL layer compression of https swift
  requests. Setting to 'False' may improve performance for artifact blobs
  which are already in a compressed format, e.g. qcow2. If set to True
  then compression will be enabled (provided it is supported by the swift
  proxy).

``swift_store_cacert``
  Can only be specified in configuration files.

  Optional. Default: ``None``

  A string giving the path to a CA certificate bundle that will allow Glare
  service to perform SSL verification when communicating with Swift.

``swift_store_retry_get_count``
  The number of times a Swift download will be retried before the request
  fails.
  Optional. Default: ``0``

Configuring Multiple Swift Accounts/Stores
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to not store Swift account credentials in the database, and to
have support for multiple accounts (or multiple Swift backing stores), a
reference is stored in the database and the corresponding configuration
(credentials/ parameters) details are stored in the configuration file.
Optional.  Default: not enabled.

The location for this file is specified using the ``swift_store_config_file``
configuration file in the section ``[DEFAULT]``. **If an incorrect value is
specified, Glare API Swift store service will not be configured.**

``swift_store_config_file=PATH``
  `This option is specific to the Swift storage backend.`

``default_swift_reference=DEFAULT_REFERENCE``
  Required when multiple Swift accounts/backing stores are configured.

  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  It is the default swift reference that is used to add any new artifact
  blobs.

``swift_store_auth_insecure``
  If True, bypass SSL certificate verification for Swift.

  Can only be specified in configuration files.

  `This option is specific to the Swift storage backend.`

  Optional. Default: ``False``

Configuring Swift configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If ``swift_store_config_file`` is set, Glare will use information
from the file specified under this parameter.

.. note::

   The ``swift_store_config_file`` is currently used only for single-tenant
   Swift store configurations. If you configure a multi-tenant Swift store
   back end (``swift_store_multi_tenant=True``), ensure that both
   ``swift_store_config_file`` and ``default_swift_reference`` are *not* set.

The file contains a set of references like:

.. code-block:: ini

    [ref1]
    user = tenant:user1
    key = key1
    auth_version = 2
    auth_address = http://localhost:5000/v2.0

    [ref2]
    user = project_name:user_name2
    key = key2
    user_domain_id = default
    project_domain_id = default
    auth_version = 3
    auth_address = http://localhost:5000/v3

A default reference must be configured. Its parameters will be used when
creating new artifact blobs. For example, to specify ``ref2`` as the default
reference, add the following value to the [glance_store] section of
:file:`glare.conf` file:

.. code-block:: ini

    default_swift_reference = ref2

In the reference, a user can specify the following parameters:

``user``
  A *project_name user_name* pair in the ``project_name:user_name`` format
  to authenticate against the Swift authentication service.

``key``
  An authentication key for a user authenticating against the Swift
  authentication service.

``auth_address``
  An address where the Swift authentication service is located.

``auth_version``
  A version of the authentication service to use.
  Valid versions are ``2`` and ``3`` for Keystone and ``1``
  (deprecated) for Swauth and Rackspace.

  Optional. Default: ``2``

``project_domain_id``
  A domain ID of the project which is the requested project-level
  authorization scope.

  Optional. Default: ``None``

  `This option can be specified if ``auth_version`` is ``3`` .`

``project_domain_name``
  A domain name of the project which is the requested project-level
  authorization scope.

  Optional. Default: ``None``

  `This option can be specified if ``auth_version`` is ``3`` .`

``user_domain_id``
  A domain ID of the user which is the requested domain-level
  authorization scope.

  Optional. Default: ``None``

  `This option can be specified if ``auth_version`` is ``3`` .`

``user_domain_name``
  A domain name of the user which is the requested domain-level
  authorization scope.

  Optional. Default: ``None``

  `This option can be specified if ``auth_version`` is ``3``. `

Configuring the RBD Storage Backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

  The RBD storage backend requires the python bindings for
  librados and librbd. These are in the python-ceph package on
  Debian-based distributions.

``rbd_store_pool=POOL``
  Optional. Default: ``rbd``

  Can only be specified in configuration files.

  `This option is specific to the RBD storage backend.`

  Sets the RADOS pool in which artifact blobs are stored.

``rbd_store_chunk_size=CHUNK_SIZE_MB``
  Optional. Default: ``4``

  Can only be specified in configuration files.

  `This option is specific to the RBD storage backend.`

  Artifact blobs will be chunked into objects of this size (in megabytes).
  For best performance, this should be a power of two.

``rados_connect_timeout``
  Optional. Default: ``0``

  Can only be specified in configuration files.

  `This option is specific to the RBD storage backend.`

  Prevents glare service hangups during the connection to RBD. Sets the time
  to wait (in seconds) for glare before closing the connection.
  Setting ``rados_connect_timeout<=0`` means no timeout.

``rbd_store_ceph_conf=PATH``
  Optional. Default: ``/etc/ceph/ceph.conf``, ``~/.ceph/config``, and
  ``./ceph.conf``

  Can only be specified in configuration files.

  `This option is specific to the RBD storage backend.`

  Sets the Ceph configuration file to use.

``rbd_store_user=NAME``
  Optional. Default: ``admin``

  Can only be specified in configuration files.

  `This option is specific to the RBD storage backend.`

  Sets the RADOS user to authenticate as. This is only needed
  when `RADOS authentication <http://ceph.newdream.net/wiki/Cephx>`_
  is `enabled. <http://ceph.newdream.net/wiki/Cluster_configuration#Cephx_auth>`_

A keyring must be set for this user in the Ceph
configuration file, e.g. with a user ``glare``::

  [client.glare]
  keyring=/etc/glare/rbd.keyring

To set up a user named ``glare`` with minimal permissions, using a pool called
``artifacts``, run::

  rados mkpool artifacts
  ceph-authtool --create-keyring /etc/glare/rbd.keyring
  ceph-authtool --gen-key --name client.glare --cap mon 'allow r' --cap osd 'allow rwx pool=artifacts' /etc/glare/rbd.keyring
  ceph auth add client.glare -i /etc/glare/rbd.keyring

Configuring the Sheepdog Storage Backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``sheepdog_store_address=ADDR``
  Optional. Default: ``localhost``

  Can only be specified in configuration files.

  `This option is specific to the Sheepdog storage backend.`

  Sets the IP address of the sheep daemon

``sheepdog_store_port=PORT``
  Optional. Default: ``7000``

  Can only be specified in configuration files.

  `This option is specific to the Sheepdog storage backend.`

  Sets the IP port of the sheep daemon

``sheepdog_store_chunk_size=SIZE_IN_MB``
  Optional. Default: ``64``

  Can only be specified in configuration files.

  `This option is specific to the Sheepdog storage backend.`

  Artifact blobs will be chunked into objects of this size (in megabytes).
  For best performance, this should be a power of two.

Configuring the Cinder Storage Backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

  Currently Cinder store is experimental. Current deployers should be
  aware that the use of it in production right now may be risky. It is expected
  to work well with most iSCSI Cinder backends such as LVM iSCSI, but will not
  work with some backends especially if they don't support host-attach.

.. note::

  To create a Cinder volume from a blob in this store quickly, additional
  settings are required. Please see the
  `Volume-backed artifact <http://docs.openstack.org/admin-guide/blockstorage_volume_backed_image.html>`_
  documentation for more information.

``cinder_catalog_info=<service_type>:<service_name>:<endpoint_type>``
  Optional. Default: ``volumev2::publicURL``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  Sets the info to match when looking for cinder in the service catalog.
  Format is : separated values of the form: <service_type>:<service_name>:<endpoint_type>

``cinder_endpoint_template=http://ADDR:PORT/VERSION/%(tenant)s``
  Optional. Default: ``None``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  Override service catalog lookup with template for cinder endpoint.
  ``%(...)s`` parts are replaced by the value in the request context.
  e.g. http://localhost:8776/v2/%(tenant)s

``os_region_name=REGION_NAME``
  Optional. Default: ``None``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  Region name of this node.

  Deprecated. Use ``cinder_os_region_name`` instead.

``cinder_os_region_name=REGION_NAME``
  Optional. Default: ``None``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  Region name of this node.  If specified, it is used to locate cinder from
  the service catalog.

``cinder_ca_certificates_file=CA_FILE_PATH``
  Optional. Default: ``None``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  Location of ca certificates file to use for cinder client requests.

``cinder_http_retries=TIMES``
  Optional. Default: ``3``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  Number of cinderclient retries on failed http calls.

``cinder_state_transition_timeout``
  Optional. Default: ``300``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  Time period, in seconds, to wait for a cinder volume transition to complete.

``cinder_api_insecure=ON_OFF``
  Optional. Default: ``False``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  Allow to perform insecure SSL requests to cinder.

``cinder_store_user_name=NAME``
  Optional. Default: ``None``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  User name to authenticate against Cinder. If <None>, the user of current
  context is used.

.. note::

  This option is applied only if all of ``cinder_store_user_name``,
  ``cinder_store_password``, ``cinder_store_project_name`` and
  ``cinder_store_auth_address`` are set.
  These options are useful to put blob volumes into the internal service
  project in order to hide the volume from users, and to make the blob
  sharable among projects.

``cinder_store_password=PASSWORD``
  Optional. Default: ``None``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  Password for the user authenticating against Cinder. If <None>, the current
  context auth token is used.

``cinder_store_project_name=NAME``
  Optional. Default: ``None``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  Project name where the blob is stored in Cinder. If <None>, the project
  in current context is used.

``cinder_store_auth_address=URL``
  Optional. Default: ``None``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  The address where the Cinder authentication service is listening. If <None>,
  the cinder endpoint in the service catalog is used.

``rootwrap_config=NAME``
  Optional. Default: ``/etc/glare/rootwrap.conf``

  Can only be specified in configuration files.

  `This option is specific to the Cinder storage backend.`

  Path to the rootwrap configuration file to use for running commands as root.

Configuring the VMware Storage Backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``vmware_server_host=ADDRESS``
  Required when using the VMware storage backend.

  Can only be specified in configuration files.

  Sets the address of the ESX/ESXi or vCenter Server target system.
  The address can contain an IP (``127.0.0.1``), an IP and port
  (``127.0.0.1:443``), a DNS name (``www.my-domain.com``) or DNS and port.

  `This option is specific to the VMware storage backend.`

``vmware_server_username=USERNAME``
  Required when using the VMware storage backend.

  Can only be specified in configuration files.

  Username for authenticating with VMware ESX/ESXi or vCenter Server.

``vmware_server_password=PASSWORD``
  Required when using the VMware storage backend.

  Can only be specified in configuration files.

  Password for authenticating with VMware ESX/ESXi or vCenter Server.

``vmware_datastores``
  Required when using the VMware storage backend.

  This option can only be specified in configuration file and is specific
  to the VMware storage backend.

  vmware_datastores allows administrators to configure multiple datastores to
  save glare artifact blob in the VMware store backend. The required format for the
  option is: <datacenter_path>:<datastore_name>:<optional_weight>.

  where datacenter_path is the inventory path to the datacenter where the
  datastore is located. An optional weight can be given to specify the priority.

  Example::

    vmware_datastores = datacenter1:datastore1
    vmware_datastores = dc_folder/datacenter2:datastore2:100
    vmware_datastores = datacenter1:datastore3:200

.. note::

    - This option can be specified multiple times to specify multiple datastores.
    - Either vmware_datastore_name or vmware_datastores option must be specified
      in glare.conf
    - Datastore with weight 200 has precedence over datastore with weight 100.
    - If no weight is specified, default weight '0' is associated with it.
    - If two datastores have same weight, the datastore with maximum free space
      will be chosen to store the artifact blob.
    - If the datacenter path or datastore name contains a colon (:) symbol, it
      must be escaped with a backslash.

``vmware_api_retry_count=TIMES``
  Optional. Default: ``10``

  Can only be specified in configuration files.

  The number of times VMware ESX/VC server API must be
  retried upon connection related issues.

``vmware_task_poll_interval=SECONDS``
  Optional. Default: ``5``

  Can only be specified in configuration files.

  The interval used for polling remote tasks invoked on VMware ESX/VC server.

``vmware_store_image_dir``
  Optional. Default: ``/openstack_glare``

  Can only be specified in configuration files.

  The path to access the folder where the artifact blobs will be stored in the
  datastore.

``vmware_api_insecure=ON_OFF``
  Optional. Default: ``False``

  Can only be specified in configuration files.

  Allow to perform insecure SSL requests to ESX/VC server.

Configuring the Storage Endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``swift_store_endpoint=URL``
  Optional. Default: ``None``

  Can only be specified in configuration files.

  Overrides the storage URL returned by auth. The URL should include the
  path up to and excluding the container. The location of an object is
  obtained by appending the container and object to the configured URL.
  e.g. ``https://www.my-domain.com/v1/path_up_to_container``


Configuring Notifications
-------------------------

Glare can optionally generate notifications to be logged or sent to a message
queue. The configuration options are specified in the ``glare.conf``
configuration file.

``[oslo_messaging_notifications]/driver``

  Optional. Default: ``noop``

  Sets the notification driver used by oslo.messaging. Options include
  ``messaging``, ``messagingv2``, ``log`` and ``routing``.

  For more information see :ref:`Glare notifications <notifications>` and
  `oslo.messaging <https://docs.openstack.org/oslo.messaging/latest/>`_.

``[DEFAULT]/disabled_notifications``

  Optional. Default: ``[]``

  List of disabled notifications. A notification can be given either as a
  notification type to disable a single event, or as a notification group prefix
  to disable all events within a group.

  Example: if this config option is set to ["artifact.create", "artifact.activate"],
  then "artifact.create" notification will not be sent after artifact is created and
  none of the notifications for artifact activation will be sent.


Configuring Glare performance profiling
---------------------------------------

Glare supports using osprofiler to trace the performance of each key internal
handling, including RESTful API calling, DB operation and etc.

``Please be aware that Glare performance profiling is currently a work in
progress feature.`` Although, some trace points is available, e.g. API
execution profiling at wsgi main entry and SQL execution profiling at DB
module, the more fine-grained trace point is being worked on.

The config value ``enabled`` is used to determine whether fully enable
profiling feature for glare service.

``enabled=<True|False>``

  Optional. Default: ``False``

  There is one more configuration option that needs to be defined to enable
  Glare service profiling. The config value ``hmac_keys`` is used for
  encrypting context data for performance profiling.

``hmac_keys=<secret_key_string>``

  Optional. Default: ``SECRET_KEY``

.. note::

  In order to make profiling work as designed operator needs
  to make those values of HMAC key be consistent for all services in their
  deployment. Without HMAC key the profiling will not be triggered even profiling
  feature is enabled.

  The config value ``trace_sqlalchemy`` is used to determine whether fully enable
  sqlalchemy engine based SQL execution profiling feature for glare service.

``trace_sqlalchemy=<True|False>``

  Optional. Default: ``False``

Configuring Glare public endpoint
---------------------------------

This setting allows an operator to configure the endpoint URL that will
appear in the Glare "versions" response (that is, the response to
``GET /``\  ).  This can be necessary when the Glare API service is run
behind a proxy because the default endpoint displayed in the versions
response is that of the host actually running the API service.  If
Glare is being run behind a load balancer, for example, direct access
to individual hosts running the Glare API may not be allowed, hence the
load balancer URL would be used for this value.

``public_endpoint=<None|URL>``

  Optional. Default: ``None``

Configuring http_keepalive option
---------------------------------

``http_keepalive=<True|False>``

  If False, server will return the header "Connection: close", If True, server
  will return "Connection: Keep-Alive" in its responses. In order to close the
  client socket connection explicitly after the response is sent and read
  successfully by the client, you simply have to set this option to False when
  you create a wsgi server.

Configuring the Health Check
----------------------------

This setting allows an operator to configure the endpoint URL that will
provide information to load balancer if given API endpoint at the node should
be available or not.

To enable the health check middleware, it must occur in the beginning of the
application pipeline.

The health check middleware should be placed in your
``glare-paste.ini`` in a section
titled ``[filter:healthcheck]``. It should look like this::

  [filter:healthcheck]
  paste.filter_factory = oslo_middleware:Healthcheck.factory
  backends = disable_by_file
  disable_by_file_path = /etc/glare/healthcheck_disable

A ready-made application pipeline including this filter is defined e.g. in
the ``glare-paste.ini`` file, looking like so::

  [pipeline:glare-api]
  pipeline = healthcheck versionnegotiation osprofiler unauthenticated-context rootapp

For more information see
`oslo.middleware <https://docs.openstack.org/oslo.middleware/latest/reference/api.html#oslo_middleware.Healthcheck>`_.

Configuration per Artifact Type
-------------------------------

Each artifact type may contain its own config parameters that are located in
special section [artifact_type:<type_name>]. For example, for ``images``
artifact type the section is called [artifact_type:images].

Some of the parameters are common across all artifact types and they redefine
global parameters that are set for all types.

``default_store``
  Optional. Default: ``None``

  The default scheme to use for storing artifacts of the type. Provide a
  string value representing the default scheme to use for storing artifact data.
  If not set, Glare uses default_store parameter from [glance_store] section.

``delayed_delete``
  Optional. Default: ``None``

  If False defines that artifacts must be deleted immediately after
  the user call. Otherwise they just will be marked as deleted so they
  can be scrubbed by some other tool in the background. Redefines
  global parameter of the same name from [DEFAULT] section.

``max_uploaded_data``
  Optional. Default: ``None``

  Defines how many bytes of data of the type user can upload to
  storage. Value -1 means no limit. Redefines global parameter of the
  same name from [DEFAULT] section.
  Minimum value: -1

``max_artifact_number``
  Optional. Default: ``None``

  Defines how many artifacts of this type user can have. Value -1
  means no limit. Redefines global parameter of the same name from
  [DEFAULT] section.
  Minimum value: -1

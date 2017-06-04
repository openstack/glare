Quick Start
===========

For running Glare with Devstack:

    1.Edit /home/stack/devstack/local.conf
      Add the following lines:

        enable_plugin glare https://github.com/openstack/glare
        LIBS_FROM_GIT+=python-glareclient # To install glare client

    2.  Go to /home/stack/devstack
        and run: ./unstack.sh
    3.  Run      ./stack.sh


=========================
Glare client Installation
=========================

If you didn't add LIBS_FROM_GIT+=python-glareclient to /home/stack/devstack/local.conf ,
you can install glare-client in a different way:

Clone the repo to /opt/stack/ and then go to the directory:

$ cd /opt/stack
$ git clone git://git.openstack.org/openstack/python-glareclient.git $ cd python-glareclient

Then run:

$ pip install -e .

another option:

$ pip install -r requirements.txt $ python setup.py install

================
Run Glare client
================

If Glare authentication is enabled, provide the information about OpenStack auth to environment variables.
Type:
$ export OS_AUTH_URL=http://<Keystone_host>:5000/v2.0 $ export OS_USERNAME=admin $ export
OS_TENANT_NAME=tenant $ export OS_PASSWORD=secret $ export OS_GLARE_URL=http://<Glare host>:9494/v2
(optional, by default URL=http://localhost:9494/v2)
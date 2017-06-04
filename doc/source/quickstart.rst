Quick Start
===========

For running Glare with Devstack:

    1.Edit /home/stack/devstack/local.conf -
      Add the following lines:

        enable_plugin glare https://github.com/openstack/glare.git
        LIBS_FROM_GIT+=python-glareclient

    2.  Go to /home/stack/devstack
        and run: ./unstack.sh
    3.  Run      ./stack.sh

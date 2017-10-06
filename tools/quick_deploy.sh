#!/usr/bin/env bash

# This small script allows to quickly deploy Glare on Ubuntu for
# testing purposes. For production things use more advanced solutions.

# Usage: ./quick_deploy.sh

# When the script is finished:
# $ glare-api &> glare.log &
# $ source openrc
# $ glare type-list

# Prepare environment
export LC_ALL=C
sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get -y install git
sudo apt-get -y install python
sudo apt-get -y install python-setuptools
sudo apt-get -y install python-pip
cd ~

# Clone latest glare and glare client
git clone https://github.com/openstack/glare.git
git clone https://github.com/openstack/python-glareclient.git

# Create openrc file for admin
sudo cat <<EOF > openrc
export OS_GLARE_URL="http://127.0.0.1:9494"
export AUTH_TOKEN="admin:admin:admin"
EOF

# Install Glare
cd glare
git pull
sudo pip install -r requirements.txt
sudo python setup.py install
sudo mkdir /etc/glare
sudo cp etc/glare-paste.ini /etc/glare

# Create config file
sudo tee -a /etc/glare/glare.conf <<EOF
[glance_store]
default_store = file
filesystem_store_datadir = /tmp/blobs
[database]
connection = sqlite:////tmp/tmp.sqlite
[paste_deploy]
flavor =
[oslo_policy]
policy_file = policy.json
EOF
sudo tee -a /etc/glare/policy.json <<EOF
{}
EOF

# Migrate database
glare-db-manage upgrade

# Install glare client
cd ../python-glareclient
git pull
sudo pip install -r requirements.txt
sudo python setup.py install

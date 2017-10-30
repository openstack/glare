Glare Configuration Guide
=========================

The following parameters can be configured in glare.conf:

Listing parameters
------------------

* *default_api_limit* - Default value for the number of items returned
by a request if not specified explicitly in the request.
Default value: 25

* *max_api_limit* - Maximum permissible number of items that could be returned by a request.
Default value: 1000


Quota parameters
----------------

* *max_uploaded_data* - Defines how many bytes of data user can upload to storage.
This parameter is global and doesn't take into account data of what type was uploaded.
Value -1 means no limit.
Default value: -1

* *max_artifact_number* - Defines how many artifacts user can have. This
parameter is global and doesn't take into account artifacts of what type were created.
Value -1 means no limit.
Default value: -1
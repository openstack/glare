# Copyright 2017 - Nokia Networks
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from oslo_utils import encodeutils
from routes.route import Route
import six.moves.urllib.parse as urlparse

from glare.api.v1 import resource
from glare.common import wsgi


"""API that allows to list all artifacts regardless of their type."""


class RequestDeserializer(resource.RequestDeserializer):

    def list(self, req):
        res = super(RequestDeserializer, self).list(req)
        res['type_name'] = 'all'
        return res

    def get(self, req):
        res = super(RequestDeserializer, self).get(req)
        res['type_name'] = 'all'
        return res

    def download(self, req):
        res = super(RequestDeserializer, self).download(req)
        res['type_name'] = 'all'
        return res


class ResponseSerializer(resource.ResponseSerializer):

    def list(self, response, af_list):
        params = dict(response.request.params)
        params.pop('marker', None)

        encode_params = {}
        for key, value in params.items():
            encode_params[key] = encodeutils.safe_encode(value)
        query = urlparse.urlencode(encode_params)

        body = {
            'first': '/all_artifacts'
        }
        if query:
            body['first'] = '%s?%s' % (body['first'], query)
        if 'next_marker' in af_list:
            params['marker'] = af_list['next_marker']
            next_query = urlparse.urlencode(params)
            body['next'] = '/all_artifacts/?%s' % next_query
        body['artifacts'] = af_list['artifacts']

        self._prepare_json_response(response, body)


def create_resource():
    """Artifact resource factory method."""
    deserializer = RequestDeserializer()
    serializer = ResponseSerializer()
    controller = resource.ArtifactsController()
    return wsgi.Resource(
        controller=controller,
        deserializer=deserializer,
        serializer=serializer
    )

all_artifacts_resource = create_resource()
reject_method_resource = wsgi.Resource(wsgi.RejectMethodController())

mapper = [
    # ---artifacts---
    Route(name=None,
          routepath='/all_artifacts',
          controller=all_artifacts_resource,
          action='list',
          conditions={'method': ['GET']},
          body_reject=True),
    Route(name=None,
          routepath='/all_artifacts',
          controller=reject_method_resource,
          action='reject',
          allowed_methods='GET'),

    Route(name=None,
          routepath='/all_artifacts/{artifact_id}',
          controller=all_artifacts_resource,
          action='show',
          conditions={'method': ['GET']},
          body_reject=True),
    Route(name=None,
          routepath='/all_artifacts/{artifact_id}',
          controller=reject_method_resource,
          action='reject',
          allowed_methods='GET'),

    # ---blobs---
    Route(name=None,
          routepath='/all_artifacts/{artifact_id}/{blob_path:.*?}',
          controller=all_artifacts_resource,
          action='download_blob',
          conditions={'method': ['GET']},
          body_reject=True),
    Route(name=None,
          routepath='/all_artifacts/{artifact_id}/{blob_path:.*?}',
          controller=reject_method_resource,
          action='reject',
          allowed_methods='GET')
]

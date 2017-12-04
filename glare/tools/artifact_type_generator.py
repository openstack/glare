import logging
import os
from __builtin__ import classmethod
from optparse import OptionParser

from osc_lib.command import command

usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)

parser.add_option("-n", "--name", dest="artifact_name", type="string", action="store")
# parser.add_option()

LOG = logging.getLogger(__name__)


class Generator(command.Lister):
    """
    generates artifact
    """
    template_file_name = "artifact_type_template.txt"

    def take_action(self, parsed_args):
        response = {}
        try:
            LOG.debug('take_action({0})'.format(parsed_args))
            params = {'artifact_name': parsed_args.name,
                      "destination_dir": (parsed_args.dest + "/" + parsed_args.name + ".py")}
            self.generate_artifact(params)
            response['Status'] = "Successfully Generated Artifact File"
            response["Path"] = parsed_args.dest
        except Exception as exception:
            logging.error("Error during creating artifact template,cause: %s ", exception)
            response["Status"] = "Failed to generated Artifact Type file"
            response["Message"] = exception
        return (response.keys(), [response.values()])

    def get_parser(self, prog_name):
        parser = super(Generator, self).get_parser(prog_name)
        parser.add_argument(
            '--name', '-n',
            metavar='<ARTIFACT_NAME>',
            help='Name of the artifact you want to create',
        )
        parser.add_argument(
            '--dest', '-d',
            metavar='<DESTINATION>',
            help='Direcotry where you want to save generated artifact type file',
            default=os.getcwd()
        )
        return parser

    def generate_artifact(self, params):
        artifact_name = params.get("artifact_name")
        artifact_class_name = self.create_artifact_class_name(artifact_name)
        template_content = self.read_template_file()
        template_content = template_content.format(artifact_class_name, artifact_name)
        return self.write_template_file(artifact_name, template_content, params.get("destination_dir"))

    @classmethod
    def create_artifact_class_name(self, artifact_name):
        artifact_name_array = artifact_name.split("_")
        artifact_class_name = ""
        for part in artifact_name_array:
            artifact_class_name += part.capitalize()
        return artifact_class_name

    def read_template_file(self):
        template_path = os.path.join(os.path.dirname(__file__), self.template_file_name)
        template_file = open(template_path, "r")
        file_content = template_file.read()
        template_file.close()
        return file_content

    @classmethod
    def write_template_file(self, artifact_name, content, dest):
        artifact_file = open(dest, "w")
        artifact_file.write(content)
        artifact_file.close()

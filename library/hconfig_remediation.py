#!/usr/bin/env python


import os.path
import yaml

from ansible.module_utils.basic import AnsibleModule
from hier_config.host import Host


# Copyright 2018 James Williams <james.williams@packetgeek.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

DOCUMENTATION = """
---
module: hconfig-remediation
short_description: Generates a remediation plan based on a templated configuration
description:
    - This module uses Hierarchical Configuration to consume a running configuration
      and a templated configuration to generate a configuration plan to bring a
      network device configuration in line with its templated configuration.
author: James Williams <james.williams@packetgeek.net>
requirements:
    - hier-config
options:
    hostname:
        description:
        - This is the hostname of the device that the remediation configuration
          is generated for.
        required: True
    compiled_config:
        description:
        - This file is what your configuration management compiles for your device.
          This file should be compiled as the source of truth.
        required: False
    compiled_config_string:
        description:
        - This is the string of configuration as it should exist on the device.
        required: False
    running_config:
        description:
        - This file is contains that is currently running on the device.
        required: True
    running_config_string:
        description:
        - This is the string of what is currently running on the device.
        required: False
    remediation_config:
        description:
        - This file is generated with the commands that should be executed to bring
          a device config up to spec with the compiled config.
        required: True
    os_role:
        description:
        - The os_role allows you to separate hier tags and options by os type, for
          example, 'os_ios' should be an ansible role located in
          roles/os_ios/{vars,templates}. The os_role should contain two yaml files
          in its vars folder:
          - roles/{{ os_role }}/vars/hierarchical_configuration_tags.yml
          - roles/{{ os_role }}/vars/hierarchical_configuration_options.yml
          An os_role failing to have those files will break the remediation builder.
        required: True
    include_tags:
        description:
        - By specifying tags, you can limit the potential remediation to specific
          commands or sections of config.
        required: False
    exclude_tags:
        description:
        - By specifying tags, you can exclude the potential remediation to specific
          commands or sections of config.
        required: False
    options_file:
        description:
        - The hier_config options yaml file with the settings used to
        parse and return the configuration updates.
        - If not provided, the module defaults to roles/{{ os_role }}/vars/hierarchical_configuration_options.yml
        required: False
    tags_file:
        description:
        - The hier_config tags yaml file with the settings used to tag configuration updates.
        - If not provided, the module defaults to roles/{{ os_role }}/vars/hierarchical_configuration_tags.yml
        required: False
"""

EXAMPLES = """

- name: hconfig-remediation with tags
  hconfig-remediation:
    hostname: "example.rtr"
    compiled_config: "compiled-template.conf"
    running_config: "running-config.conf"
    remediation_config: "remediation.conf"
    os_role: "os_ios"
    config_tags: "safe"

- name: hconfig-remediation with multiple tags
  hconfig-remediation:
    hostname: "example.rtr"
    compiled_config: "compiled-template.conf"
    running_config: "running-config.conf"
    remediation_config: "remediation.conf"
    os_role: "os_ios"
    exclude_tags:
    - dangerous
    include_tags:
    - "aaa"
    - "tacacs"

- name: net-remediation without tags
  hconfig-remediation:
    hostname: "example.rtr"
    compiled_config: "compiled.conf"
    running_config: "running.conf"
    remediation_config: "remediation.conf"
    os_role: "os_ios"
"""


def _load_config(config_type, module):
    config = ''
    config_file = True

    if module.params["{}_config".format(config_type)]:
        config = module.params["{}_config".format(config_type)]
        if not os.path.isfile(config):
            module.fail_json(msg="Error opening {}.".format(config))
    elif module.params["{}_config_string".format(config_type)]:
        config = module.params["{}_config_string".format(config_type)]
        config_file = False
    else:
        module.fail_json(msg="No {} config specified".format(config))

    return {"config": config, "from_file": config_file}


def _load_hier(data, os_role, module):
    data_file = module.params["{}_file".format(data)]
    hier_data = dict()

    if data_file is None:
        data_file = 'roles/{}/vars/hierarchical_configuration_{}.yml'.format(
            os_role, data)

    if os.path.isfile(data_file):
        with open(data_file) as tmp:
            hier_data = yaml.safe_load(tmp.read())
    else:
        module.fail_json(msg="Error opening {}".format(data_file))

    return hier_data


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(required=True, type='str'),
            compiled_config=dict(required=False, type='str'),
            compiled_config_string=dict(required=False, type='str'),
            running_config=dict(required=False, type='str'),
            running_config_string=dict(required=False, type='str'),
            remediation_config=dict(required=False, type='str'),
            os_role=dict(required=True, type='str'),
            options_file=dict(required=False, type='str'),
            tags_file=dict(required=False, type='str'),
            include_tags=dict(required=False, type='list'),
            exclude_tags=dict(required=False, type='list'),
        ),
        required_one_of=[
            ['compiled_config', 'compiled_config_string'],
            ['running_config', 'running_config_string'],
        ],
        mutually_exclusive=[
            ['compiled_config', 'compiled_config_string'],
            ['running_config', 'running_config_string'],
        ],
        supports_check_mode=False,
    )
    hostname = module.params['hostname']

    running_config = _load_config("running", module=module)
    compiled_config = _load_config("compiled", module=module)
    remediation_config = module.params['remediation_config']
    os_role = module.params['os_role']
    operating_system = os_role.strip('os_')

    include_tags = list()
    if module.params['include_tags']:
        include_tags = list(module.params['include_tags'])

    exclude_tags = list()
    if module.params['exclude_tags']:
        exclude_tags = list(module.params['exclude_tags'])

    hier_options = _load_hier("options", os_role=os_role, module=module)
    hier_tags = _load_hier("tags", os_role=os_role, module=module)

    host = Host(hostname, operating_system, hier_options)

    host.load_config_from(config_type="running",
                          name=running_config["config"],
                          load_file=running_config["from_file"])
    host.load_config_from(config_type="compiled",
                          name=compiled_config["config"],
                          load_file=compiled_config["from_file"])
    host.load_tags(hier_tags, load_file=False)
    host.load_remediation()

    if include_tags or exclude_tags:
        host.filter_remediation(include_tags=include_tags,
                                exclude_tags=exclude_tags)

    remediation_config_string = host.facts['remediation_config_raw']

    if remediation_config is not None:
        with open(remediation_config, 'w') as tmp:
            tmp.write(remediation_config_string)

    changed = False
    if remediation_config_string:
        changed = True

    module.exit_json(changed=changed, response=remediation_config_string)


if __name__ == "__main__":
    main()

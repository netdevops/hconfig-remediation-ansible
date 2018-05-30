#!/usr/bin/env python

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

DOCUMENTATION = '''
---
module: hconfig-remediation
short_description: Generates a remediation plan based on a templated configuration
description:
- This module uses Hierarchical Configuration to consume a running configuration and a templated configuration to
  generate a configuration plan to bring a network device configuration in line with its templated configuration.
author: James Williams <james.williams@packetgeek.net>
requirements:
- hier-config
options:
  hostname:
    description:
    - This is the hostname of the device that the remediation configuration is generated for.
    required: yes
  compiled_config:
    description:
    - This file is what your configuration management compiles for your device.
    - This file is the configuration as it should exist on the device.
    required: no
  compiled_config_string:
    description:
    - This is the string of configuration as it should exist on the device.
    required: no
  running_config:
    description:
    - This file contains what is currently running on the device.
    required: no
  running_config_string:
    description:
    - This is the string of what is currently running on the device.
    required: no
  remediation_config:
    description:
    - This file is generated with the commands that should be executed to bring
      a device config up to spec with the compiled config.
    required: no
  os_role:
    description:
    - The os_role allows you to separate hier tags and options by os type, for
      example, 'os_ios' should be an ansible role located in
      roles/os_ios/{vars,templates}.
    - The os_role var will default options and tags files as following:
      - roles/{{ os_role }}/vars/hierarchical_configuration_tags.yml
      - roles/{{ os_role }}/vars/hierarchical_configuration_options.yml
    required: no
  config_tags:
    description:
    - By specifying tags, you can limit the potentiail remediations to specific
      commands or sections of config.
  options_file:
    description:
    - The hier_config options yaml file with the settings used to
      parse and return the configuration updates.
    - If not provided, the module defaults to roles/{{ os_role }}/vars/hierarchical_configuration_options.yml
    required: no
  tags_file:
    description:
    - The hier_config tags yaml file with the settings used to tag configuration updates.
    - If not provided, the module defaults to roles/{{ os_role }}/vars/hierarchical_configuration_tags.yml
    required: no
'''

EXAMPLES = '''

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
    config_tags:
    - "aaa"
    - "tacacs"

- name: net-remediation without tags
  hconfig-remediation:
    hostname: "example.rtr"
    compiled_config: "compiled.conf"
    running_config: "running.conf"
    remediation_config: "remediation.conf"
    os_role: "os_ios"
'''
from ansible.module_utils.basic import AnsibleModule
from hier_config import HConfig

import os.path
import yaml


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
            config_tags=dict(required=False, type='list'),
            options_file=dict(required=False, type='str'),
            tags_file=dict(required=False, type='str'),
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
    compiled_config = module.params['compiled_config']
    if compiled_config is not None:
        if not os.path.isfile(compiled_config):
            module.fail_json(msg="Error opening {}.".format(compiled_config))
    else:
        compiled_config_string = module.params['compiled_config_string']
    running_config = module.params['running_config']
    if running_config is not None:
        if not os.path.isfile(running_config):
            module.fail_json(msg="Error opening {}.".format(running_config))
    else:
        running_config_string = module.params['running_config_string']
    remediation_config = module.params['remediation_config']
    os_role = module.params['os_role']
    operating_system = os_role.strip('os_')
    config_tags = module.params['config_tags']
    options_file = module.params['options_file']
    if options_file is None:
        options_file = 'roles/{}/vars/hierarchical_configuration_options.yml'.format(os_role)
    tags_file = module.params['tags_file']
    if tags_file is None:
        tags_file = 'roles/{}/vars/hierarchical_configuration_tags.yml'.format(os_role)

    for item in options_file, tags_file:
        if not os.path.isfile(item):
            module.fail_json(msg="Error opening {}.".format(item))

    hier_options = yaml.load(open(options_file))
    hier_tags = yaml.load(open(tags_file))

    running_hier = HConfig(hostname=hostname, os=operating_system, options=hier_options)
    if running_config is not None:
        running_hier.load_from_file(running_config)
    else:
        running_hier.load_from_string(running_config_string)

    compiled_hier = HConfig(hostname=hostname, os=operating_system, options=hier_options)
    if compiled_config is not None:
        compiled_hier.load_from_file(compiled_config)
    else:
        compiled_hier.load_from_string(compiled_config_string)

    remediation_hier = running_hier.config_to_get_to(compiled_hier)
    remediation_hier.add_sectional_exiting()
    remediation_hier.set_order_weight()
    remediation_hier.add_tags(hier_tags)

    remediation_config_list = [
        line.cisco_style_text() for line in remediation_hier.all_children_sorted()
        if config_tags is None or line.tags.intersection(config_tags)
    ]
    remediation_config_lines = '\n'.join(remediation_config_list)

    if remediation_config is not None:
        with open(remediation_config, 'w') as f:
            f.write(remediation_config_lines)

    if remediation_config_lines:
        changed = True
    else:
        changed = False
    
    module.exit_json(changed=changed, response=remediation_config_lines)


if __name__ == "__main__":
    main()

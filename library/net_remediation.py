#!/usr/local/bin/python3

# Copyright 2016 James Williams <james.williams@packetgeek.net>
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
module: net-remediation
short_description: Generates a remediation plan based on a templated configuration
description:
    - This module uses Hierarchical Configuration to consume a running configuration
      and a templated configuration to generate a configuration plan to bring a
      network device configuration in line with its templated configuration.
author: James Williams <james.williams@packetgeek.net>
requirements:
    - hierarchical_configuration
options:
    compiled_config:
        description:
        - This file is what your configuration management compiles for your device.
          This file should be compiled as the source of truth.
        required: True
    running_config:
        description:
        - This file is contains that is currently running on the device.
        required: True
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
    config_tags:
        description:
        - By specifying tags, you can limit the potentiail remediations to specific
          commands or sections of config.
        required: False
'''

EXAMPLES = '''

# net-remediation with tags
- net-remediation:
    compiled_config: "compiled-template.conf"
    running_config: "running-config.conf"
    remediation_config: "remediation.conf"
    os_role: "os_ios"
    config_tags:
    - safe

# net-remediation without tags
- net-remediation:
    compiled_config: "compiled.conf"
    running_config: "running.conf"
    remediation_config: "remediation.conf"
    os_role: "os_ios"
'''

from hierarchical_configuration import HierarchicalConfiguration

import os.path
import yaml


def main():
    module = AnsibleModule(
        argument_spec=dict(
            compiled_config=dict(required=True),
            running_config=dict(required=True),
            remediation_config=dict(required=True),
            os_role=dict(required=True),
            config_tags=dict(required=False)
        ),
        required_together=(
            ['compiled_config',
             'running_config',
             'remediation_config',
             'os_role']
        ),
        supports_check_mode=False
    )

    compiled_config = str(module.params['compiled_config'])
    running_config = str(module.params['running_config'])
    remediation_config = str(module.params['remediation_config'])
    os_role = str(module.params['os_role'])
    if module.params['config_tags']:
        config_tags = list(module.params['config_tags'])
    else:
        config_tags = False

    hier_files = ['hierarchical_configuration_options.yml',
                  'hierarchical_configuration_tags.yml']

    for item in hier_files:
        if not os.path.isfile('roles/{}/vars/{}'.format(
                os_role, item)):
            module.fail_json(msg="Error opening {}.".format(item))

    hier_options = yaml.load(open('roles/{}/vars/{}'.format(
        os_role,
        'hierarchical_configuration_options.yml')))

    hier_tags = yaml.load(open('roles/{}/vars/{}'.format(
        os_role,
        'hierarchical_configuration_tags.yml')))

    if os.path.isfile(running_config):
        running_hier = HierarchicalConfiguration(options=hier_options)
        running_hier.from_file(running_config)
    else:
        module.fail_json(msg="Error opening {}.".format(running_config))

    if os.path.isfile(compiled_config):
        compiled_hier = HierarchicalConfiguration(options=hier_options)
        compiled_hier.from_file(compiled_config)
    else:
        module.fail_json(msg="Error opening {}.".format(compiled_config))

    remediation_hier = compiled_hier.deep_diff_tree_with(running_hier)
    remediation_hier.set_order_weight()
    remediation_hier.add_sectional_exiting()
    remediation_hier.add_tags(hier_tags)

    with open(remediation_config, 'w') as f:
        if config_tags:
            for line in remediation_hier.to_detailed_ouput():
                if line['tags'] in config_tags:
                    f.write('{}\n'.format(line['text']))
        else:
            for line in remediation_hier.to_detailed_ouput():
                f.write('{}\n'.format(line['text']))

    with open(remediation_config) as f:
        remediation_config = f.read()

    results = dict()
    results['response'] = remediation_config

    if len(remediation_config) > 0:
        module.exit_json(changed=True, **results)
    else:
        module.exit_json(changed=False)


from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()

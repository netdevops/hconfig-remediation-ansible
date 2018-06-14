#!/usr/bin/env python

from ansible.module_utils.basic import AnsibleModule, return_values
from hier_config.host import Host

import os.path
import yaml


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
"""

EXAMPLES = """

# hconfig-remediation with tags
- hconfig-remediation:
    hostname: "example.rtr"
    compiled_config: "compiled-template.conf"
    running_config: "running-config.conf"
    remediation_config: "remediation.conf"
    os_role: "os_ios"
    include_tags:
    - safe
    exclude_tags:
    - dangerous

# net-remediation without tags
- hconfig-remediation:
    hostname: "example.rtr"
    compiled_config: "compiled.conf"
    running_config: "running.conf"
    remediation_config: "remediation.conf"
    os_role: "os_ios"
"""


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(required=True),
            compiled_config=dict(required=True),
            running_config=dict(required=True),
            remediation_config=dict(required=True),
            os_role=dict(required=True),
            include_tags=dict(required=False, type='list'),
            exclude_tags=dict(required=False, type='list'),
        ),
        required_together=(
            ['hostname',
             'compiled_config',
             'running_config',
             'remediation_config',
             'os_role']
        ),
        supports_check_mode=False
    )

    hostname = str(module.params['hostname'])
    compiled_config = str(module.params['compiled_config'])
    running_config = str(module.params['running_config'])
    remediation_config = str(module.params['remediation_config'])
    os_role = str(module.params['os_role'])
    operating_system = os_role.strip('os_')

    if module.params['include_tags']:
        include_tags = list(module.params['include_tags'])
    else:
        include_tags = list()

    if module.params['exclude_tags']:
        exclude_tags = list(module.params['exclude_tags'])
    else:
        exclude_tags = list()

    hier_files = ['hierarchical_configuration_options.yml',
                  'hierarchical_configuration_tags.yml']

    for item in hier_files:
        if not os.path.isfile('roles/{}/vars/{}'.format(
                os_role, item)):
            module.fail_json(msg="Error opening {}.".format(item))

    hier_options = yaml.safe_load(open('roles/{}/vars/{}'.format(
        os_role,
        'hierarchical_configuration_options.yml')))

    hier_tags = yaml.safe_load(open('roles/{}/vars/{}'.format(
        os_role,
        'hierarchical_configuration_tags.yml')))

    host = Host(hostname, operating_system, hier_options)

    if os.path.isfile(running_config):
        host.load_config_from(config_type="running", name=running_config)
    else:
        module.fail_json(msg="Error opening {}.".format(running_config))

    if os.path.isfile(compiled_config):
        host.load_config_from(config_type="compiled", name=compiled_config)
    else:
        module.fail_json(msg="Error opening {}.".format(compiled_config))

    host.load_tags(hier_tags, file=False)
    host.load_remediation()

    if include_tags or exclude_tags:
        host.filter_remediation(include_tags=include_tags, exclude_tags=exclude_tags)

    with open(remediation_config, 'w') as f:
        f.write(host.facts['remediation_config_raw'])

    with open(remediation_config) as f:
        remediation_config = f.read()

    results = dict()
    results['response'] = remediation_config

    if remediation_config:
        module.exit_json(changed=True, **results)
    else:
        module.exit_json(changed=False)


if __name__ == "__main__":
    main()

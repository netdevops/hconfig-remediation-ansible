#!/usr/bin/env python


import os.path
import yaml
import hashlib

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
module: netdevops.hier_config.remediation
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
    generated_config:
        description:
        - This file is what your configuration management compiles for your device.
          This file should be generated as the source of truth.
        required: False
    generated_config_string:
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
          a device config up to spec with the generated config.
        required: False
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

- name: netdevops.hier_config.remediation with tags
  netdevops.hier_config.remediation:
    hostname: "example.rtr"
    generated_config: "generated-template.conf"
    running_config: "running-config.conf"
    remediation_config: "remediation.conf"
    os_role: "os_ios"
    include_tags: "safe"

- name: netdevops.hier_config.remediation with multiple tags
  netdevops.hier_config.remediation:
    hostname: "example.rtr"
    generated_config: "generated-template.conf"
    running_config: "running-config.conf"
    remediation_config: "remediation.conf"
    os_role: "os_ios"
    exclude_tags:
    - dangerous
    include_tags:
    - "aaa"
    - "tacacs"

- name: netdevops.hier_config.remediation without tags
  netdevops.hier_config.remediation:
    hostname: "example.rtr"
    generated_config: "generated.conf"
    running_config: "running.conf"
    remediation_config: "remediation.conf"
    os_role: "os_ios"
"""


def _load_hier(data, os_role, module):
    data_file = module.params[f"{data}_file"]
    hier_data = dict()

    if data_file is None:
        data_file = f"roles/{os_role}/vars/hierarchical_configuration_{data}.yml"

    if os.path.isfile(data_file):
        with open(data_file) as tmp:
            hier_data = yaml.safe_load(tmp.read())
    else:
        module.fail_json(msg=f"Error opening {data_file}")

    return hier_data


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(required=True, type="str"),
            generated_config=dict(required=False, type="str"),
            generated_config_string=dict(required=False, type="str"),
            running_config=dict(required=False, type="str"),
            running_config_string=dict(required=False, type="str"),
            remediation_config=dict(required=False, type="str"),
            os_role=dict(required=True, type="str"),
            options_file=dict(required=False, type="str"),
            tags_file=dict(required=False, type="str"),
            include_tags=dict(required=False, type="list"),
            exclude_tags=dict(required=False, type="list"),
        ),
        required_one_of=[
            ["generated_config", "generated_config_string"],
            ["running_config", "running_config_string"],
        ],
        mutually_exclusive=[
            ["generated_config", "generated_config_string"],
            ["running_config", "running_config_string"],
        ],
        supports_check_mode=False,
    )
    changed = False
    hostname = module.params["hostname"]
    remediation_config = module.params["remediation_config"]
    os_role = module.params["os_role"]
    operating_system = os_role.strip("os_")
    include_tags = (
        module.params["include_tags"] if module.params["include_tags"] else None
    )
    exclude_tags = (
        module.params["exclude_tags"] if module.params["exclude_tags"] else None
    )
    hier_options = _load_hier("options", os_role=os_role, module=module)
    hier_tags = _load_hier("tags", os_role=os_role, module=module)

    host = Host(hostname, operating_system, hier_options)
    if module.params["running_config"]:
        host.load_running_config_from_file(file=module.params["running_config"])
    else:
        host.load_running_config(config_text=module.params["running_config_string"])

    if module.params["generated_config"]:
        host.load_generated_config_from_file(file=module.params["generated_config"])
    else:
        host.load_generated_config(config_text=module.params["generated_config_string"])

    host.load_tags(hier_tags)
    host.remediation_config()
    remediation_obj = host.remediation_config_filtered_text(
        include_tags=include_tags, exclude_tags=exclude_tags
    )

    remediation_config_string = "".join([line for line in remediation_obj])

    if remediation_config is not None:
        md5_original = None
        if os.path.isfile(remediation_config):
            md5_original = hashlib.md5(
                open(remediation_config).read().encode("utf-8")
            ).hexdigest()

        with open(remediation_config, "w") as tmp:
            tmp.write(remediation_config_string)

        md5_new = hashlib.md5(
            open(remediation_config).read().encode("utf-8")
        ).hexdigest()

        if len({md5_new, md5_original}) > 1:
            changed = True
    else:
        if remediation_config_string:
            changed = True

    module.exit_json(changed=changed, response=remediation_config_string)


if __name__ == "__main__":
    main()

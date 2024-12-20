#!/usr/bin/env python3

import os.path
import hashlib
from ansible.module_utils.basic import AnsibleModule
from hier_config import WorkflowRemediation, get_hconfig, Platform
from hier_config.utils import read_text_from_file, load_hier_config_tags

DOCUMENTATION = """
---
module: netdevops.hier_config.remediation
short_description: Generates a remediation plan based on a templated configuration
description:
    - Uses Hierarchical Configuration (v3) to compare the running configuration with the intended configuration
      and generate a remediation plan to bring a device into compliance.
author: James Williams, updated by [Your Name]
requirements:
    - hier-config >= 3.0
options:
    hostname:
        description:
        - Hostname of the device being remediated.
        required: True
    generated_config:
        description:
        - Path to the generated configuration file.
        required: False
    generated_config_string:
        description:
        - String representation of the generated configuration.
        required: False
    running_config:
        description:
        - Path to the running configuration file.
        required: False
    running_config_string:
        description:
        - String representation of the running configuration.
        required: False
    remediation_config:
        description:
        - Path to the file where the remediation configuration will be saved.
        required: False
    platform:
        description:
        - The platform (e.g., CISCO_IOS, JUNIPER_JUNOS).
        required: True
    include_tags:
        description:
        - Tags to include during remediation.
        required: False
    exclude_tags:
        description:
        - Tags to exclude during remediation.
        required: False
    tags_file:
        description:
        - Path to a file containing tag rules.
        required: False
"""

EXAMPLES = """
- name: Generate remediation plan with tags
  netdevops.hier_config.remediation:
    hostname: "example.rtr"
    generated_config: "generated-template.conf"
    running_config: "running-config.conf"
    remediation_config: "remediation.conf"
    platform: "CISCO_IOS"
    include_tags: ["safe"]

- name: Generate remediation plan without tags
  netdevops.hier_config.remediation:
    hostname: "example.rtr"
    generated_config: "generated.conf"
    running_config: "running.conf"
    remediation_config: "remediation.conf"
    platform: "CISCO_IOS"
"""


def load_config(file_path: str, config_string: str, platform: Platform):
    """Load configuration from a file or string."""
    if file_path:
        return get_hconfig(platform, read_text_from_file(file_path))
    elif config_string:
        return get_hconfig(platform, config_string)
    else:
        raise ValueError(
            "Either file path or string representation of the configuration must be provided."
        )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(required=True, type="str"),
            generated_config=dict(required=False, type="str"),
            generated_config_string=dict(required=False, type="str"),
            running_config=dict(required=False, type="str"),
            running_config_string=dict(required=False, type="str"),
            remediation_config=dict(required=False, type="str"),
            platform=dict(required=True, type="str"),
            include_tags=dict(required=False, type="list"),
            exclude_tags=dict(required=False, type="list"),
            tags_file=dict(required=False, type="str"),
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

    params = module.params
    hostname = params["hostname"]
    platform = Platform[params["platform"]]
    remediation_config_path = params["remediation_config"]
    include_tags = set(params["include_tags"] or [])
    exclude_tags = set(params["exclude_tags"] or [])
    tags_file = params["tags_file"]

    try:
        running_config = load_config(
            params["running_config"], params["running_config_string"], platform
        )
        generated_config = load_config(
            params["generated_config"], params["generated_config_string"], platform
        )

        # Load tag rules if provided
        tag_rules = load_hier_config_tags(tags_file) if tags_file else None

        # Create the WorkflowRemediation object
        workflow = WorkflowRemediation(
            running_config=running_config, generated_config=generated_config
        )

        # Apply tags if provided
        if tag_rules:
            workflow.apply_remediation_tag_rules(tag_rules)

        # Generate filtered remediation configuration
        remediation_config = workflow.remediation_config_filtered_text(
            include_tags=include_tags, exclude_tags=exclude_tags
        )

        remediation_config_str = "".join(remediation_config)
        changed = bool(remediation_config_str)

        # Write to file if specified
        if remediation_config_path:
            md5_original = None
            if os.path.isfile(remediation_config_path):
                md5_original = hashlib.md5(
                    open(remediation_config_path).read().encode("utf-8")
                ).hexdigest()

            with open(remediation_config_path, "w") as file:
                file.write(remediation_config_str)

            md5_new = hashlib.md5(
                open(remediation_config_path).read().encode("utf-8")
            ).hexdigest()
            changed = md5_new != md5_original

        module.exit_json(changed=changed, remediation_config=remediation_config_str)

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

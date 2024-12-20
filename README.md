# hconfig-remediation-ansible
An Ansible Module for utilizing Hierarchical Configuration

[![CodeFactor](https://www.codefactor.io/repository/github/netdevops/hconfig-remediation-ansible/badge)](https://www.codefactor.io/repository/github/netdevops/hconfig-remediation-ansible)

Testing
=======

## Install from Github

1. [Install Poetry](https://python-poetry.org/docs/)
2. Clone from Github: `https://github.com/netdevops/hconfig-remediation-ansible`
3. Install dependencies: `cd hconfig-remediation-ansible; poetry install`
4. Create ansible-galaxy collection: `ansible-galaxy collection build -f`
5. Install ansible-galaxy collection: `ansible-galaxy collection install netdevops-hier_config-*.tar.gz -f`
6. Execute example playbook: `cd example; ansible-playbook -i inventory test.pb.yml -v`

## Example Output

```bash
% ansible-playbook -i inventory test.pb.yml -v
No config file found; using defaults

PLAY [all] ****************************************************************************************************************************************************************************************

TASK [BUILD REMEDIATION CONFIG WITHOUT TAGS] ******************************************************************************************************************************************************
changed: [router1] => {"changed": true, "response": "aaa group server tacacs+ MYTACACS\n  no server-private 10.0.0.1 port 49\n  server-private 10.0.0.2 port 49\n    key secretkey\nipv4 access-list vty\n  permit ip host 10.4.1.9 any\n  permit ip any 10.4.106.0 0.0.0.255\n  permit ip 10.0.150.0 0.127.0.255 any\nrouter ospf 65000\n  auto-cost reference-bandwidth 1000000\nrouter bgp 65000\n  no neighbor RR-Client remote-as 65000\n  no neighbor RR-Client update-source Loopback0\n  no maximum-paths ibgp 16\n  neighbor RR-CLIENT peer-group\n  neighbor RR-CLIENT remote-as 65000\n  neighbor RR-CLIENT update-source Loopback0\n  neighbor 10.4.2.234 remote-as 65000\n  neighbor 10.4.2.234 peer-group RR-CLIENT\n  neighbor 10.4.2.234 description RR1B\n  neighbor 10.4.2.235 peer-group RR-CLIENT\n  address-family ipv4\n    no neighbor RR-Client soft-reconfiguration inbound\n    neighbor RR-CLIENT soft-reconfiguration inbound\n    neighbor 10.4.2.234 activate\n    maximum-paths ibgp 16\n    exit-address-family"}

TASK [BUILD REMEDIATION CONFIG WITH INCLUDE TAGS] *************************************************************************************************************************************************
changed: [router1] => {"changed": true, "response": "ipv4 access-list vty\n  permit ip host 10.4.1.9 any\n  permit ip any 10.4.106.0 0.0.0.255\n  permit ip 10.0.150.0 0.127.0.255 any\nrouter bgp 65000\n  neighbor RR-CLIENT peer-group\n  neighbor RR-CLIENT remote-as 65000\n  neighbor RR-CLIENT update-source Loopback0\n  neighbor 10.4.2.234 remote-as 65000\n  neighbor 10.4.2.234 peer-group RR-CLIENT\n  neighbor 10.4.2.234 description RR1B\n  neighbor 10.4.2.235 peer-group RR-CLIENT\n  address-family ipv4\n    neighbor RR-CLIENT soft-reconfiguration inbound\n    neighbor 10.4.2.234 activate\n    maximum-paths ibgp 16\n    no neighbor RR-Client soft-reconfiguration inbound\n    exit-address-family\n  no neighbor RR-Client remote-as 65000\n  no neighbor RR-Client update-source Loopback0"}

TASK [BUILD REMEDIATION CONFIG WITH EXCLUDE TAGS] *************************************************************************************************************************************************
changed: [router1] => {"changed": true, "response": "ipv4 access-list vty\n  permit ip host 10.4.1.9 any\n  permit ip any 10.4.106.0 0.0.0.255\n  permit ip 10.0.150.0 0.127.0.255 any\nrouter ospf 65000\n  auto-cost reference-bandwidth 1000000\nrouter bgp 65000\n  no maximum-paths ibgp 16\n  neighbor RR-CLIENT peer-group\n  neighbor RR-CLIENT remote-as 65000\n  neighbor RR-CLIENT update-source Loopback0\n  neighbor 10.4.2.234 remote-as 65000\n  neighbor 10.4.2.234 peer-group RR-CLIENT\n  neighbor 10.4.2.234 description RR1B\n  neighbor 10.4.2.235 peer-group RR-CLIENT\n  address-family ipv4\n    neighbor RR-CLIENT soft-reconfiguration inbound\n    neighbor 10.4.2.234 activate\n    maximum-paths ibgp 16\n    no neighbor RR-Client soft-reconfiguration inbound\n    exit-address-family\n  no neighbor RR-Client remote-as 65000\n  no neighbor RR-Client update-source Loopback0"}

TASK [BUILD REMEDIATION CONFIG WITH EXCLUDE TAGS] *************************************************************************************************************************************************
changed: [router1] => {"changed": true, "response": "ipv4 access-list vty\n  permit ip host 10.4.1.9 any\n  permit ip any 10.4.106.0 0.0.0.255\n  permit ip 10.0.150.0 0.127.0.255 any\nrouter bgp 65000\n  neighbor RR-CLIENT peer-group\n  neighbor RR-CLIENT remote-as 65000\n  neighbor RR-CLIENT update-source Loopback0\n  neighbor 10.4.2.234 remote-as 65000\n  neighbor 10.4.2.234 peer-group RR-CLIENT\n  neighbor 10.4.2.234 description RR1B\n  neighbor 10.4.2.235 peer-group RR-CLIENT\n  address-family ipv4\n    neighbor RR-CLIENT soft-reconfiguration inbound\n    neighbor 10.4.2.234 activate\n    maximum-paths ibgp 16\n    no neighbor RR-Client soft-reconfiguration inbound\n    exit-address-family\n  no neighbor RR-Client remote-as 65000\n  no neighbor RR-Client update-source Loopback0"}

PLAY RECAP ****************************************************************************************************************************************************************************************
router1                    : ok=4    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```
## Example Playbook
```yaml
---
- hosts: all
  gather_facts: False
  connection: local

  tasks:
  - name: BUILD REMEDIATION CONFIG WITHOUT TAGS
    netdevops.hier_config.remediation:
      hostname: router1.rtr
      running_config: router1-running.conf
      generated_config: router1-generated.conf
      remediation_config: router1-remediation.conf
      platform: "CISCO_XR"

  - name: BUILD REMEDIATION CONFIG WITH INCLUDE TAGS
    netdevops.hier_config.remediation:
      hostname: router1.rtr
      running_config: router1-running.conf
      generated_config: router1-generated.conf
      remediation_config: router1-remediation-with-include-tags.conf
      platform: "CISCO_XR"
      include_tags:
        - push

  - name: BUILD REMEDIATION CONFIG WITH EXCLUDE TAGS
    netdevops.hier_config.remediation:
      hostname: router1.rtr
      running_config: router1-running.conf
      generated_config: router1-generated.conf
      remediation_config: router1-remediation-with-exclude-tags.conf
      platform: "CISCO_XR"
      exclude_tags:
        - ignore

  - name: BUILD REMEDIATION CONFIG WITH BOTH INCLUDE AND EXCLUDE TAGS
    netdevops.hier_config.remediation:
      hostname: router1.rtr
      running_config: router1-running.conf
      generated_config: router1-generated.conf
      remediation_config: router1-remediation-with-tags.conf
      platform: "CISCO_XR"
      include_tags:
        - push
      exclude_tags:
        - ignore
```
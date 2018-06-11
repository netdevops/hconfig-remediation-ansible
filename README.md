# hconfig-remediation-ansible
An Ansible Module for utilizing Hierarchical Configuration

=======
Testing
=======

```
$ cd ./example
$ virtualenv env
$ source env/bin/activate
(env)$ pip install hier-config ansible

(env)$ ansible-playbook -i inventory test.pb.yml -v
No config file found; using defaults

PLAY [all] *******************************************************************************************************************

TASK [BUILD REMEDIATION CONFIG WITHOUT TAGS] *********************************************************************************
changed: [router1] => {"changed": true, "response": "no ip access-list extended vty\nipv4 access-list vty\n  permit ip host 10.4.1.9 any\n  permit ip any 10.4.106.0 0.0.0.255\n  permit ip 10.0.150.0 0.127.0.255 any\n  permit ip 10.0.125.0 0.127.0.255 any\n  permit ip 10.4.108.0 0.0.0.15 any\n  permit ip host 10.4.126.56 any\n  permit ip 10.0.255.64 0.127.0.31 any\nrouter ospf 65000\n  max-metric router-lsa summary-lsa external-lsa on-startup wait-for-bgp\n  ispf\n  log-adjacency-changes\n  auto-cost reference-bandwidth 1000000\n  exit\nrouter bgp 65000\n  bgp default ipv4-unicast\n  no maximum-paths ibgp 8\n  bgp log-neighbor-changes\n  neighbor RR-Client peer-group\n  neighbor RR-Client remote-as 65000\n  neighbor RR-Client update-source Loopback0\n  neighbor 10.4.2.234 remote-as 65000\n  neighbor 10.4.2.234 peer-group RR-Client\n  neighbor 10.4.2.234 description RR1B\n  neighbor 10.4.2.235 remote-as 65000\n  neighbor 10.4.2.235 peer-group RR-Client\n  neighbor 10.4.2.235 description RR1A\n  maximum-paths ibgp 16\n  address-family ipv4\n    no maximum-paths ibgp 8\n    neighbor RR-Client soft-reconfiguration inbound\n    neighbor 10.4.2.234 activate\n    neighbor 10.4.2.235 activate\n    maximum-paths ibgp 16\n    no auto-summary\n    no synchronization\n  exit-address-family\n\n"}

TASK [BUILD REMEDIATION CONFIG WITH TAGS] ************************************************************************************
changed: [router1] => {"changed": true, "response": "ipv4 access-list vty\n  permit ip host 10.4.1.9 any\n  permit ip any 10.4.106.0 0.0.0.255\n  permit ip 10.0.150.0 0.127.0.255 any\n  permit ip 10.0.125.0 0.127.0.255 any\n  permit ip 10.4.108.0 0.0.0.15 any\n  permit ip host 10.4.126.56 any\n  permit ip 10.0.255.64 0.127.0.31 any\n\n"}

PLAY RECAP *******************************************************************************************************************
router1                    : ok=2    changed=2    unreachable=0    failed=0
```

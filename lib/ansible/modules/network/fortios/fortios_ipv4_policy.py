#!/usr/bin/python
#
# Ansible module to manage IPv4 policy objects in fortigate devices
# (c) 2017, Benjamin Jolivot <bjolivot@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'version': '1.0'
}

DOCUMENTATION = """
---
module: fortios_ipv4_policy
version_added: "2.3"
author: "Benjamin Jolivot (@bjolivot)"
short_description: Manage fortios firewall IPv4 policy objects
description:
  - This module provides management of firewall IPv4 policies on FortiOS devices.
extends_documentation_fragment: fortios
options:
  id:
    description:
      - Policy ID.
    required: true
  state:
    description:
      - Specifies if address need to be added or deleted.
    choices: ['present', 'absent']
    default: present
  src_intf:
    description:
      - Specifies source interface name.
    default: any
  dst_intf:
    description:
      - Specifies destination interface name.
    default: any
  src_addr:
    description:
      - Specifies source address (or group) object name(s).
    required: true
  src_addr_negate:
    description:
      - Negate source address param.
    default: false
    choices: ["true", "false"]
  dst_addr:
    description:
      - Specifies destination address (or group) object name(s).
    required: true
  dst_addr_negate:
    description:
      - Negate destination address param.
    default: false
    choices: ["true", "false"]
  policy_action:
    description:
      - Specifies accept or deny action policy.
    choices: ['accept', 'deny']
    required: true
    aliases: ['action']
  service:
    description:
      - "Specifies policy service(s), could be a list (ex: ['MAIL','DNS'])."
    required: true
    aliases:
      - services
  service_negate:
    description:
      - Negate policy service(s) defined in service value.
    default: false
    choices: ["true", "false"]
  schedule:
    description:
      - defines policy schedule.
    default: 'always'
  nat:
    description:
      - Enable or disable Nat.
    default: false
    choices: ["true", "false"]
  fixedport:
    description:
      - Use fixed port for nat.
    default: false
    choices: ["true", "false"]
  poolname:
    description:
      - Specifies NAT pool name.
  av_profile:
    description:
      - Specifies Antivirus profile name.
  webfilter_profile:
    description:
      - Specifies Webfilter profile name.
  ips_sensor:
    description:
      - Specifies IPS Sensor profile name.
  application_list:
    description:
      - Specifies Application Control name.
  comment:
    description:
      - free text to describe policy.
notes:
  - This module requires pyFG library.
"""

EXAMPLES = """
- name: Allow external DNS call
  fortios_ipv4_policy:
    host: 192.168.0.254
    username: admin
    password: password
    id: 42
    srcaddr: internal_network
    dstaddr: all
    service: dns
    nat: True
    state: present
    policy_action: accept

- name: Public Web
  fortios_ipv4_policy:
    host: 192.168.0.254
    username: admin
    password: password
    id: 42
    srcaddr: all
    dstaddr: webservers
    services:
      - http
      - https
    state: present
    policy_action: accept
"""

RETURN = """
firewall_address_config:
  description: full firewall adresses config string
  returned: always
  type: string
change_string:
  description: The commands executed by the module
  returned: only if config changed
  type: string
msg_error_list:
  description: "List of errors returned by CLI (use -vvv for better readability)."
  returned: only when error
  type: string
"""

from ansible.module_utils.fortios import fortios_argument_spec, fortios_required_if
from ansible.module_utils.fortios import backup, AnsibleFortios

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception


def main():
    argument_spec = dict(
        comment                   = dict(type='str'),
        id                        = dict(type='int', required=True),
        src_intf                  = dict(default='any'),
        dst_intf                  = dict(default='any'),
        state                     = dict(choices=['present', 'absent'], default='present'),
        src_addr                  = dict(required=True, type='list'),
        dst_addr                  = dict(required=True, type='list'),
        src_addr_negate           = dict(type='bool', default=False),
        dst_addr_negate           = dict(type='bool', default=False),
        policy_action             = dict(choices=['accept','deny'], required=True, aliases=['action']),
        service                   = dict(aliases=['services'], required=True, type='list'),
        service_negate            = dict(type='bool', default=False),
        schedule                  = dict(type='str', default='always'),
        nat                       = dict(type='bool', default=False),
        fixedport                 = dict(type='bool', default=False),
        poolname                  = dict(type='str'),
        av_profile                = dict(type='str'),
        webfilter_profile         = dict(type='str'),
        ips_sensor                = dict(type='str'),
        application_list          = dict(type='str'),
    )

    #merge global required_if & argument_spec from module_utils/fortios.py
    argument_spec.update(fortios_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=fortios_required_if,
    )

    #init forti object
    fortigate = AnsibleFortios(module)

    #test params
    #NAT related
    if not module.params['nat']:
        if module.params['poolname']:
            module.fail_json(msg='Poolname param requires NAT to be true.')
        if module.params['fixedport']:
            module.fail_json(msg='Fixedport param requires NAT to be true.')

    #id must be str(int) for pyFG to work
    policy_id = str(module.params['id'])

    #load config
    fortigate.load_config('firewall policy')

    #Absent State
    if module.params['state'] == 'absent':
        fortigate.candidate_config[path].del_block(policy_id)

    #Present state
    elif module.params['state'] == 'present':
        new_policy = fortigate.get_empty_configuration_block(policy_id, 'edit')

        #src / dest / service / interfaces
        new_policy.set_param('srcintf', '"%s"' % (module.params['src_intf']))
        new_policy.set_param('dstintf', '"%s"' % (module.params['dst_intf']))


        new_policy.set_param('srcaddr', " ".join('"' + item + '"' for item in module.params['src_addr']))
        new_policy.set_param('dstaddr', " ".join('"' + item + '"' for item in module.params['dst_addr']))
        new_policy.set_param('service', " ".join('"' + item + '"' for item in module.params['service']))

        # negate src / dest / service
        if module.params['src_addr_negate']:
            new_policy.set_param('srcaddr-negate', 'enable')
        if module.params['dst_addr_negate']:
            new_policy.set_param('dstaddr-negate', 'enable')
        if module.params['service_negate']:
            new_policy.set_param('service-negate', 'enable')

        # action
        new_policy.set_param('action', '%s' % (module.params['policy_action']))

        # Schedule
        new_policy.set_param('schedule', '%s' % (module.params['schedule']))

        #NAT
        if module.params['nat']:
            new_policy.set_param('nat', 'enable')
            if module.params['fixedport']:
                new_policy.set_param('fixedport', 'enable')
            if module.params['poolname'] is not None:
                new_policy.set_param('ippool', 'enable')
                new_policy.set_param('poolname', '"%s"' % (module.params['poolname']))

        #security profiles:
        if module.params['av_profile'] is not None:
            new_policy.set_param('av-profile', '"%s"' % (module.params['av_profile']))
        if module.params['webfilter_profile'] is not None:
            new_policy.set_param('webfilter-profile', '"%s"' % (module.params['webfilter_profile']))
        if module.params['ips_sensor'] is not None:
            new_policy.set_param('ips-sensor', '"%s"' % (module.params['ips_sensor']))
        if module.params['application_list'] is not None:
            new_policy.set_param('application-list', '"%s"' % (module.params['application_list']))

        # comment
        if module.params['comment'] is not None:
            new_policy.set_param('comment', '"%s"' % (module.params['comment']))

        #add the new policy to the device
        fortigate.add_block(policy_id, new_policy)

    #Apply changes
    fortigate.apply_changes()

if __name__ == '__main__':
    main()


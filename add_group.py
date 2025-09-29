#!/taiga/admin/iccp/nodemap/bin/hostvenv
from ldap3 import Server, Connection, ALL, Tls, extend, BASE
from datetime import datetime
import ssl
import csv
from adldap import Adldap
from ncsaldapapi import IccpNcsaLdap
import sys

def eprint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

if len(sys.argv) < 2:
    print("Usage: add_group <group> | \"<group1, group2,...>\"")
    sys.exit(1)

input_grps = list(map(str.strip, sys.argv[1].split(",")))

# create Adldap insance
adldap = Adldap(config_file="/taiga/admin/iccp/nodemap/conf/ug.config")

# create ldapapi instance
ldapapi = IccpNcsaLdap(config_file="/taiga/admin/iccp/nodemap/test/bin/config")

# load group nodemap
group_nodemap = adldap.get_nodemap_group()
##print(group_nodemap)

# load ldap group info
ldap_groups = adldap.get_ldap_groups()

#### load user nodemap
###user_nodemap = adldap.get_nodemap_user()

# timestamp for output
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

for input_grp in input_grps:
    input_grp_all = adldap.get_ad_group_by_dispname(input_grp)
    
    gprefix = adldap.config['LDAP']['group_prefix']
    ldapowner = ldapapi.config['API']['group_owner']
    prefix_input_grp = gprefix + input_grp
    if not [lgroup for lgroup in ldap_groups if lgroup['attributes']['cn'][0] == prefix_input_grp]: # if not in ldap
        newgid = int(input_grp_all['attributes']['gidNumber'])
        if newgid < 500000:
            newgid += 500000
            
        ####eprint("pre request: "+prefix_input_grp + " " + str(newgid) + " " + input_grp + " " + ldapowner)
        result = ldapapi.create_campus_cluster_groups(prefix_input_grp, newgid, input_grp, ldapowner)
        if result:
            if not [ngroup for ngroup in group_nodemap if ngroup['adname'] == input_grp]:
                group_nodemap.append({'adname': input_grp_all['attributes']['displayName'], 'adgid': str(input_grp_all['attributes']['gidNumber']), 'ldapname': prefix_input_grp, 'ldapgid': newgid})
        else:
            eprint("add_group: ERROR adding group :" + input_grp + " see api log for more information.")             

group_nodemap.sort(key=lambda x: x['adgid'])

# timestamp for output
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

output_ldap_groups = adldap.config['NODEMAP']['directory']+'/'+timestamp+'.group.nodemap'
with open(output_ldap_groups,'w', newline='') as gmapfile:
    fieldnames = ['adname','adgid','ldapname','ldapgid']
    writer = csv.DictWriter(gmapfile, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()
    writer.writerows(group_nodemap)

group_nodemap_current = adldap.config['NODEMAP']['directory']+'/'+adldap.config['NODEMAP']['group']

adldap.archive_and_link_new(group_nodemap_current, output_ldap_groups, adldap.config['NODEMAP']['directory'])

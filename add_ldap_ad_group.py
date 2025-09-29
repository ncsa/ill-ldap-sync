#!/taiga/admin/iccp/nodemap/bin/hostvenv
from adldap import Adldap
from datetime import datetime
import csv
import sys

if len(sys.argv) < 2:
    print("Usage: add_group <group> | \"<group1, group2,...>\"")
    sys.exit(1)

input_groups = list(map(str.strip, sys.argv[1].split(",")))

# create Adldap instance
adldap = Adldap(config_file="/taiga/admin/iccp/nodemap/conf/ug.config")

# LDAP Groups OU
ldapGroupsOU = adldap.config['LDAP_SYNC']['groups_ou']

# Get ldap sync map
ldapGroupSyncMap = adldap.get_ldap_sync_group_map()

# timestamp for output
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

# get DN's for all input groups
inputDNs = []
notfound = []
newgroups = []
for inGrp in input_groups:
    mapEntry = [mgroup for mgroup in ldapGroupSyncMap if mgroup['ldapname'] == inGrp]
    if mapEntry:
        print("{inGrp} already in sync map.\n")
        continue
    thisgroup = adldap.get_ldap_group(inGrp)
    if thisgroup:
        thisGrpCN = adldap.config['LDAP_SYNC']['prefix'] + inGrp
        thisGrpDN = 'cn='+ thisGrpCN  + ',' + ldapGroupsOU
        inputDNs.append(thisGrpDN)
        newGid = adldap.get_ldap_group_sync_next_gid()
        tgroup = adldap.add_ad_group(thisGrpDN,thisGrpCN,newGid)
        if tgroup:
            print("Success adding group {} to AD.\n".format(thisGrpDN))
            update = adldap.update_ldap_group_sync_next_gid()
            print(update)
            newGrpMap = {
                    'ldapname': inGrp,
                    'ldapgid': thisgroup[0]['attributes']['gidNumber'],
                    'adname': thisGrpCN,
                    'adgid': newGid
                    }
            newgroups.append(newGrpMap)
        else:
            print("Error adding group {} to AD.\n".format(thisGrpDN))
    else:
        notfound.append(inGrp)

print("Added the following groups:\n    {}".format('\n'.join(inputDNs)))
if notfound:
    print("The following groups were not found:\n    {}".format('\n'.join(notfound)))


if not newgroups:
    exit
else:
    
    newgroupsync = ldapGroupSyncMap
    newgroupsync.extend(newgroups)
    
    output_ldap_group_sync_map = adldap.config['LDAP_SYNC']['directory']+'/'+timestamp+'.group.ldapsync'
    with open(output_ldap_group_sync_map,'w', newline='') as gmapfile:
        fieldnames = ['ldapname','ldapgid','adname','adgid']
        writer = csv.DictWriter(gmapfile, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()
        writer.writerows(newgroupsync)
    
    ldap_group_sync_map_current = adldap.config['LDAP_SYNC']['directory']+'/'+adldap.config['LDAP_SYNC']['map']
    
    adldap.archive_and_link_new(ldap_group_sync_map_current, output_ldap_group_sync_map, adldap.config['LDAP_SYNC']['directory'])

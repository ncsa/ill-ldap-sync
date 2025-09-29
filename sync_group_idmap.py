#!/taiga/admin/iccp/nodemap/bin/hostvenv
from ldap3 import Server, Connection, ALL, Tls, extend, BASE
from datetime import datetime
import ssl
import csv
from adldap import Adldap
import os
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# create Adldap insance
adldap = Adldap(config_file="/taiga/admin/iccp/nodemap/conf/ug.config")

# load group nodemap
groupNodemap = adldap.get_nodemap_group()

# load ldap sync map
ldapGroupSyncMap = adldap.get_ldap_sync_group_map()

# timestamp for output
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

# Combine AD to LDAP group and LDAP to AD groups
combinedGroupNodemap = []
combinedGroupNodemap.extend(groupNodemap)
combinedGroupNodemap.extend(ldapGroupSyncMap)

## Determine what needs to be updated in maps
##### Get idmap
groupIdmap = adldap.get_idmap_group()

##### Check for groups in nodemap and not idmap
newldapgid = []
mismatchgid = []
newgidmap = []
for group in combinedGroupNodemap:
    #if not (group['aduidnum'],user['ldapuidnum']) in userIdmap:
    gids = [(x,y) for (x,y) in groupIdmap if (x,y) == (group['adgid'],group['ldapgid'])]
    agid = [(x,y) for (x,y) in groupIdmap if x == group['adgid']]
    ngid = [(x,y) for (x,y) in groupIdmap if y == group['ldapgid']]
    if not gids:
        if agid:
            if not ngid:
                print("NEWLDAPGROUP: idmap: {} nodemap:{}".format(agid, ','.join(group.values())))
                newldapgid.append({'idmap': adgid[0], 'nodemap': ','.joing(group.values())})   
            else:
                print("ad and ldap: {},{} nodemap: {}".format(agid,ngid,','.join(group.values())))
        else:
            if not ngid:
                print("new idmap: {}:{}".format(group['adgid'],group['ldapgid']))
                newgidmap.append("{}:{}".format(group['adgid'],group['ldapgid']))
            else:
                print("ADGIDNOMATCH: idmap: {} nodemap: {}".format(ngid, ','.join(group.values())))
                mismatchgid.append({'idmap': ngid[0], 'nodemap': ','.join(group.values())})

###### write files for idmap info
## write new gid idmap
new_gidmap_link = adldap.config['LUSTRE']['directory']+'/'+adldap.config['LUSTRE']['new_gids']
output_new_gidmap = adldap.config['LUSTRE']['directory']+'/'+timestamp+'.'+adldap.config['LUSTRE']['new_gids']
with open(output_new_gidmap, 'w', newline='\n') as ngidmap:
    for g in newgidmap:
        ngidmap.write("{}\n".format(g))
adldap.archive_and_link_new(new_gidmap_link,output_new_gidmap,adldap.config['LUSTRE']['directory'])

## write new ldap group file
output_newldap_gids = adldap.config['NODEMAP']['directory']+'/archive/'+timestamp+'.'+adldap.config['NODEMAP']['maptoldapgid']
with open(output_newldap_gids, 'w', newline='\n') as newldapf:
    for map in newldapgid:
        newldapf.write("idmap: {}, nodemap: {}\n".format(map['idmap'], map['nodemap']))

## write mismatched gids file
output_mismatchgids = adldap.config['NODEMAP']['directory']+'/archive/'+timestamp+'.'+adldap.config['NODEMAP']['mismatchgids']
with open(output_mismatchgids, 'w', newline='\n') as mismatchf:
    for map in mismatchgid:
        mismatchf.write("idmap: {}, nodemap: {}\n".format(map['idmap'], map['nodemap']))

###### write combined group map
output_combined_groups = adldap.config['NODEMAP']['directory']+'/'+timestamp+'.group.combined'
with open(output_combined_groups,'w', newline='') as gcombmapfile:
    fieldnames = ['adname','adgid','ldapname','ldapgid']
    writer = csv.DictWriter(gcombmapfile, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()
    writer.writerows(combinedGroupNodemap)

group_combinedmap_current = adldap.config['NODEMAP']['directory']+'/'+adldap.config['NODEMAP']['groupcombined']

adldap.link_new_and_remove(group_combinedmap_current, output_combined_groups, adldap.config['NODEMAP']['directory'])

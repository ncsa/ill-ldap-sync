#!/taiga/admin/iccp/nodemap/bin/hostvenv
from ldap3 import Server, Connection, ALL, Tls, extend, BASE
from datetime import datetime
import ssl
import csv
from adldap import Adldap
from ncsaldapapi import IccpNcsaLdap
import os
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# create Adldap insance
adldap = Adldap(config_file="/taiga/admin/iccp/nodemap/conf/ug.config")

# create ldapapi instance
ldapapi = IccpNcsaLdap(config_file="/taiga/admin/iccp/nodemap/test/bin/config")

# load group nodemap
group_nodemap = adldap.get_nodemap_group()

# load ldap group info
ldap_groups = adldap.get_ldap_groups()

# load ldap users
ldap_users = adldap.get_ldap_users()

# load user nodemap
user_nodemap = adldap.get_nodemap_user()

# timestamp for output
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

# output groups file
output_groups = adldap.config['LDAP']['directory']+'/'+timestamp+'.groups.flat'
output_groups_ad = adldap.config['LDAP']['directory']+'/'+timestamp+'.groups_ad.flat'


with open(output_groups,'w', newline='\n') as gfile, open(output_groups_ad, 'w',newline='\n') as gfile_ad:
    # get all users in each group(including nested groups)
    #     then get their ldap user
    #     verify users in groups and if anyone needs to be added or removed
    for group in group_nodemap:
        grpAccts = adldap.get_ad_group_samaccounts(group['adname'])
        mapGrpName = adldap.config['LDAP']['group_prefix'] + group['adname']
        #ldapGrpAccts = [lgroup for lgroup in ldap_groups if lgroup['gr_name'] == group['adname']]
        ldapGrpAccts = adldap.get_ldap_group_with_uids(mapGrpName)
        grpAccts_ldap = []
        grpAccts_ad = []
        adduser = []
        remuser = []
        
        # for ad users in this group get mapped ldap user and add to group accounts or add to the to be added list
        for user in grpAccts:
            for thisuser in user_nodemap:
                if thisuser.get('aduid') == user:
                    ldapuser = thisuser['ldapuid']
                    grpAccts_ldap.append(ldapuser)
                    grpAccts_ad.append(user)
                    if ldapGrpAccts:
                        if not ldapuser in ldapGrpAccts['gr_users']:
                            adduser.append(ldapuser)
    
        # for ldap users in this group check if they still exist on the AD side
        if ldapGrpAccts:
            for luser in ldapGrpAccts['gr_users']:
                testnodemap = [thisuser for thisuser in user_nodemap if thisuser['ldapuid'] == luser]
                if not testnodemap:
                    remuser.append(luser)
                elif not [aduser for aduser in grpAccts if aduser == testnodemap[0]['aduid']]:
                    remuser.append(luser)

        for auser in adduser:
            result = ldapapi.add_to_campus_cluster_groups(group['adname'],auser)
            if result:
                eprint("Added user: "+ auser + " to group: "+ mapGrpName)
            else:
                eprint("ERROR adding user: "+ auser + " to group: "+ mapGrpName)

        for ruser in remuser:
            result = ldapapi.delete_from_campus_cluster_groups(mapGrpName,ruser)
            if result:
                eprint("Removed user: "+ ruser + " from group: "+ mapGrpName)
            else:
                eprint("ERROR Removing user: "+ ruser + " from group: "+ mapGrpName)
    
        grpAcctsString = ','.join(str(user) for user in sorted(grpAccts_ldap))
        grpAcctsString_ad = ','.join(str(user) for user in sorted(grpAccts_ad))
        grpGID = group['ldapgid']
        grpGID_ad = group['adgid']
        # print group file line
        gfile.write("{}:x:{}:{}\n".format(group['ldapname'],grpGID,grpAcctsString))
        gfile_ad.write("{}:x:{}:{}\n".format(group['adname'],grpGID_ad,grpAcctsString_ad))

        ##print("ADD - {}".format(','.join(str(user) for user in adduser)))
        ##print("REM - {}".format(','.join(str(user) for user in remuser)))

ldap_groups_sym = adldap.config['LDAP']['directory']+'/'+adldap.config['LDAP']['group_file']
ldap_groups_target = os.readlink(ldap_groups_sym)
ldap_groups_target_full = adldap.config['LDAP']['directory']+'/'+ldap_groups_target
ldap_groups_target_rename = adldap.config['LDAP']['directory']+'/archive/'+os.path.basename(ldap_groups_target)

# symlink new file and move old to archive
os.unlink(ldap_groups_sym)
os.symlink(os.path.basename(output_groups),ldap_groups_sym)
os.rename(ldap_groups_target_full, ldap_groups_target_rename)

new_group_ad_file_sym = adldap.config['LDAP']['directory']+'/'+adldap.config['LDAP']['group_ad_file']
adldap.archive_and_link_new(new_group_ad_file_sym,output_groups_ad,adldap.config['LDAP']['directory'])

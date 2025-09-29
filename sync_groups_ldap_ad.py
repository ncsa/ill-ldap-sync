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

# load ldap2ad group list
ldap_sync_group_map = adldap.get_ldap_sync_group_map()

# load AD group nodemap
group_nodemap = adldap.get_nodemap_group()

# timestamp for output
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

all_groups_users = []

for group in ldap_sync_group_map:
    ldapGrpAccts = adldap.get_ldap_group_members_full(group['ldapname'])
    adGrpAccts = adldap.get_ad_nested_group_members(group['adname'])
    adGrp = adldap.get_ad_group_by_dispname(group['adname'])

    mailDomain = adldap.config['LDAP']['mail_domain']

    for ldapGrpMember in [luser for luser in ldapGrpAccts if luser[0]['attributes']['mail'][0].endswith(mailDomain)]:
        adUser = [auser for auser in adGrpAccts if auser['attributes']['mail'] == ldapGrpMember[0]['attributes']['mail'][0]]
        all_groups_users.append(adUser)
        if not adUser: # user is not in the ad group yet
            newUser = adldap.get_ad_user_by_mail(ldapGrpMember[0]['attributes']['mail'][0])
            #print("Add {} to {}\n".format(newUser[0]['dn'],group['adname']))
            if newUser:
                add_user = adldap.add_ad_user_to_group(newUser[0]['dn'],adGrp['attributes']['distinguishedName'])
                if add_user:
                    print("{} {}: success\n".format(newUser[0]['dn'],group['adname']))
                else:
                    print("{} {}: error\n".format(newUser[0]['dn'],group['adname']))
    for adGrpMember in adGrpAccts:
        ldapUser = [luser for luser in ldapGrpAccts if luser[0]['attributes']['mail'][0] == adGrpMember['attributes']['mail']]

        if not ldapUser: # user is no longer in ldap group, remove from AD group
            print("remove {} from {}\n".format(adGrpMember['attributes']['distinguishedName'],group['adname']))
            rem_user = adldap.remove_ad_user_from_group(adGrpMember['attributes']['distinguishedName'],adGrp['attributes']['distinguishedName'])
            if rem_user:
                print("{} {}: removed\n".format(adGrpMember['attributes']['distinguishedName'],adGrp['attributes']['distinguishedName']))
            else:
                print("{} {}: removal error\n".format(adGrpMember['attributes']['distinguishedName'],adGrp['attributes']['distinguishedName']))

combined_group_members = adldap.get_ad_nested_group_members(adldap.config['LDAP_SYNC']['combined_sync_users_group'])
for member in combined_group_members:
    # is the group member in the list of all users
    tUser = [auser for auser in all_groups_users if auser['attributes']['distinguishedName'] == member['attributes']['distinguishedName']]
    if not tUser: #user is not in the list of all users, remove from combined_ldap_users
        rem_user = adldap.remove_ad_user_from_group(member['attributes']['distinguishedName'],adldap.config['LDAP_SYNC']['combined_sync_users_groupdn'])
    
for user in all_groups_users:
    # is the user in the group?
    aMember = [auser for auser in combined_group_members if auser['attributes']['distinguishedName'] == user['attributes']['distinguishedName']]
    if not aMember: # user is not already in the group.
        add_user = adldap.add_ad_user_to_group(user[0]['attributes']['distinguishedName'],adldap.config['LDAP_SYNC']['combined_sync_users_groupdn'])


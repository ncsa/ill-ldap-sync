#!/taiga/admin/iccp/nodemap/bin/hostvenv
from ldap3 import Server, Connection, ALL, Tls, extend
from datetime import datetime
import ssl
import csv
from adldap import Adldap
from ncsaldapapi import IccpNcsaLdap
import shutil
import sys
import logging

def eprint(*args, **kwargs):
            print(*args, file=sys.stderr, **kwargs)

debug = 0

# create Adldap insance
adldap = Adldap(config_file="/taiga/admin/iccp/nodemap/conf/ug.config")

# create ldapapi instance
ldapapi = IccpNcsaLdap(config_file="/taiga/admin/iccp/nodemap/test/bin/config")

# setup loggin
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=adldap.config['NODEMAP']['logfile'])

# get ad groups being mapped
groupNodemap = adldap.get_nodemap_group()

##### AD query - get users from all groups in nodemap 
adUsers = []
for group in groupNodemap:
    these_users = adldap.get_ad_nested_group_members(group['adname'])
    for user in these_users:
        alreadyinfull = [entry for entry in adUsers if entry['attributes']['sAMAccountName'] == user['attributes']['sAMAccountName']]
        if not alreadyinfull:
            adUsers.append(user)

##### Get Nodemap
userNodemap = adldap.get_nodemap_user()

#####LDAP Query
ldapUsers = adldap.get_ldap_users()

#####LDAP mapped
mappedUsers = adldap.get_ldap_mapped_extra()

mappedUsers.sort(key=lambda x: x['uidnum'])

timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

newmap = []
nomap = []
nomail = []
for aduser in adUsers:
    if aduser['attributes']['sAMAccountName'].startswith("ccp-"): continue
    aduid = aduser['attributes']['sAMAccountName'] if 'sAMAccountName' in aduser['attributes'] else None
    admail = aduser['attributes']['mail'] if 'mail' in aduser['attributes'] else None
    # is there a matching uid in ldap?
    thisuser={}
    tnomail = {}
    tnomap = {}
    # check if the user is already in the nodemap
    testnodemap = [entry for entry in userNodemap if entry['aduid'] == aduid] 
    if testnodemap:
        if debug:
            # user is in the nodemap check
            if testldap:
                # aduid matches ldap entry
                eprint("aduid: "+aduid+" is mapped directly in ldap: "+testnodemap[0]['ldapuid'])
            if testmap:
                # aduid matches mappedUsers
                eprint(mappedaduid+" mapped user")

    else: # not already in nodemap    
        testldap = [entry for entry in ldapUsers if entry['attributes']['uid'][0] == aduid]
        #mappedaduid = aduid.replace("-","")
        #mappedaduid = trim_string(mappedaduid, 17)
        #mappedaduid='ill'+aduid
        prefixuid = aduid.replace("-","")
        if len(prefixuid) > 17:
            prefixuid = prefixuid[:17]
        prefixuid='ill'+prefixuid
        mappedaduid='icc-'+aduid
        testldapprefix = [entry for entry in ldapUsers if entry['attributes']['uid'][0] == prefixuid]
        testmap = [entry for entry in mappedUsers if entry['uid'] == mappedaduid]
        if testldap:
            # does mail match as well as uid?
            ldapmail = testldap[0]['attributes']['mail'][0]
            if ldapmail == admail:
                thisuser={
                    'aduid': aduid,
                    'aduidnum': aduser['attributes']['uidNumber'],
                    'ldapuid': testldap[0]['attributes']['uid'][0],
                    'ldapuidnum': testldap[0]['attributes']['uidNumber']
                }
            else: #uid matches but mail does not
                #check prefixed uid 
                if testldapprefix: # prefixed ldap user exists
                    if testldapprefix[0]['attributes']['mail'][0] == admail: #prefixed uid mail in ldap matches
                        thisuser={
                            'aduid': aduid,
                            'aduidnum': aduser['attributes']['uidNumber'],
                            'ldapuid': testldapprefix[0]['attributes']['uid'][0],
                            'ldapuidnum': testldapprefix[0]['attributes']['uidNumber']
                        }
                    else:
                        tnomail={
                            'aduid': aduid,
                            'aduidnum': aduser['attributes']['uidNumber'],
                            'admail': admail,
                            'ldapuid': testldapprefix[0]['attributes']['uid'][0],
                            'ldapuidnum': testldapprefix[0]['attributes']['uidNumber'],
                            'ldapmail': testldapprefix[0]['attributes']['mail'][0]
                        }
                else:
                    testmail = [entry for entry in ldapUsers if entry['attributes']['mail'][0] == admail]
                    # matching uid (non-matching mail) and no prefixed uid, so check mail instead
                    if testmail:
                        thisuser={
                            'aduid': aduid,
                            'aduidnum': aduser['attributes']['uidNumber'],
                            'ldapuid': testmail[0]['attributes']['uid'][0],
                            'ldapuidnum': testmail[0]['attributes']['uidNumber']
                        }
                    else: # no matching prefixed uid or mail create new LDAP user
                        tnomap={
                            'aduid': aduid,
                            'aduidnum': aduser['attributes']['uidNumber'],
                            'admail': admail
                        }
                        # no matching mail, create new ldap user with prefixed uid since matching uid with non-matched mail exists
                        # add user in ldap
                        data = { "login" : prefixuid,
                                 "email" : admail,
                                 "first_name": aduser['attributes']['uiucEduFirstName'],
                                 "last_name": aduser['attributes']['uiucEduLastName']
                               }
                        retry = 0
                        maxret = 2
                        while retry < maxret:
                            result = ldapapi.create_campus_cluster_accounts(data["login"],data["email"],data["first_name"],data["last_name"])
                            logger.info(f"ldapapi.create_campus_cluster_accounts {data}")
                        
                            if result:#success adding to ldap
                                thisuser = {
                                    'aduid': aduid,
                                    'aduidnum': aduser['attributes']['uidNumber'],
                                    'ldapuid': data["login"],
                                    'ldapuidnum': result
                                }
                                break
                            else:
                                if data['login'].startswith("ill"): #already prefixed stop here
                                    break
                                else:
                                    data['login'] = "ill" + data['login']
                                    retry += 1
                        ## end while add user in ldap
        # check mapped ldap entries
        elif testmap:
            thisuser={
                'aduid': aduid,
                'aduidnum': aduser['attributes']['uidNumber'],
                'ldapuid':  testmap[0]['uid'],
                'ldapuidnum': testmap[0]['uidnum']
            }
        elif testldapprefix:
            if testldapprefix[0]['attributes']['mail'][0] == admail: #prefixed uid mail in ldap matches
                thisuser={
                    'aduid': aduid,
                    'aduidnum': aduser['attributes']['uidNumber'],
                    'ldapuid': testldapprefix[0]['attributes']['uid'][0],
                    'ldapuidnum': testldapprefix[0]['attributes']['uidNumber']
                }
            else: # prefixed uid exists but has non-matching mail.. send to no mail log
                tnomail={
                    'aduid': aduid,
                    'aduidnum': aduser['attributes']['uidNumber'],
                    'admail': admail,
                    'ldapuid': testldapprefix[0]['attributes']['uid'][0],
                    'ldapuidnum': testldapprefix[0]['attributes']['uidNumber'],
                    'ldapmail': testldapprefix[0]['attributes']['mail'][0]
                }
        else: #no matching uid or prefixed uid, check mail 
            testmail = [entry for entry in ldapUsers if entry['attributes']['mail'][0] == admail]
            # no matching uid, so check mail instead
            if testmail:
                thisuser={
                    'aduid': aduid,
                    'aduidnum': aduser['attributes']['uidNumber'],
                    'ldapuid': testmail[0]['attributes']['uid'][0],
                    'ldapuidnum': testmail[0]['attributes']['uidNumber']
                }
            else: # no matching uid or mail create new LDAP user
                tnomap={
                    'aduid': aduid,
                    'aduidnum': aduser['attributes']['uidNumber'],
                    'admail': admail
                }
                # add user in ldap
                data = { "login" : aduid,
                         "email" : admail,
                         "first_name": aduser['attributes']['uiucEduFirstName'],
                         "last_name": aduser['attributes']['uiucEduLastName']
                       }
                retry = 0
                maxret = 2
                while retry < maxret:
                    result = ldapapi.create_campus_cluster_accounts( 
                        data["login"],
                        data["email"],
                        data["first_name"],
                        data["last_name"])
                    logger.info(f"ldapapi.create_campus_cluster_accounts {data}")

                    if result:#success adding to ldap
                        # user added tp ldap successfully so add to nodemap
                        thisuser = {
                            'aduid': aduid,
                            'aduidnum': aduser['attributes']['uidNumber'],
                            'ldapuid': data['login'],
                            'ldapuidnum': result
                        }
                        break
                    else:
                        if data['login'].startswith("ill"): #already prefixed stop here
                            break
                        else:
                            data['login'] = "ill" + data['login']
                            retry += 1
                ## end while add user in ldap

    if thisuser:
        newmap.append(thisuser)

    if tnomail:
        nomail.append(tnomail)

    if tnomap:
        nomap.append(tnomap)

# add newly mapped users to the nodemap
userNodemap.extend(newmap)

# write any nomap users to nomap file 
with open(adldap.config['NODEMAP']['directory']+'/archive/'+timestamp+'.nomap.users.csv','w', newline='\n') as csvfile:
    fieldnames = ['aduid', 'aduidnum', 'admail']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()
    writer.writerows(nomap)

# write any users that didn't have matching email to nomail file
with open(adldap.config['NODEMAP']['directory']+'/archive/'+timestamp+'.nomail.users.csv','w', newline='\n') as csvfile:
    fieldnames = ['aduid', 'aduidnum', 'admail', 'ldapuid', 'ldapuidnum', 'ldapmail']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()
    writer.writerows(nomail)

# sort nodemap list by ad uid number
userNodemap.sort(key=lambda x: int(x['aduidnum']))

# ouput nodemap csv file and link as current
output_user_nodemap = adldap.config['NODEMAP']['directory']+'/'+timestamp+'.nodemap.users.csv'
user_nodemap_current = adldap.config['NODEMAP']['directory']+'/'+adldap.config['NODEMAP']['user']

# write user nodemap
with open(output_user_nodemap,'w', newline='') as csvfile:
    fieldnames = ['aduid', 'aduidnum', 'ldapuid', 'ldapuidnum']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()
    writer.writerows(userNodemap)

adldap.archive_and_link_new(user_nodemap_current, output_user_nodemap, adldap.config['NODEMAP']['directory'])

# output new passwd/shadow files for pwgr sync
output_passwd_extras=adldap.config['NODEMAP']['directory']+'/'+timestamp+'.passwd.extras'
output_shadow_extras=adldap.config['NODEMAP']['directory']+'/'+timestamp+'.shadow.extras'
users_ldap_new=adldap.config['NODEMAP']['directory']+'/'+timestamp+'.user.ldap'
users_ldap_current=adldap.config['LDAP']['directory']+'/'+adldap.config['LDAP']['user_file']
passwd_extras_current=adldap.config['NODEMAP']['directory']+'/'+adldap.config['NODEMAP']['passwd']
shadow_extras_current=adldap.config['NODEMAP']['directory']+'/'+adldap.config['NODEMAP']['shadow']

# write passwd and shadow
with open(output_passwd_extras, 'w', newline='\n') as passwdfile, open(output_shadow_extras, 'w', newline='\n') as shadowfile:
    for u in mappedUsers:
        passwdfile.write("{}:x:{}:{}:{}:{}:{}\n".format(u['uid'],u['uidnum'],u['gidnum'],u['gecos'],u['home'],u['shell']))
        shadowfile.write("{}:!!:19464::::::\n".format(u['uid']))

# move old passwd/shadow to archive and link new
shutil.copy(output_passwd_extras, users_ldap_new)
adldap.archive_and_link_new(users_ldap_current, users_ldap_new, adldap.config['LDAP']['directory'])
adldap.archive_and_link_new(passwd_extras_current, output_passwd_extras, adldap.config['NODEMAP']['directory'])
adldap.archive_and_link_new(shadow_extras_current, output_shadow_extras, adldap.config['NODEMAP']['directory'])

### Determine what needs to be updated in the idmap
######reload nodemap from file
userNodemap = adldap.get_nodemap_user()

###### get idmap
userIdmap = adldap.get_idmap_user()

##### Check for user in nodemap not idmap
newldapuid = []
mismatchuid = []
newidmap = []
for user in userNodemap:
    uids = [(x,y) for (x,y) in userIdmap if (x,y) == (user['aduidnum'],user['ldapuidnum'])]
    auid = [(x,y) for (x,y) in userIdmap if x == user['aduidnum']]
    nuid = [(x,y) for (x,y) in userIdmap if y == user['ldapuidnum']]
    if not uids:
        if auid:
            if not nuid:
                ###print("NEWLDAPUSER: idmap: {} nodemap:{}".format(auid, ','.join(user.values())))
                newldapuid.append({'idmap': auid[0], 'nodemap': ','.join(user.values())})
            else:
                print("ad and ldap: {},{} nodemap: {}".format(auid,nuid,','.join(user.values())))
                
        else:
            if not nuid:
                ###print("new idmap: {}:{}".format(user['aduidnum'],user['ldapuidnum']))
                newidmap.append("{}:{}".format(user['aduidnum'],user['ldapuidnum']))
            else:
                ###print("ADUIDNOMATCH: idmap: {} nodemap: {}".format(nuid, ','.join(user.values())))
                mismatchuid.append({
                    'idmap': nuid[0],
                    'nodemap': ','.join(user.values())
                })
###### write files for for idmap info
new_uidmap_link = adldap.config['LUSTRE']['directory']+'/'+adldap.config['LUSTRE']['new_uids']
output_new_uidmap = adldap.config['LUSTRE']['directory']+'/'+timestamp+'.'+adldap.config['LUSTRE']['new_uids']
with open(output_new_uidmap, 'w', newline='\n') as nuidmap:
    for u in newidmap:
        nuidmap.write("{}\n".format(u))
adldap.archive_and_link_new(new_uidmap_link,output_new_uidmap,adldap.config['LUSTRE']['directory'])

output_newldap_uids = adldap.config['NODEMAP']['directory']+'/archive/'+timestamp+'.'+adldap.config['NODEMAP']['maptoldap']
with open(output_newldap_uids, 'w', newline='\n') as newldapf:
    for map in newldapuid:
        newldapf.write("idmap: {}, nodemap: {}\n".format(map['idmap'], map['nodemap']))

output_mismatchuids = adldap.config['NODEMAP']['directory']+'/archive/'+timestamp+'.'+adldap.config['NODEMAP']['mismatchuids']
with open(output_mismatchuids, 'w', newline='\n') as mismatchf:
    for map in mismatchuid:
        mismatchf.write("idmap: {}, nodemap: {}\n".format(map['idmap'], map['nodemap']))
    

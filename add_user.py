#!/taiga/admin/iccp/nodemap/bin/hostvenv
from adldap import Adldap
import csv
import sys

if len(sys.argv) < 2:
    print("Usage: add_group <group> | \"<group1, group2,...>\"")
    sys.exit(1)

input_users = list(map(str.strip, sys.argv[1].split(",")))

# create Adldap insance
adldap = Adldap(config_file="/taiga/admin/iccp/nodemap/conf/config")

# Extra Group DN
extraUsersGrpDN = adldap.config['AD']['add_users_group']

# Get current group members
extraUsers = adldap.get_ad_nested_group_members('icc-storage-adldap-extra')

user = adldap.get_ad_user(input_users[0])
print(user[0]['dn'])

# get DN's for all input users
inputDNs = []
notfound = []
for inuser in input_users:
    thisuser = adldap.get_ad_user(inuser)
    if thisuser:
        inputDNs.append(thisuser[0]['dn'])
    else:
        notfound.append(inuser)

print("Adding the following users:\n    {}".format('\n'.join(inputDNs)))
if notfound:
    print("The following users were not found:\n    {}".format('\n'.join(notfound)))

for user in inputDNs:
    tuser = adldap.add_ad_user_to_group(user,extraUsersGrpDN)
    if tuser:
        print("{}: success\n".format(user))
    else:
        print ("{}: ERROR\n".format(user))

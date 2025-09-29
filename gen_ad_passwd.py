#!/taiga/admin/iccp/nodemap/bin/hostvenv
from adldap import Adldap

# create Adldap insance
adldap = Adldap(config_file="/taiga/admin/iccp/nodemap/conf/config")

##### AD query
adUsers = adldap.get_ad_nested_group_members('CampusClusterUsers')

#print(adUsers[0])

adUsers.sort(key=lambda x: x['attributes']['uidNumber'])
for user in adUsers:
    print('{}:{}:{}:{}:{}:{}:{}'.format(user['attributes']['samaccountname'],'x',user['attributes']['uidNumber'],'51000',user['attributes']['displayname'],'/','/sbin/nologin'))

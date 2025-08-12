# ill-ldap-sync
Synchronize Active Directory users and groups(with uidNumber and gidNumber mappings)  into LDAP. 

Lustre nodemap provides an ID mapping option for uid/gid. This allows Lustre clients with possibly different identity domains from the mounted Lustre fs. 

## ncsaadldap
Provides functions to query Active Directory and LDAP in order to discover and generate user/group mappings for Lustre idmap.

## ncsaldapapi
Provides functions to interact with NCSA LDAP API. Enables creating users and groups (and managing groups) required for mapping.


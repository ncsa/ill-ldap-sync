# ill-ldap-sync
Synchronize Active Directory users and groups(with uidNumber and gidNumber mappings)  into LDAP. 

Lustre nodemap provides an ID mapping option for uid/gid. This allows Lustre clients with possibly different identity domains from the mounted Lustre fs. 

## adldap
Provides functions to query Active Directory and LDAP in order to discover and generate user/group mappings for Lustre idmap.

## ncsaldapapi
Provides functions to interact with NCSA LDAP API. Enables creating users and groups (and managing groups) required for mapping.

## ncsaadldap.py
* Module with too many helper functions for accessing both AD and LDAP

## Nodemap generation
* There are 2 nodemaps that map between Campus Active Directory and NCSA LDAP
  * user nodemap - for AD uid to LDAP uid mapping
  * group nodemap - for AD gid to LDAP gid mapping
* User Nodemap
  * user_nodemap.py
    * compares AD users to current nodemap as well as LDAP users
       * maps AD user to NCSA LDAP user
       * creates new NCSA LDAP user if needed
       * checks newnodemap against current Lustre idmap uids
         * creates file with new mappings to be added to Lustre: uid.idmap.new

* Group Nodemap
  * sync_groups.py
    * compares AD groups to current nodmeap as well as LDAP groups
      * maps AD group to NCSA LDAP group
      * creates new NCSA LDAP group if needed
      * checks new nodemap against current Lustre idmap gids
        * creates file with new mappings to be added to Lustre: gid.idmap.new

## Adding Users and Groups to nodemap(s)
* add_user.py - add lone user(s) to the nodemap
  * takes an argument of user sAMAccountName's (netid) can be one or multiple (comma separated)
  * adds user to special AD group that is used for generating the nodemap

* add_group.py - add group to the nodemap
  * takes an argument of a group displayName. Can be one or multiple (comma separated)
  * adds user to the group list to be mapped


## TODO
* example config file

#!/usr/bin/env python3
from ldap3 import Server, Connection, ALL, Tls, extend, BASE, ALL_ATTRIBUTES, MODIFY_REPLACE
import ssl
import configparser
import csv
import sys
import os

def eprint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

class Adldap:
    def __init__( self, config_file="config" ):

        self.config_file = config_file

        # Load the config from a configuration file
        self.config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
        self.config.sections()
        self.config.read( self.config_file )
        ##print(self.config['AD']['user'])
        # Setup AD connection
        self.tls_configuration = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1)
        self.adserv = Server(self.config['AD']['server'], use_ssl=True, tls=self.tls_configuration)
        self.adconn = Connection(self.adserv, self.config['AD']['user'], self.config['AD']['password'], auto_bind=True, auto_referrals=False)
        
        # Setup LDAP connection
        self.ldapserv = Server(self.config['LDAP']['server'], use_ssl=True, port=636)
        self.ldapconn = Connection(self.ldapserv, self.config['LDAP']['user'], self.config['LDAP']['password'], auto_bind=True)

    # get user nodemap
    def get_nodemap_user(self):
        with open(self.config['NODEMAP']['directory']+'/'+self.config['NODEMAP']['user'], 'r') as f:
            dict_reader = csv.DictReader(f)
            thisnodemap = list(dict_reader)
            genmap = []
            for entry in thisnodemap:
                thisdict = dict(entry)
                genmap.append(thisdict)

            return genmap

    # get group nodemap
    def get_nodemap_group(self):
        with open(self.config['NODEMAP']['directory']+'/'+self.config['NODEMAP']['group'], 'r') as f:
            dict_reader = csv.DictReader(f)
            thisnodemap = list(dict_reader)
            genmap = []
            for entry in thisnodemap:
                thisdict = dict(entry)
                genmap.append(thisdict)

            return genmap

    # get ldap group sync map
    def get_ldap_sync_group_map(self):
        with open(self.config['LDAP_SYNC']['directory']+'/'+self.config['LDAP_SYNC']['map'], 'r') as f:
            dict_reader = csv.DictReader(f)
            thissyncmap = list(dict_reader)
            genmap = []
            for entry in thissyncmap:
                thisdict = dict(entry)
                genmap.append(thisdict)

            return genmap

    # get ldap group sync next gid
    def get_ldap_group_sync_next_gid(self):
        # get next gid group
        next_gid_dn = self.config['LDAP_SYNC']['next_ad_gid_dn']
        adgrp = list(self.adconn.extend.standard.paged_search(
            search_base = next_gid_dn,
            search_filter = '(objectClass=group)',
            attributes = ALL_ATTRIBUTES,
            paged_size = 999))
        nextgid = adgrp[0]['attributes']['gidNumber']
        return nextgid

    # update ldap group sync next gid
    def update_ldap_group_sync_next_gid(self):
        # adjust next gid
        current_gid = self.get_ldap_group_sync_next_gid()
        next_gid = current_gid + 1
        updates = { 'gidNumber': [(MODIFY_REPLACE, [next_gid])]}
        returned = self.adconn.modify(self.config['LDAP_SYNC']['next_ad_gid_dn'], updates)

        return returned
        
    # get user idmap
    def get_idmap_user(self):
        with open(self.config['LUSTRE']['directory']+'/'+self.config['LUSTRE']['user_idmap'], 'r') as f:
            csv_reader = csv.reader(f)
            #idmap = [tuple[entry] for entry in csv_reader]
            uidmap = list(map(tuple, csv_reader))

        return uidmap

    # get group idmap
    def get_idmap_group(self):
        with open(self.config['LUSTRE']['directory']+'/'+self.config['LUSTRE']['group_idmap'], 'r') as f:
            csv_reader = csv.reader(f)
            #idmap = [tuple[entry] for entry in csv_reader]
            gidmap = list(map(tuple, csv_reader))

        return gidmap        

    # get user nodemap not in idmap
    def get_user_nodemap_not_in_idmap(self):
        uNodemap = self.get_nodemap_user()
        uIdmap = self.get_idmap_user()
        retMissingIdmap = []

        for user in uNodemap:
            if not (user['aduidnum'],user['ldapidnum']) in uIdmap:
                thisEntry = user['aduidnum']+":"+user['ldapuidnum']
                retMissingIdmap.append(thisEntry)

        return retMissingIdmap

    # get group nodemap not in idmap
    def get_group_nodemap_not_in_idmap(self):
        return

    # get ldap mapped groups
    def get_ldap_mapped_groups(self):
        group_entries = []
        with open(self.config['LDAP']['directory']+'/'+self.config['LDAP']['group_file'], 'r') as g:
            for line in g:
                # skip comments and empty lines
                if line.startswith("#") or line.strip() == "":
                    continue

                # split out the : separated fields
                fields = line.strip().split(':')

                if len(fields) == 4:
                    gr_name,gr_passwd,gr_id,gr_users = fields
                    grp_entry = { 'gr_name' : gr_name,
                                  'gr_passwd' : gr_passwd,
                                  'gr_id' : gr_id,
                                  'gr_users' : gr_users.split(',') if gr_users else [] }
                    group_entries.append(grp_entry)
                
        return group_entries

    # get ldap mapped groups (real LDAP)
    def get_ldap_mapped_groups2(self):
        group_entries = []

    # get ldap mapped extra users
    def get_ldap_mapped_extra(self):
        u_entries = []
        with open(self.config['LDAP']['directory']+'/'+self.config['LDAP']['user_file'], 'r') as u:
            for line in u:
                # skip comments and empty lines
                if line.startswith("#") or line.strip() == "":
                    continue

                # split out the fields
                fields = line.strip().split(':')

                if len(fields) == 7:
                    uid,passwd,uidnum,gidnum,gecos,home,shell = fields
                    u_entry = { 'uid': uid,
                                'passwd' : passwd,
                                'uidnum' : uidnum,
                                'gidnum' : gidnum,
                                'gecos'  : gecos,
                                'home'   : home,
                                'shell'  : shell }
                    u_entries.append(u_entry)

        return u_entries

    # write linux group file
    def format_linux_group_file(self,groups):
        for group in groups:
            return 

    # add ad user to ad group
    def add_ad_user_to_group(self, userdn, groupdn,):
        returned = self.adconn.extend.microsoft.add_members_to_groups(userdn, groupdn)

        return returned

    # remove ad user from ad group
    def remove_ad_user_from_group(self,userdn, groupdn):
        returned = self.adconn.extend.microsoft.remove_members_from_groups(userdn,groupdn)

        return returned

    # add ad group 
    def add_ad_group(self, groupdn, groupname, gidnum):
        group_security = -2147483646
        group_attributes = {
            'objectClass': ['top', 'group'],
            'groupType': group_security,
            'displayName': groupname,
            'sAMAccountName': groupname,
            'gidNumber': gidnum
        }
        returned = self.adconn.add(groupdn, attributes=group_attributes)
        print(returned)
        return returned
            
    # get ad users
    def get_ad_users(self):
        adusers = list(self.adconn.extend.standard.paged_search(
            search_base = self.config['AD']['user_search_base'],
            search_filter = self.config['AD']['user_search_filter'],
            search_scope = self.config['AD']['user_search_scope'],
            attributes = self.config.getlist('AD', 'user_search_attributes'),
            paged_size = 999))
        return adusers

    # get ad users
    def get_ad_users2(self):
        sbases = []
        sbases.append('OU=People,DC=ad,DC=uillinois,DC=edu')
        sbases.append('OU=Urbana,DC=ad,DC=uillinois,DC=edu')
        all_users = []
        for thisbase in sbases:
            adusers = list(self.adconn.extend.standard.paged_search(
                search_base = thisbase,
                search_filter = self.config['AD']['user_search_filter'],
                search_scope = self.config['AD']['user_search_scope'],
                attributes = self.config.getlist('AD', 'user_search_attributes'),
                paged_size = 999))
            all_users.extend(adusers)
        return all_users

    # get ad user
    def get_ad_user(self,samaccount):
        aduser = list(self.adconn.extend.standard.paged_search(
            search_base = self.config['AD']['user_search_base'],
            search_filter = '(&(objectClass=person)(sAMAccountname='+samaccount+'))',
            search_scope = self.config['AD']['group_search_scope'],
            attributes = self.config.getlist('AD', 'user_search_attributes'),
            paged_size = 999))

        if not aduser:
            aduser2 = list(self.adconn.extend.standard.paged_search(
                search_base = 'OU=Urbana,DC=ad,DC=uillinois,DC=edu',
                search_filter = '(&(objectClass=person)(sAMAccountname='+samaccount+'))',
                search_scope = self.config['AD']['group_search_scope'],
                attributes = self.config.getlist('AD', 'user_search_attributes'),
                paged_size = 999))
            if not aduser2: 
                aduser = []
            else:
                aduser = aduser2
        
        return aduser

    # get ad user by mail
    def get_ad_user_by_mail(self,mail):
        aduser = list(self.adconn.extend.standard.paged_search(
            search_base = self.config['AD']['user_search_base'],
            search_filter = '(&(objectClass=person)(mail='+mail+'))',
            search_scope = self.config['AD']['user_search_scope'],
            attributes = self.config.getlist('AD', 'user_search_attributes'),
            paged_size = 999))
        if not aduser:
            aduser = []
        
        return aduser

    
    # get ad groups
    def get_ad_groups(self):
        adgroups = list(self.adconn.extend.standard.paged_search(
            search_base = self.config['AD']['group_search_base'],
            search_filter = self.config['AD']['group_search_filter'],
            search_scope = self.config['AD']['group_search_scope'],
            attributes = self.config.getlist('AD', 'group_search_attributes'),
            paged_size = 999))
        return adgroups
        
    # get ldap users
    def get_ldap_users(self):
        ldapusers = list(self.ldapconn.extend.standard.paged_search(
            search_base = self.config['LDAP']['user_search_base'],
            search_filter = self.config['LDAP']['user_search_filter'],
            search_scope = self.config['LDAP']['user_search_scope'],
            attributes = self.config.getlist('LDAP', 'user_search_attributes'), 
            paged_size=999))
        
        return ldapusers

    # get ldap group
    def get_ldap_group(self,group):
        ldapgroup = list(self.ldapconn.extend.standard.paged_search(
            search_base = self.config['LDAP']['group_search_base'],
            search_filter = '(&(objectClass=posixGroup)(cn=' + group + '))',
            search_scope = self.config['LDAP']['group_search_scope'],
            attributes = self.config.getlist('LDAP', 'group_search_attributes'),
            paged_size = 999))
        return ldapgroup

    # get ldap groups
    def get_ldap_groups(self):
        ldapgroups = list(self.ldapconn.extend.standard.paged_search(
            search_base = self.config['LDAP']['group_search_base'],
            search_filter = self.config['LDAP']['group_search_filter'],
            search_scope = self.config['LDAP']['group_search_scope'],
            attributes = self.config.getlist('LDAP', 'group_search_attributes'),
            paged_size = 999))
        return ldapgroups
    
    # get_ldap_group_members
    def get_ldap_group_members(self,group):
        ldapgrpmembers = list(self.ldapconn.extend.standard.paged_search(
            search_base = self.config['LDAP']['group_search_base'],
            search_filter = '(&(objectClass=posixGroup)(cn=' + group + '))',
            search_scope = self.config['LDAP']['group_search_scope'],
            attributes = ['uniqueMember'],
            paged_size = 999))
        ldapgrpmembersdn = ldapgrpmembers[0]['attributes']['uniqueMember']
        return ldapgrpmembersdn

    # get_ldap_group_with_uids
    def get_ldap_group_with_uids(self,group):
        ldapgroup = list(self.ldapconn.extend.standard.paged_search(
            search_base = self.config['LDAP']['group_search_base'],
            search_filter = '(&(objectClass=posixGroup)(cn=' + group + '))',
            search_scope = self.config['LDAP']['group_search_scope'],
            attributes = ['cn', 'gidNumber', 'uniqueMember'],
            paged_size = 999))
        ldapgroupwuid = {}
        ldapgroupuids = []

        if ldapgroup:
            for user in ldapgroup[0]['attributes']['uniqueMember']:
                uid = self.get_ldap_user_uid(user)
                if uid:
                    ldapgroupuids.append(uid)

            ldapgroupwuid = {
                'gr_name': ldapgroup[0]['attributes']['cn'],
                'gr_id' : ldapgroup[0]['attributes']['gidNumber'],
                'gr_users': ldapgroupuids
                }
        return ldapgroupwuid

    # get_ldap_group_members_full
    def get_ldap_group_members_full(self,group):
        ldapgroup = list(self.ldapconn.extend.standard.paged_search(
            search_base = self.config['LDAP']['group_search_base'],
            search_filter = '(&(objectClass=posixGroup)(cn=' + group + '))',
            search_scope = self.config['LDAP']['group_search_scope'],
            attributes = ['cn', 'gidNumber', 'uniqueMember'],
            paged_size = 999))
        ldapgroupfull = []

        if ldapgroup:
            for user in ldapgroup[0]['attributes']['uniqueMember']:
                userdetail = self.get_ldap_user(user)
                if userdetail:
                    ldapgroupfull.append(userdetail)

        return ldapgroupfull

    # get_ldap_user
    def get_ldap_user(self,ldapdn):
        ldapuser = list(self.ldapconn.extend.standard.paged_search(
            search_base = ldapdn,
            search_filter = '(objectClass=*)',
            attributes = self.config.getlist('LDAP', 'user_search_attributes'),
            paged_size = 999))
        if not ldapuser:
            ldapuser = []

        return ldapuser
            
    
    # get_ldap_user_uid
    def get_ldap_user_uid(self,ldapdn):
        ldapuser = list(self.ldapconn.extend.standard.paged_search(
            search_base = ldapdn,
            search_filter = '(objectClass=*)',
            attributes = ['uid'],
            paged_size = 999))
        ldapuid = ldapuser[0]['attributes']['uid'][0]
        return ldapuid
    
    # get_ad_user_samaccount
    def get_ad_user_samaccount(self, adcn):
        aduser = list(self.adconn.extend.standard.paged_search(
            search_base = adcn,
            search_filter = '(objectClass=person)',
            #search_scope = self.config['AD']['user_search_scope'],
            #search_filter = '(&(objectClass=person)(cn=' + adcn + '))',
            attributes = ['sAMAccountName'],
            paged_size = 999))
        if not aduser:
            adsamaccount = ''
        else:
            adsamaccount = aduser[0]['attributes']['sAMAccountName']
        return adsamaccount

    # get_ad_group
    def get_ad_group(self,groupcn):
        adgrp = list(self.adconn.extend.standard.paged_search(
            search_base = groupcn,
            search_filter = '(objectClass=group)',
            attributes = ALL_ATTRIBUTES,
            paged_size = 999))
        adgrpentry = adgrp[0]
        return adgrpentry

    def get_ad_group_by_dispname(self,groupdispname):
        adgrpbydisp = list(self.adconn.extend.standard.paged_search(
            search_base = self.config['AD']['group_search_base'],
            search_scope = self.config['AD']['group_search_scope'],
            search_filter = '(&(objectClass=group)(displayName=' + groupdispname + '))',
            attributes = ALL_ATTRIBUTES,
            paged_size = 999))
        adgrpbydispentry = []
        if len(adgrpbydisp) > 1:
            for grp in adgrpbydisp:
                if grp['attributes']['name'].startswith('ticc'):
                    continue
                else:
                    adgrpbydispentry = grp
        else:
            adgrpbydispentry = adgrpbydisp[0]

        return adgrpbydispentry
        

    # get_ad_group_member_groups
    def get_ad_group_member_groups(self,group):
        adgrpgroups = list(self.adconn.extend.standard.paged_search(
            search_base = self.config['AD']['group_search_base'],
            search_scope = self.config['AD']['group_search_scope'],
            search_filter = '(&(objectclass=group)(memberOf=' + group + '))',
            attributes = ['distinguishedName'],
            paged_size = 999))
        if not adgrpgroups:
            adgrpgroupscn = []
        else:
            adgrpgroupscn = adgrpgroups
        return adgrpgroupscn
    
    # get_ad_group_members
    def get_ad_group_members(self,group):
        adgrpmembers = list(self.adconn.extend.standard.paged_search(
            search_base = self.config['AD']['user_search_base'],
            search_scope = self.config['AD']['group_search_scope'],
            search_filter = '(&(objectClass=person)(memberOf='+ group + '))',
            attributes = ['distinguishedName'],
            paged_size = 999)) 
        if not adgrpmembers:
            adgrpmembersdn = []
        else:
            adgrpmembersdn = adgrpmembers
        return adgrpmembersdn

    # get_ad_group_members
    def get_ad_group_members2(self,group):
        sbases = []
        sbases.append('OU=People,DC=ad,DC=uillinois,DC=edu')
        sbases.append('OU=Urbana,DC=ad,DC=uillinois,DC=edu')
        all_members = []
        for thisbase in sbases:
            adgrpmembers = list(self.adconn.extend.standard.paged_search(
                search_base = thisbase,
                search_scope = self.config['AD']['group_search_scope'],
                search_filter = '(&(objectClass=person)(memberOf='+ group + '))',
                attributes = ['distinguishedName', 'sAMAccountName', 'mail', 'uidNumber', 'displayName', 'uiucEduFirstName', 'uiucEduLastName'],
                paged_size = 999))
            all_members.extend(adgrpmembers)

        if not all_members:
            all_members_return = []
        else:
            all_members_return = all_members
        return all_members_return

    # get_ad_group_nested_members
    def get_ad_nested_group_members(self,group):
        # query for CN
        this_group = self.get_ad_group_by_dispname(group)
        all_nested_members = []
        all_nested_members_st = set()
        
        top_grp_members = self.get_ad_group_members2(this_group['attributes']['distinguishedName'])
        for top_member in top_grp_members:
            if not top_member['attributes']['distinguishedName'] in all_nested_members_st:
                all_nested_members.append(top_member)
                all_nested_members_st.add(top_member['attributes']['distinguishedName'])

        this_nested_groups = self.get_ad_nested_groups(this_group['attributes']['distinguishedName'])
        for nested_grp in this_nested_groups:
            nested_grp_members = self.get_ad_group_members2(nested_grp) 
            for nested_member in nested_grp_members:
                if not nested_member['attributes']['distinguishedName'] in all_nested_members_st:
                    all_nested_members.append(nested_member)
                    all_nested_members_st.add(nested_member['attributes']['distinguishedName'])

        if not all_nested_members:
            all_nested_members = []

        return all_nested_members

    # get_ad_nested_groups
    def get_ad_nested_groups(self,groupcn,visited=None,depth=0):
        #eprint("get_ad_nested_groups: "+groupcn)
        max_depth = 4
        if visited is None:
            visited = set()

        # skip if already processed
        if groupcn in visited:
            #eprint("VISITED: ", groupcn)
            return []

        # If depth is > 4 we're done
        if depth >= max_depth:
            return []

        # This group is now visited
        visited.add(groupcn)

        # create return set
        all_groups = set()

        nested_grps = self.get_ad_group_member_groups(groupcn)
        for this_nested in nested_grps:
            all_groups.add(this_nested['attributes']['distinguishedName'])
            all_groups.update(self.get_ad_nested_groups(this_nested['attributes']['distinguishedName'],visited,depth+1))

        #eprint(all_groups)
        return all_groups

    # get_ad_group_samaccounts
    def get_ad_group_samaccounts(self,group):
        # query group for CN
        this_group = self.get_ad_group_by_dispname(group)
        #eprint("get_ad_group_samaccounts: ", this_group)
        grp_samaccounts_set = set()

        # get users from top level group
        top_grp_members = self.get_ad_group_members2(this_group['attributes']['distinguishedName'])
        for member in top_grp_members:
            member_samaccount = self.get_ad_user_samaccount(member['attributes']['distinguishedName'])
            grp_samaccounts_set.add(member_samaccount)
        
        # get all nested groups
        this_nested_groups = self.get_ad_nested_groups(this_group['attributes']['distinguishedName'])

        # get users from nested groups
        for nested_grp in this_nested_groups:
            #eprint("NESTED_GRP: ", nested_grp)
            nested_grp_members = self.get_ad_group_members2(nested_grp)

            for member in nested_grp_members:
                #eprint("MEMBER: ", member['attributes']['distinguishedName'])
                member_samaccount = self.get_ad_user_samaccount(member['attributes']['distinguishedName'])
                grp_samaccounts_set.add(member_samaccount) 

        grp_samaccounts = list(grp_samaccounts_set)
        #eprint("FINISH get_ad_group_samaccounts: ",group, grp_samaccounts_set)

        return grp_samaccounts

    # archive and link nodemap files
    def archive_and_link_new(self, current_link, new_file, base_path):
        current_target = os.readlink(current_link)
        current_target_full = base_path+'/'+current_target
        current_target_rename = base_path+'/archive/'+current_target

        # symlink new file and move old to archive
        os.unlink(current_link)
        os.symlink(os.path.basename(new_file),current_link)
        os.rename(current_target_full, current_target_rename)

    # symlink new file and remove old
    def link_new_and_remove(self, current_link, new_file, base_path):
        current_target = os.readlink(current_link)
        current_target_full = base_path+'/'+current_target

        # symlink new file and remove old
        os.unlink(current_link)
        os.symlink(os.path.basename(new_file),current_link)
        os.remove(current_target_full)

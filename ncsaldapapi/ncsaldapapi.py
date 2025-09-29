#!/usr/bin/env python3
import configparser
import sys
import os
import requests
import logging
import json

def eprint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

class IccpNcsaLdap:
    def __init__( self, config_file="config" ):

        self.config_file = config_file

        # Load the config from a configuration file
        self.config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
        self.config.sections()
        self.config.read( self.config_file )

        self.url = self.config['API']['api_url']
        self.api_key = self.config['API']['api_key']

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=self.config['API']['logfile'])

    def test_json(self, inval):
        try:
            json.loads(inval)
            return True
        except ValueError:
            return False

    def _doreq(self, http_method: str, endpoint: str, data: {}):
        full_url = self.url + endpoint
        data['api_key'] = self.api_key
        response = requests.request(method=http_method, url=full_url, data=data)
        data_resp = response.text

        if response.status_code == 200:
            resp_return = {'code': response.status_code, 'data_out': data_resp}
        else:
            resp_return = {'code': response.status_code, 'data_out': data_resp}
            self.logger.error(f"Error with request {data}")
    
        return resp_return
    
    def create_campus_cluster_accounts(self, login, email, first_name, last_name):
        thisData = { 'login': login,
                     'email': email,
                     #'uidNumber' : uid,
                     'first_name' : first_name,
                     'last_name' : last_name }

        attempt = 0
        resp = self._doreq(http_method='POST', endpoint='create-campus-cluster-accounts', data=thisData)
        loginfo = login + " " + str(resp['code']) + json.dumps(resp['data_out'])
        if resp['code'] == 200:
            if self.test_json(resp['data_out']):
                json_resp = json.loads(resp['data_out'])
                if json_resp[login].startswith("created with uid "):
                    split_resp = json_resp[login].split()
                    new_uid = split_resp[-1]
                    logmsg = "SUCCESS creating: "+ loginfo
                    self.logger.info(logmsg)
                    return new_uid
                else:
                    logmsg = "Warning - unkown response when creating:"
                    self.logger.info(logmsg)
                    return 0
            else:
                logmsg = "Error creating: " + loginfo
                self.logger.error(logmsg)
                return 0
        else:
            logmsg = "Error creating: "+ loginfo
            self.logger.error(logmsg)
            return 0


    def create_campus_cluster_groups(self, group_name, gid, description, owner_login):
        thisData = { 'group_name' : group_name,
                     'gid'        : gid,
                     'description': description,
                     'owner_login': owner_login }

        resp = self._doreq(http_method='POST', endpoint='create-campus-cluster-groups', data=thisData)
        loginfo = group_name + " " + str(resp['code']) + json.dumps(resp['data_out'])
        if resp['code'] == 200:
            if self.test_json(resp['data_out']):
                json_resp = json.loads(resp['data_out'])
                if json_resp['result'] == "Group Created":
                    logmsg = "SUCCESS creating: "+ loginfo
                    self.logger.info(logmsg)
                    return 1
                else:
                    logmsg = "Warning - unkown response when adding:"
                    self.logger.info(logmsg)
                    return 0
            else:
                logmsg = "Error creating group: " + loginfo
                self.logger.error(logmsg)
                return 0
        else:
            logmsg = "Error creating group: " + loginfo
            self.logger.error(logmsg)
            return 0 


    def add_to_campus_cluster_groups(self,group_name,login):
        thisData = { 'group_name': group_name, 'login': login }

        resp = self._doreq(http_method='POST', endpoint='add-to-campus-cluster-groups', data=thisData)
        loginfo = login + " to group: " + group_name + " " + json.dumps(resp['data_out'])
        if resp['code'] == 200:
            if self.test_json(resp['data_out']):
                json_resp = json.loads(resp['data_out'])
#                if json_resp['result'] == "ok":
                if json_resp.get('result'):
                    if json_resp['result'] == "ok":
                        logmsg = "SUCCESS adding: " + loginfo
                        self.logger.info(logmsg)
                        return 1
                    else:
                        logmsg = "Warning - unknown response when adding:"
                        self.logger.info(logmsg)
                        return 0
                else:
                    logmsg = "Warning - unkown response when adding:"
                    self.logger.info(logmsg)
                    return 0
            else:
                logmsg = "Error adding: " + loginfo
                self.logger.error(logmsg)
                return 0
        else:
            logmsg = "Error adding: " + loginfo
            self.logger.error(logmsg)
            return 0

    def delete_from_campus_cluster_groups(self,group_name,login):
        cleanGroup = group_name.lower()
        thisData = { 'group_name' : cleanGroup, 'login': login }

        resp = self._doreq(http_method='POST', endpoint='delete-from-campus-cluster-groups', data=thisData)
        loginfo = login + " from group: " + group_name + " " + json.dumps(resp['data_out'])
        if resp['code'] == 200:
            if self.test_json(resp['data_out']):
                json_resp = json.loads(resp['data_out'])
                if json_resp.get('result'):
                    if json_resp['result'] == "User Removed":
                        logmsg = "SUCCESS removing: " + loginfo
                        self.logger.info(logmsg)
                        return 1
                    else:
                        logmsg = "Warning - unknown response when removing:"
                        self.logger.info(logmsg)
                        return 0
                else:
                    logmsg = "Warning - unkown response when removing:"
                    self.logger.info(logmsg)
                    return 0
            else:
                logmsg = "Error removing: " + loginfo
                self.logger.error(logmsg)
                return 0
        else:
            logmsg = "Error removing: " + loginfo
            self.logger.error(logmsg)
            return 0

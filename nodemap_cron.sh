#!/bin/bash

nodemap_dir=/taiga/admin/iccp/nodemap

# get_current_idmaps
${nodemap_dir}/cron/get_lustre_idmap.sh ${NODEMAP_NAME}

# run user nodemap generatioin push new files 
${nodemap_dir}/cron/user_nodemap.py
if [[ $? -eq 0 ]]; then
    ${nodemap_dir}/cron/push_pwgr_extras.sh passwd
    ${nodemap_dir}/cron/push_lustre_idmap.sh uid
fi

# run group sync and push new files
${nodemap_dir}/cron/sync_groups_ad.py

${nodemap_dir}/cron/sync_groups_ldap_ad.py

${nodemap_dir}/cron/sync_group_idmap.py
if [[ $? -eq 0 ]]; then
    ${nodemap_dir}/cron/push_lustre_idmap.sh gid
fi

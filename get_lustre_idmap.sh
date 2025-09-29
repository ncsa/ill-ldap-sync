#!/bin/bash

nodemap_dir=/taiga/admin/iccp/nodemap
host=tgio01
uidfile=uid.lustre.idmap
gidfile=gid.lustre.idmap

if [[ -z $NODEMAP_NAME ]]; then
    NODEMAP_NAME=$1
fi

if [[ $NODEMAP_NAME == "" ]]; then
cat << EOF
Usage: $0 [nodemap name]
EOF
exit 1
fi

ssh ${host} "lctl get_param nodemap.${NODEMAP_NAME}.idmap | grep uid," |awk '{print $5$7}'|grep -v ^$ > ${nodemap_dir}/${uidfile}
ssh ${host} "lctl get_param nodemap.${NODEMAP_NAME}.idmap | grep gid," |awk '{print $5$7}'|grep -v ^$ > ${nodemap_dir}/${gidfile}


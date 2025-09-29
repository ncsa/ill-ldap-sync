#!/bin/bash

if [[ -z $NODEMAP_NAME ]]; then
    NODEMAP_NAME=$1
fi

new_users=/root/nodemap/new_idmap/uid.lustre.new
new_groups=/root/nodemap/new_idmap/gid.lustre.new

errcount=0
if [[ -f "$new_users" && -s "$new_users" ]]; then
    for i in $(cat ${new_users})
    do
        /usr/sbin/lctl nodemap_add_idmap --name $NODEMAP_NAME --idtype uid --idmap ${i}
        if [ $? -ne 0 ]; then
            errcount=$((errcount+1))
            errlog="${errlog} ${i}"
        fi
        sleep 2
    done
    rm ${new_users}
fi

if [[ -f "$new_groups" && -s "$new_groups" ]]; then
    for i in $(cat ${new_groups})
    do
        /usr/sbin/lctl nodemap_add_idmap --name $NODEMAP_NAME  --idtype gid --idmap ${i}
        if [ $? -ne 0 ]; then
            errcount=$((errcount+1))
            errlog="${errlog} ${i}"
        fi
        sleep 2
    done
    /usr/bin/rm ${new_groups}
fi

exit ${errcount}

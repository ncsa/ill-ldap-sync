#!/bin/bash

nodemap_dir=/taiga/admin/iccp/nodemap
lustre_idmap_dir=/root/nodemap/new_idmap
host=tgio01
newuidfile=${nodemap_dir}/uid.lustre.new
newgidfile=${nodemap_dir}/gid.lustre.new

if [ -z "$1" ]; then
    echo "Usage: $0 [uid|gid]"
    exit 1
fi

if [ "$1" == "uid" ]; then
    /bin/scp $newuidfile ${host}:${lustre_idmap_dir}/
elif [ "$1" == "gid" ]; then
    /bin/scp $newgidfile ${host}:${lustre_idmap_dir}/
else
    echo "Unkown argument: $1"
fi

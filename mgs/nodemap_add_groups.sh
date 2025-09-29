#!/bin/bash

if [[ -z $NODEMAP_NAME ]]; then
    NODEMAP_NAME=$2
fi

if [[ $NODEMAP_NAME == "" ]]; then
cat << EOF
Usage: $0 [gid idmap file] [nodemap name]
EOF
exit 1
fi

for i in $(cat $1)
do
    echo "lctl nodemap_add_idmap --name $NODEMAP_NAME --idtype gid --idmap ${i}"
    lctl nodemap_add_idmap --name $NODEMAP_NAME --idtype gid --idmap ${i}
    sleep 2
done

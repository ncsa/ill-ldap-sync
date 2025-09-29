#!/bin/bash

if [[ -z $NODEMAP_NAME ]]; then
    NODEMAP_NAME=$2
fi

if [[ $NODEMAP_NAME == "" ]]; then
cat << EOF
Usage: $0 [uid idmap file] [nodemap name]
EOF
exit 1
fi

for i in $(cat ${1})
do
    echo "lctl nodemap_add_idmap --name $NODEMAP_NAME --idtype uid --idmap ${i}"
    lctl nodemap_add_idmap --name $NODEMAP_NAME --idtype uid --idmap ${i}
    sleep 2
done

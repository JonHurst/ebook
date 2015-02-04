#!/bin/bash

if [ -e "${1}.old" ]
then
    echo "${1}.old exists"
    ANS=""
    until [[ "$ANS" == "y" || "$ANS" == "n" ]]
    do read -p "overwrite? [y/n] " ANS
    done
    if [[ "$ANS" == "n" ]]
    then
        exit -1
    fi
fi

cp "${1}" "${1}.old"
tidy -asxhtml -utf8 --wrap 110 --indent auto --quote-nbsp no --write-back yes "$1"

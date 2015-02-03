#!/bin/bash

DEFAULTCSS_LOCATION="/home/jon/proj/ebook/include"

#Need 2 additional cl arguments, the 2nd of which must be a readable file and
#the first of which must be '5' or '6'
if [ $# -lt 2 -o "$1" != "5" -a "$1" != "6" ]
then
    echo "Usage: $0 [5|6] HTMLFILE"
    exit -1
fi

if [ "$1" == "5" ]
then
    DEFAULTCSS="${DEFAULTCSS_LOCATION}/prince-5in.css"
else
    DEFAULTCSS="${DEFAULTCSS_LOCATION}/prince-6in.css"
fi

OUTPUTFILE="${2%.*}.pdf"
shift
prince -s $DEFAULTCSS -o $OUTPUTFILE "$@"

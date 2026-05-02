#!/bin/bash
# Helper: fetch UniProt entry text, extract ID/status/protein-name/gene-name/organism.
# Usage: bash verify_accessions.sh <ACC> [<ACC> ...]

set -u

for acc in "$@"; do
    txt=$(curl -sS --max-time 15 "https://rest.uniprot.org/uniprotkb/${acc}.txt" 2>/dev/null) || { echo "$acc  FETCH_FAIL"; continue; }
    if [ -z "$txt" ]; then echo "$acc  EMPTY_OR_OBSOLETE"; continue; fi

    id_line=$(echo "$txt" | grep -m1 '^ID ' | awk '{print $2, $3}' | tr -d ';')
    de_full=$(echo "$txt" | awk '/^DE   RecName: Full=/{sub("^DE   RecName: Full=",""); sub(" \\{.*","",$0); sub(";$",""); print; exit}')
    [ -z "$de_full" ] && de_full=$(echo "$txt" | awk '/^DE   SubName: Full=/{sub("^DE   SubName: Full=",""); sub(" \\{.*","",$0); sub(";$",""); print; exit}')
    gn=$(echo "$txt" | awk '/^GN   /{sub("^GN   Name=",""); sub(" \\{.*",""); sub(";.*",""); print; exit}')
    os=$(echo "$txt" | awk '/^OS   /{sub("^OS   ",""); sub(" \\(.*","",$0); sub("\\.$",""); print; exit}')
    len=$(echo "$txt" | awk '/^ID /{print $4}')

    printf "%-12s | %-9s | len=%-4s | gene=%-12s | %s | %s\n" \
        "$acc" "$id_line" "$len" "${gn:-?}" "${de_full:-?}" "${os:-?}"
done

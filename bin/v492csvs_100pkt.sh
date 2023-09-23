#!/bin/bash
[[ $_ != $0 ]] && leave=return || leave=exit
me=$(basename "$0")
mydir=$(dirname "${me}")
me=$(basename "${me}")

die() { printf "${me}: %s -- exiting.\n" >&2 ; ${leave} 1; } 

usage() {
    cat >&2 <<_eof_
Usage: ${me} <folder>
${me} parses Harrier VRT Extension Packets in a folder into CSV files:
   <v49file>.csv : contains packet payload and metadata
   <v49fileL.hdr.csv : contains single-line packet metadata
_eof_
    ${leave} 1
}

(($#)) || usage
[ -d "$1" ] || die "$1 must be a folder"

command cd "$1" || die "Cannot change to $1"

n=0
for i in *.v49; do 
    [[ "$i" =~ .*_100.* ]] && continue
    ((n++))
    printf "${me}: Processing $i...\n"
    name=$(basename "$i" ".v49")
    dd bs=4152 count=100 if="$i" of="${name}_100.v49"
done
((n)) || die "No .v49 files found in ${PWD}"
for i in *_100.v49; do 
    printf "${me}: Processing $i...\n"
    ~ljcorsa/cpp/bin/v492csv "$i" > "$i.out.csv" 2> "$i.hdr.csv" 
done

awk 'FNR >= 3 && FNR <= 5' *_100.v49.hdr.csv | tee "firstlines-$(basename "${PWD}").txt"
printf "${me}: done.\n"



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
for v49file in *.v49; do 
    [[ "$v49file" =~ .*_100.* ]] && continue
    ((n++))
    stream="${v49file%%\.v49},"
    printf "${me}: Processing ${v49file}...\n"
    (
    ~ljcorsa/cpp/bin/v492csv "$v49file" \
        1> >(grep "${stream}" > "${v49file}.out.csv") \
        2> >(grep "${stream}" > "${v49file}.hdr.csv") &
    ) &>/dev/null
done
((n)) || die "No .v49 files found in ${PWD}"

printf "${me}: waiting...\n"
sleep 1
watch -n 1 -p wc -l ????????.v49.hdr.csv & disown
watch_pid=$!
wait
kill $watch_pid
ls -l ????????.v49*
#    | xargs awk 'FNR >= 3 && FNR <= 5'\
command ls *.v49.hdr.csv \
    | grep -v _100 \
    | xargs head -3 \
    | tee "firstlines-$(basename "${PWD}").txt"
printf "${me}: done.\n"

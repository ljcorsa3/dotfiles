#!/bin/bash

awkscript=$( cat << '__awkscript_end__'
    function report() {
        if(id>0 && ldr>0) {
            #printf "done" > "/dev/stderr"
            printf("%d %d\n",id,ldr) 
            exit 0
        }
        id=0;ldr=0
    }
    BEGIN {
        id=0; ldr=0;
        #print "targ~" targ > "/dev/stderr"
    }

    /^$/ { report() }
    /^Id=/ {
        id=int($2)
        #print "id~" id > "/dev/stderr"
    }
    /^Leader=/ {
        #print "ldr~" $2 > "/dev/stderr"
        if(int($2)==int(targ)){
            ldr=int($2)
            #print "found" > "/dev/stderr"
        }
    }
    END { report() }

__awkscript_end__
)

loginctl
ppids=$PPID
pid=$PPID
echo  "My parent is: $pid"
ps -fh -o ppid,pid,user,args -p $pid

until [ "$pid" -eq 1 ]; do
    ppid=$(command ps -hoppid:1 $pid)
    [ "$ppid" -eq 1 ] && break
    ppids="${ppid} ${ppids}"
    pid=$ppid
    ps -fh -o ppid,pid,user,args -p $pid
done
PPIDS=( "${ppids}" )
echo "tree is ${PPIDS[@]}"

ldr=$(ps -hoppid:1 $(ps -hoppid:1 $(ps -hoppid:1 $$))) # :1 gets rid of leading spaces
echo leader=$ldr
a=( $( loginctl --no-pager --no-legend |
    awk -v uid=$(id -u) '$2==uid {print $1}' |
    xargs loginctl --no-pager show-session |
    awk -F '=' -v targ="${ldr}" -- "${awkscript}" ) )
echo "Session and leader: ${a[@]}"
loginctl --no-pager session-status ${a[0]}


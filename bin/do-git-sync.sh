#!/bin/bash

readarray -t dirs < <(
    find . -mindepth 1 -xdev -type d -name .git -printf '%P\0' |
    xargs -r0 -L 1 dirname
)

command cd ~/mnt/f/ljcorsa/sync

for d in "${dirs[@]}"; do
    (
        mkdir -p "$d"
        command cd $d; pwd
        if [ -d .git ]; then
            git pull -v 
        else
            git clone -v ${HOME}/$d .
        fi
    )
done

#!/bin/bash

if ! command cd ~/mnt/f/ljcorsa/sync; then
    printf "f/ljcorsa/sync is not mounted!\n" >&2
    exit 1
fi

readarray -t dirs < <(
    find "${HOME}" -mindepth 1 -xdev -type d -name .git -printf '%P\0' |
    xargs -r0 -L 1 dirname
)

for d in "${dirs[@]}"; do
    (
        mkdir -p "$d"
        if ! command cd $d; then
            printf "cannot cd to $PWD/$d" >&2
            exit # this subshell
        fi
        pwd
        if [ -d .git ]; then
            git pull -v 
        else
            git clone -v ${HOME}/$d .
        fi
    )
done

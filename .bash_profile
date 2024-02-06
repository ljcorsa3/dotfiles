# .bash_profile
# vim: filetype=sh
# skip if not interactive WITH a tty
[[ $- == *i* ]] || return
[ -t 0 ] || return
[ "$(basename ${SHELL})" == "sh" ] && { exec env -i HOME="${HOME}" ENV="${HOME}/.profile" ${SHELL} -il; }
#debugging
if ((0)); then
    LOGFILE=/tmp/${USER}-$$.xtrace.log
#   exec >>${LOGFILE} 2>&1 42>>${LOGFILE}
    exec 42>${LOGFILE}
    BASH_XTRACEFD=42
    echo >>${LOGFILE}
    date >>${LOGFILE}
    ps --no-headers -fp $$ ${PPID} >>${LOGFILE}
    echo ${TERM} >>${LOGFILE}
    echo >>${LOGFILE}
    ((0)) && trap '(read -p "[${BASH_SOURCE}:${LINENO}] ${BASH_COMMAND}? ")' DEBUG   #single-stepping
    set -xv
fi
: ${BASHPROFILE_SOURCED:=1}; export BASHPROFILE_SOURCED

# don't run if being called from xrdp-sesman
# usual parents are gnome-terminal-server, sshd, login
ps --no-headers -fp ${PPID} 2>/dev/null | grep xrdp-sesman &>/dev/null && return 0
# don't run without a proper terminal
[ -z "${TERM}" -o "${TERM}" == dumb ] && return 0

# set RCFILE differently if being called by setenv
[[ ${BASH_SOURCE[1]} =~ /setenv$ ]] && export RCFILE=${BASH_SOURCE[1]} || export RCFILE=${BASH_SOURCE[0]}

# if TMOUT or PROMPT_COMMAND are read-only, re-invoke shell without them
if readonly | grep -qE '(TMOUT|PROMPT_COMMAND)'; then
    # save environment without TMOUT or PROMPT_COMMAND to a PID-specific file
    # named ~/.env$$.   This env will be sourced after necessary re-invocation
    # each envvar written wrapped with single quotes, e.g., VAR='VAL'
    # note that env command breaks up long lines, so use null terminators
    env -0 | awk 'BEGIN {RS="\0"; qt="\x27"}
        /^(TMOUT|PROMPT_COMMAND)=/ {next}
        {sub("=","=" qt); print $0 qt}' > $HOME/.env$$
    # pass verbose option along...
    [[ $- =~ x ]] && x=' -x'
    # re-invoke shell (and this .bash_profile!) with an empty env.
    # future self will know what to do.
    exec env -i BASHPROFILE_SOURCED=2 TERM=${TERM} HOME=${HOME} USER=${USER} \
        ${SHELL} --noprofile --rcfile "${RCFILE}" -i ${x}
elif ((BASHPROFILE_SOURCED==2)); then
    # if we're here, we've been reinvoked.  Let's get argv[0] set to "-bash" if not already
    if [ $0 != "-$(basename ${SHELL})" ]; then
        # OK, one more reinvocation.  since no profile or rc, temporarily use
        # shell prompt to invoke them
        export BASHPROFILE_SOURCED=3 RCFILE PROMPT_COMMAND="source ${RCFILE}"
        exec -l -a "$(basename ${SHELL})" --noprofile -norc -i
    fi
fi
# read and delete pid-specific environment file created (or not) above
[ -r ${HOME}/.env$$ ] && source ${HOME}/.env$$ ; rm -f ${HOME}/.env$$

# export everything in this script (turn off at end)
set -a

# # if launched from ssh, grab our remote client info
# if [ -n "${SSH_CLIENT}" ]; then
#     SSH_CLIENT_IP="${SSH_CLIENT%%[[:space:]]*}"
#     # SSH_CLIENT_NAME=$(nslookup ${SSH_CLIENT_IP} 2>/dev/null |
#     #   awk '/name = / {sub(/\.$/,"",$NF); print $NF}')
#     SSH_CLIENT_NAME=$(dig +search +time=1 +short +4 -x ${SSH_CLIENT_IP} \
#         2>/dev/null | sed -e 's/\.$//')
# fi

# initialize important env vars
TMOUT=0
unset USERNAME MAILCHECK

# # initialize ssh-agent if no signs exist
# if [ -z "${SSH_AUTH_SOCK}" -a -r "~/.ssh/id_rsa" ]; then
#     eval $(ssh-agent -s)
# fi
# if [ "${SSH_AUTH_SOCK}" ]; then
#     ssh-add -l | grep -q "${USER}" || \
#     ssh-add  <&-
# fi

if [[ "${USER,,}" =~ (ren|ljcorsa) ]]; then
    umask 0
    TZ=EST5EDT
    USER=${LOGNAME:-$(id -un)}
    BASH_VERSION_NO="${BASH_VERSINFO[0]}.${BASH_VERSINFO[1]}"

    case "$(uname -o)" in
        *Linux*)
            CPATH=/usr/include:/usr/local/include:$HOME/share/include
#           C_INCLUDE_PATH=/usr/lib/x86_64-redhat-linux5E/include
            if [[ :$LD_LIBRARY_PATH: =~ :/usr/local/lib: ]]; then
                LD_LIBRARY_PATH+=${LD_LIBRARY_PATH:+:}/usr/local/lib
            fi
            LANG=en_US.utf-8
            LESSCHARSET=utf-8
            if [[ ! :$PATH: =~ :$HOME/bin: ]]; then
                PATH=".:$HOME/bin${PATH:+":$PATH"}"
            fi
            if [[ ! :$PATH: =~ :$HOME/.local/bin: ]]; then
                PATH="$HOME/.local/bin${PATH:+":$PATH"}"
            fi
        ;;
    esac

fi

# set up (and work around bug) in dircolors
if [ -f "$HOME/.dircolors" ] ; then
    if grep -sq -E "TERM[[:space:]]+$TERM" "$HOME/.dircolors"; then
        shopt failglob &>/dev/null ; RC=$?
        shopt -u failglob
        eval "$(dircolors -sh $HOME/.dircolors 2>/dev/null)"
        ((RC)) || shopt -s failglob
        unset RC
    fi
fi

# customize common commands
#GREP_OPTIONS='--color=auto --binary-files=without-match --no-messages'
GREP_COLOR='7;33'
LS_OPTIONS='-Fh --color=auto --group-directories-first'
command ls $LS_OPTIONS >/dev/null 2>&1  || LS_OPTIONS="-F --color=auto"
# minicom: no init, Alt key, color, status
MINICOM='-moz -c on'

# set vim as editor if available
FCEDIT=vi; EDITOR=vi; VISUAL=vi
type -p vim >/dev/null 2>&1 && { EDITOR=vim; VISUAL=vim; }

# set less as pager if availabel
PAGER=more
if type -p less >/dev/null 2>&1 ; then
    PAGER=less
    LESS="-RcX -x4 -P?f%f:stdin. [%T] (?pB%pB\% li %lb/%L:line %lb.)?m -- File %i/%m."
    [ -x /usr/bin/lesspipe.sh ] && LESSOPEN="| /usr/bin/lesspipe.sh %s 2>&-"
fi

# parse man configuration for manfile path
if [ -r /etc/man.config ]; then
    MANPATH=$(awk '$1 == "MANPATH" {p=$2 ":" p} END {print p}' /etc/man.config)
    MANPATH="${MANPATH}${HOME}/share/man"
fi

#[ "${DISPLAY}" ] && xhost + >/dev/null 2>&1
unset XAUTHORITY ER USERNAME MAILCHECK

# set up common colors for shell prompts
export -n ps1_ign='\001' ps1_noign='\002'
BLACK=${ps1_ign}$(tput sgr0;tput setaf 0)${ps1_noign}
DKGRAY=${ps1_ign}$(tput bold;tput setaf 0)${ps1_noign}
RED=${ps1_ign}$(tput sgr0;tput setaf 1)${ps1_noign}
LTRED=${ps1_ign}$(tput bold;tput setaf 1)${ps1_noign}
GREEN=${ps1_ign}$(tput sgr0;tput setaf 2)${ps1_noign}
LTGREEN=${ps1_ign}$(tput bold;tput setaf 2)${ps1_noign}
BROWN=${ps1_ign}$(tput sgr0;tput setaf 3)${ps1_noign}
YELLOW=${ps1_ign}$(tput bold;tput setaf 3)${ps1_noign}
BLUE=${ps1_ign}$(tput sgr0;tput setaf 4)${ps1_noign}
LTBLUE=${ps1_ign}$(tput bold;tput setaf 4)${ps1_noign}
PURPLE=${ps1_ign}$(tput sgr0;tput setaf 5)${ps1_noign}
LTPURPLE=${ps1_ign}$(tput bold;tput setaf 5)${ps1_noign}
CYAN=${ps1_ign}$(tput sgr0;tput setaf 6)${ps1_noign}
LTCYAN=${ps1_ign}$(tput bold;tput setaf 6)${ps1_noign}
GRAY=${ps1_ign}$(tput sgr0;tput setaf 7)${ps1_noign}
WHITE=${ps1_ign}$(tput bold;tput setaf 7)${ps1_noign}
RST=${ps1_ign}$(tput sgr0)${ps1_noign}

#make less(1) colorful and happy with ncurses
LESS_TERMCAP_mb=$(tput bold; tput setaf 2) # green
LESS_TERMCAP_md=$(tput bold; tput setaf 6) # cyan
LESS_TERMCAP_me=$(tput sgr0)
LESS_TERMCAP_so=$(tput bold; tput setaf 3; tput setab 4) # yellow on blue
LESS_TERMCAP_se=$(tput rmso; tput sgr0)
LESS_TERMCAP_us=$(tput smul; tput bold; tput setaf 7) # white
LESS_TERMCAP_ue=$(tput rmul; tput sgr0)
LESS_TERMCAP_mr=$(tput rev)
LESS_TERMCAP_mh=$(tput dim)
LESS_TERMCAP_ZN=$(tput ssubm)
LESS_TERMCAP_ZV=$(tput rsubm)
LESS_TERMCAP_ZO=$(tput ssupm)
LESS_TERMCAP_ZW=$(tput rsupm)
         
# run all the bash startups
if [[ $(readlink -f "${BASH_SOURCE[0]}") == "${HOME}/.bash_profile" ]]; then
    if [ -r "${HOME}/.bashrc" ]; then
        export BASH_ENV="${HOME}/.bashrc"
        source "${HOME}/.bashrc"
    fi
fi

#get nickname for HOST
typeset -F getNickname &>/dev/null && HOST=$(getNickname)
# set HOST to first declaration in ssh config if possible
if [ -z "${HOST}" -a -r ~/.ssh/config ]; then
    HOST=$(gawk -v h="$(hostname -s)" -- '
    $1 == "Host" {
        for (i=2;i<=NF;i++) {
           if (h == $i) {
               print $2; exit
           }
        }
    }' ~/.ssh/config )
fi
# if HOST unset, set to short host
: ${HOST:=$(hostname -s)}

# construct initial window titles
case $TERM in
    linux) unset _title ;;
    xterm*|putty*) _title='${ps1_ign}\033]0;\u@${HOST}:\w\a${ps1_noign}' ;;
esac
unset ps1_ign ps1_noign

# construct initial prompts (red==failure, green=ok)
# if there is a pre-existing PROMPT_COMMAND, we have to re-insert
# ... this ahead of our succeed/fail stuff
_success='${_title}${GREEN}\u${LTPURPLE}@${GREEN}${HOST} ${LTBLUE}\w\r\n${GREEN}\$ ${RST}'
_failure='${_title}${RED}\u${LTPURPLE}@${RED}${HOST} ${LTBLUE}\w\r\n${RED}\$ ${RST}'
if [ -z "${PROMPT_COMMAND}" ]; then
    PROMPT_COMMAND='(($?==0)) && PS1="$_success" '
    PROMPT_COMMAND+=' || PS1="$_failure" '
    PROMPT_COMMAND+=' ; builtin history -a '
else
    # if we've already done this, don't redo
    if [[ ! "${PROMPT_COMMAND}" =~ "_success" ]] ; then
        PROMPT_COMMAND='((_rv=$?));'"${PROMPT_COMMAND}"
        PROMPT_COMMAND+=' ; ((_rv==0)) && PS1="$_success" '
        PROMPT_COMMAND+=' || PS1="$_failure" '
        PROMPT_COMMAND+=' ; unset _rv '
        PROMPT_COMMAND+=' ; builtin history -a '
    fi
fi
PS1="$_success"
PS2='>> '
PS3='>>> '
#PS4='+${BASH_SOURCE##*/}:${LINENO}:${FUNCNAME[0]:+${FUNCNAME[0]}: }'
PS4='+$(date "+%H:%M:%S"):${BASH_SOURCE##*/}:${LINENO}:${FUNCNAME[0]:+${FUNCNAME[0]}: }'

#declare -i SHLVL0=$SHLVL
if [ ! "${SHLVL0}" ]; then
    SHLVL=1
    [ "${DESKTOP_SESSION}" ] && SHLVL0=2
    [[ $(ps --no-header -p $PPID -o args) =~ terminator ]] && SHLVL0=3
fi
# host-specific history
TTY=$(tty | sed -e 's^/dev/^^' -e 's^/^^')
if [[ "${USER,,}" =~ (pi|ren|ljcorsa) ]]; then
    if [ -f ${HOME}/.bash_history ]; then
        # convert file to folder full of timestamped files
        dt=$(stat --printf '%Z' "${HOME}/.bash_history")
        dt=$(date '+%y%m%d-%H:%M' "@${dt}")
        TMPHIST="${dt}-${HOST}-${TTY}"
        # rename history file
        mv "${HOME}/.bash_history" "${TMPHIST}"
        # create history folder
        mkdir "${HOME}/.bash_history"
        # move FILE to new folder
        mv "${TMPHIST}" "${HOME}/.bash_history"
        unset dt TMPHIST
    fi
    HISTTIMEFORMAT="%s "
    HISTFILE="${HOME}/.bash_history/$(date '+%y%m%d-%H:%M')-${HOST}-${TTY}"
    HISTFILESIZE=0
    HISTCONTROL=erasedups
    HISTIGNORE="l:l[als]:h:hh:H:HH:history:[bf]g:exit"
    HISTFILESIZE=2200
    HISTSIZE=2000
    source ~/bin/hist_combiner
fi

# set up anaconda
for d in ${HOME} /opt /usr/local; do
    if [ -f ${d}/anaconda3/etc/profile.d/conda.sh ]; then
        source ${d}/anaconda3/etc/profile.d/conda.sh
        if [ -f ${d}/anaconda3/bin/activate ]; then
            source ${d}/anaconda3/bin/activate
            conda activate base
        fi
        break
    fi
done
unset d

# PYTHON
[ -r "${HOME}/.pythonrc" ] && PYTHONSTARTUP="${HOME}/.pythonrc"

# maintain DIRSTACK across sessions
if [ -r "${HOME}/.dirslist" ]; then
    # cd_func() appends each dir to its list
    # get last ten unique entries to seed DIRSTACK
    readarray -t arr < <( tac "${HOME}/.dirslist" |
        awk 'BEGIN {a[ENVIRON["HOME"]]=1} {if(!a[$0]++){if(++i<10){print}}}' )
    # clear DIRSTACK
    dirs -c
    # push entries onto stack
    for ((i=${#arr[*]}-1;i>=0;i--)); do
        pushd -n "${arr[i]}" &>/dev/null
    done
    unset i arr
fi

# remove duplicates in PATH
PATH=$( printf '%s' "${PATH}" | 
    awk -v RS=':' '!($0 in a){a[$0];printf("%s%s",length(a)>1?":":"",$0)}' )

# try to get a unique ssh agent going
if [ "${WSL2}" == "1" ] && type -p wsl2-ssh-pageant &>/dev/null; then
	export SSH_AUTH_SOCK="$HOME/.ssh/agent.sock"
	rm -f ${SSH_AUTH_SOCK}
	(
		setsid nohup socat UNIX-LISTEN:"$SSH_AUTH_SOCK,fork" EXEC:wsl2-ssh-pageant &>/dev/null &
		disown
	)
elif typeset -F startAgent &>/dev/null; then
	startAgent -s
fi

# stop exporting vars
set +a

# bash completion
if [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
fi

# run all the bash startups
if [ -z "${BASHRC_SOURCED}" ]; then
    if [[ "${USER,,}" =~ (pi|ren|ljcorsa) ]]; then
        [ -r ~/.bashrc ] && { export BASH_ENV="~/.bashrc"; source ~/.bashrc; }
    fi
fi

cd .

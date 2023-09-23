# .bashrc
# vim: filetype=sh nu wm=0

# skip if not interactive WITH a tty
[[ $- == *i* ]] || return
[ -t 0 ] || return
    
# Source global definitions # sourced in local definitions
# [ -r /etc/bashrc ] && source /etc/bashrc

# Source local definitions
#[ -r ~git/.bashrc ] && source ~git/.bashrc

#builtin history -r

# ssh logins don't always source .bash_profile
export BASHRC_SOURCED=1
[ -z "${BASHPROFILE_SOURCED}" -a -r ~/.bash_profile ] && source ~/.bash_profile

set -o vi
set -o notify
set -o ignoreeof
bind -m vi-command
bind '"\\e[A":history-search-backward'
bind '"\\e[B":history-search-forward'
bind '"\\e0A":history-search-backward'
bind '"\\e0B":history-search-forward'
# make tab cycle through commands after listing
bind '"\t":menu-complete'
bind "set show-all-if-ambiguous off"
bind "set completion-ignore-case off"
bind "set menu-complete-display-prefix on"

shopt -sq dotglob nocaseglob
shopt -sq checkwinsize cmdhist huponexit histappend xpg_echo
[ ${BASH_VERSINFO[0]} -gt 3 ] && shopt -sq globstar

# User specific aliases
[ -r ~/.aliases ] && source ~/.aliases

# User specific functions
[ -r ~/.functions ] && source ~/.functions

# if not in my login group, make all new files group-accessible
[ "$(id --group --name)" == "$(id --group --name $LOGNAME)" ] || umask 0002
return

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/opt/anaconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
        . "/opt/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="/opt/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<


" .vimrc
"        0         0         0         0         0         0         0         0         0         1         1         1
"        1         2         3         4         5         6         7         8         9         0         1         2
"23456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
set nocompatible " always set.  compatibility sucks.
set nobackup 
set swapfile

:try
	colorscheme slate
:catch /^Vim\%((\a\+)\)\=:E185/
:endtry


" Set off the other paren
highlight MatchParen ctermbg=7
" highlight current line & adjust color
"highlight CursorLine term=NONE cterm=NONE ctermbg=7
"set cul

" try paste mode
autocmd InsertLeave <buffer> "normal! :set nopaste\<cr>"
map <leader>I :set paste<cr>I
map <leader>i :set paste<cr>i
map <leader>O :set paste<cr>O
map <leader>o :set paste<cr>o

set showmode showcmd
set shiftwidth=4 tabstop=4 wrapmargin=4 softtabstop=4 wrap sidescroll=1
" allow backspacing over anything in Insert mode
set backspace=indent,eol,start
"set backspace=indent,eol
"set textwidth=80 
"set linebreak
set sidescroll=1
"set list
set listchars=eol:$,tab:>.,trail:.,extends:#,nbsp:.
set listchars+=precedes:<,extends:>

set autoindent
set expandtab writeany

" report everything all the time
set report=1
set noerrorbells visualbell t_vb=
 
set ruler rulerformat=%l/%L(%p%%),%c
set ignorecase smartcase
set shortmess=lnrxI  
" set mouse=a

" make redraw (Ctrl-L) unhighlight search results
inoremap <C-l> <esc>:noh<cr>:redraw!<cr>:<bs>i
nnoremap <C-l> :noh<cr>:redraw!<cr>:<bs>

function! IsCapsLockOn()
    echohl ErrorMsg
    echo "             CAPS LOCK?            "
    echohl None
    sleep 700m
endfunction
map K :call IsCapsLockOn()<cr>:redraw<CR>:<BS>

" undo/redo
map  <C-Z> :undo<cr>
map  <C-Y> :redo<cr>
imap <C-Z> <esc>:undo<cr>
imap <C-Y> <esc>:redo<cr>

" remove ANSI escape sequences
map <leader>m :%s/<esc>\[.\{-}m//g<cr>

" Insert OFF when moving
imap <Up> <esc><Up>
imap <Down> <esc><Down>
imap <Left> <esc><Left>
imap <Right> <esc><Right>
imap <PageUp> <esc><PageUp>
imap <PageDown> <esc><PageDown>
imap <S-Up> <esc><S-Up>
imap <S-Down> <esc><S-Down>
imap <S-Left> <esc><S-Left>
imap <S-Right> <esc><S-Right>
imap <S-PageUp> <esc><S-PageUp>
imap <S-PageDown> <esc><S-PageDown>
imap <C-Up> <esc><C-Up>
imap <C-Down> <esc><C-Down>
imap <C-Left> <esc><C-Left>
imap <C-Right> <esc><C-Right>
imap <C-PageUp> <esc><C-PageUp>
imap <C-PageDown> <esc><C-PageDown>
noremap xp xph
nnoremap <silent> xw "_yiw:s/\(\%#\w\+\)\(\W\+\)\(\w\+\)/\3\2\1/<cr><c-o><c-l>

" Automatically cd into the directory that the file is in
" set autochdir doesn't work
autocmd BufEnter * execute "chdir ".escape(expand("%:p:h"), ' ')

" Allow saving of files as sudo when I forgot to start vim using sudo (once I can has privac)
cmap w!! w !sudo tee > /dev/null %

filetype on
filetype indent on
filetype plugin on
syntax enable

set grepprg=grep\ -nH\ $*
set expandtab 
set incsearch nohlsearch

set magic
set wildchar=<TAB> wildmenu

set title
set laststatus=2 " status line always present
set statusline=%F\ %m%r%w[%{&ff}]%y\ %l,%v(%p%%)\ %a

" useful when moving among multiple files and hating to get write! errors
set noautowrite autoread ttyfast

"highlight OverLength ctermbg=red ctermfg=black guibg=khaki3 "match OverLength /%80v.+/ "set colorcolumn=80
let g:vimsyn_embed= "mpPrt"
:if v:version >= 700
set diffopt=filler,context:3,vertical,iwhite
:endif

let python_highlight_all = 1

let @a=':%s/\[.\{-}m//g'

augroup myvimrc
    au!
    au BufWritePost .vimrc,_vimrc,vimrc,.gvimrc,_gvimrc,gvimrc so $MYVIMRC | if has('gui_running') | so $MYGVIMRC | endif
augroup END


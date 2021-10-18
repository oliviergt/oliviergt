let mapleader=","

" setl suffixesadd+=.md

" Use gf to open markdown file when the cursor is on a link:
autocmd FileType markdown setlocal suffixesadd+=.md

" Expand all folds upon opening markdown file.
autocmd BufRead *.md normal! zR

function! OpenKmsFile(d) " {{{
  if filereadable(a:d . ".md")
    execute 'edit' a:d . ".md"
    execute "normal! zR\<down>\<down>"
  else  
    execute 'edit' a:d . ".md"
    execute "normal! a# " . a:d . "\<cr>\<cr>\<Esc>"
  endif
endfunction " }}}

function! MdFmtCurrentParagraph() " {{{
  execute "normal! vip!./mdfmt.py\<cr>"
  " execute "'<,'>!./mdfmt.py"
  " execute "normal! gv:!./mdfmt.py"
endfunction " }}}

" Today: Open today's journal (create file if necessary).
nnoremap <leader>t :execute OpenKmsFile(strftime("%Y-%m-%d"))<cr>
" Yesterday: Open yesterday's journal (create file if necessary).
nnoremap <leader>y :execute OpenKmsFile(strftime("%Y-%m-%d", localtime() - 3600 * 24))<cr>
" format Paragraph: Formats the current paragraph.
nnoremap <leader>p :execute MdFmtCurrentParagraph()<cr>

set shiftwidth=2

" Also use shiftwidth=2 for python code.
autocmd BufRead,BufNewFile *.py set shiftwidth=2

au CursorMoved * checktime
au FileChangedShell * echohl "Warning: File changed on disk"

syntax on

inoremap jk <esc>

set backup                        " enable backups
set noswapfile                    " it's 2013, Vim.

set undodir=~/.vim/tmp/undo//     " undo files
set backupdir=~/.vim/tmp/backup// " backups
set directory=~/.vim/tmp/swap//   " swap files

set expandtab

inoremap <c-u> <esc>viwUea

nnoremap <leader>ve :e ~/.vimrc<cr>
nnoremap <leader>vc :e ~/github/oliviergt/configs/vim/config.vim<cr>
nnoremap <leader>vs :source ~/.vimrc<cr>
nnoremap <leader>vn :e ~/secure/notes.txt<cr>
nnoremap <c-w><bar> :vsplit <cr>

" Don't move when you use *
nnoremap <silent> * :let stay_star_view = winsaveview()<cr>*:call winrestview(stay_star_view)<cr>

" Keep search matches in the middle of the window.
nnoremap n nzzzv
nnoremap N Nzzzv

:nnoremap <F8> a---------- <esc>"=strftime("%a %Y-%b-%d")<CR>pa ----------<CR><esc>
:inoremap <F8> ---------- <C-R>=strftime("%a %Y-%b-%d")<CR> ----------<CR>

nnoremap <silent> <Space> @=(foldlevel('.')?'za':"\<Space>")<CR>
vnoremap <Space> zf
hi Visual term=reverse cterm=reverse guibg=Grey

set background=light
set pastetoggle=<f12>
au InsertLeave * set nopaste

set hlsearch

set ruler
set wildmenu
set wildmode=longest,list

" Highlight Word {{{
"
" This mini-plugin provides a few mappings for highlighting words temporarily.
"
" Sometimes you're looking at a hairy piece of code and would like a certain
" word or two to stand out temporarily.  You can search for it, but that only
" gives you one color of highlighting.  Now you can use <leader>N where N is
" a number from 1-6 to highlight the current word in a specific color.

function! HiInterestingWord(n) " {{{
    " Save our location.
    normal! mz

    " Yank the current word into the z register.
    normal! "zyiw

    " Calculate an arbitrary match ID.  Hopefully nothing else is using it.
    let mid = 86750 + a:n

    " Clear existing matches, but don't worry if they don't exist.
    silent! call matchdelete(mid)

    " Construct a literal pattern that has to match at boundaries.
    let pat = '\V\<' . escape(@z, '\') . '\>'

    " Actually match the words.
    call matchadd("InterestingWord" . a:n, pat, 1, mid)

    " Move back to our original location.
    normal! `z
endfunction " }}}

" Mappings {{{

nnoremap <silent> <leader>1 :call HiInterestingWord(1)<cr>
nnoremap <silent> <leader>2 :call HiInterestingWord(2)<cr>
nnoremap <silent> <leader>3 :call HiInterestingWord(3)<cr>
nnoremap <silent> <leader>4 :call HiInterestingWord(4)<cr>
nnoremap <silent> <leader>5 :call HiInterestingWord(5)<cr>
nnoremap <silent> <leader>6 :call HiInterestingWord(6)<cr>

" }}}
" Default Highlights {{{

hi def InterestingWord1 guifg=#000000 ctermfg=16 guibg=#ffa724 ctermbg=214
hi def InterestingWord2 guifg=#000000 ctermfg=16 guibg=#aeee00 ctermbg=154
hi def InterestingWord3 guifg=#000000 ctermfg=16 guibg=#8cffba ctermbg=121
hi def InterestingWord4 guifg=#000000 ctermfg=16 guibg=#b88853 ctermbg=137
hi def InterestingWord5 guifg=#000000 ctermfg=16 guibg=#ff9eb8 ctermbg=211
hi def InterestingWord6 guifg=#000000 ctermfg=16 guibg=#ff2c4b ctermbg=195

" }}}

" Enable syntax highlighting when buffers were loaded through :bufdo, which
" disables the Syntax autocmd event to speed up processing.
augroup EnableSyntaxHighlighting
    " Filetype processing does happen, so we can detect a buffer initially
    " loaded during :bufdo through a set filetype, but missing b:current_syntax.
    " Also don't do this when the user explicitly turned off syntax highlighting
    " via :syntax off.
    " Note: Must allow nesting of autocmds so that the :syntax enable triggers
    " the ColorScheme event. Otherwise, some highlighting groups may not be
    " restored properly.
    autocmd! BufWinEnter * nested if exists('syntax_on') && ! exists('b:current_syntax') && ! empty(&l:filetype) | syntax enable | endif

    " The above does not handle reloading via :bufdo edit!, because the
    " b:current_syntax variable is not cleared by that. During the :bufdo,
    " 'eventignore' contains "Syntax", so this can be used to detect this
    " situation when the file is re-read into the buffer. Due to the
    " 'eventignore', an immediate :syntax enable is ignored, but by clearing
    " b:current_syntax, the above handler will do this when the reloaded buffer
    " is displayed in a window again.
    autocmd! BufRead * if exists('syntax_on') && exists('b:current_syntax') && ! empty(&l:filetype) && index(split(&eventignore, ','), 'Syntax') != -1 | unlet! b:current_syntax | endif
augroup END

" This should be the last line
filetype plugin indent on

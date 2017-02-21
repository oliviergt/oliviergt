#!/usr/bin/python

import sys

class Setup(object):

  def InstallVim(self):
    CreateDirs([
        '~/.vim/autoload',
        '~/.vim/bundle',
        '~/.vim/tmp/backup',
        '~/.vim/tmp/swap'
        ])
    RunCommands([
        'curl -LSso ~/.vim/autoload/pathogen.vim https://tpo.pe/pathogen.vim'
        ])
    EnsureConfigLines(
        '~/.vimrc',
        ['execute pathogen#infect()',
         'source ~/oliviergt/configs/vim/config.vim'
        ])



if __name__ == '__main__':
  print sys.argv[0]

#!/usr/bin/python3

import os
import os.path
import shlex
import subprocess
import sys

def CreateDirs(dir_list):
  for path in dir_list:
    path = os.path.expanduser(path)
    if not os.path.exists(path):
      print('Created directory %s' % path)
      os.makedirs(path)


def RunCommands(cmd_list):
  for cmd in cmd_list:
    args = [os.path.expanduser(token) for token in shlex.split(cmd)]
    print('Running command %s'
          % ' '.join(shlex.quote(token) for token in args))
    subprocess.check_call(args)
    # Will throw on nonzero return code.


def Install(package_list):
  RunCommands(['sudo apt-get install %s' % ' '.join(package_list)])


def EnsureConfigLines(path, config_lines):
  """Add config_lines to the end of the file 'path'.

  If any config_line is already present in the file, a duplicate will not be
  added.
  """
  path = os.path.expanduser(path)
  config_lines = [line.rstrip() for line in config_lines]
  present_lines = {config_line: False for config_line in config_lines}
  current_content = []
  if os.path.exists(path):
    f = open(path)
    for line in f:
      line = line.strip()
      current_content.append(line)
      if line in present_lines:
        present_lines[line] = True
    f.close()
  print('Updating config file %s' % path)
  f = open(path, 'w')
  for line in current_content:
    f.write('%s\n' % line)
  for line in config_lines:
    if not present_lines[line]:
      print(line)
      f.write('%s\n' % line)
  f.close()

 
class Setup(object):
  def __init__(self):
    os.chdir(os.path.expanduser('~'))

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

  def InstallTmux(self):
    Install(['tmux'])
    EnsureConfigLines(
        '~/.tmux.conf',
        ['source-file ~/oliviergt/configs/tmux'])

  def InstallBash(self):
    EnsureConfigLines(
        '~/.bashrc',
        ['source %s' % os.path.expanduser('~/oliviergt/configs/bash')])

  def InstallSecret(self):
    Install(['gnupg'])
    RunCommands([
        'gpg --output ~/secret.tgz -d ~/oliviergt/configs/secret.tgz.gpg',
        'tar -xzvf ~/secret.tgz',
        'rm ~/secret.tgz'])

  def InstallGit(self):
    RunCommands(['cp --no-clobber ~/secret/gitconfig ~/.gitconfig'])

  def InstallAll(self):
    self.InstallVim()
    self.InstallTmux()
    self.InstallBash()
    self.InstallSecret()
    self.InstallGit()


if __name__ == '__main__':
  setup = Setup()
  setup.InstallAll()

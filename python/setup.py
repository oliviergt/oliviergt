#!/usr/bin/env python3

import os
import os.path
import shlex
import stat
import subprocess
import sys


RED = '\033[31m'
BLUE = '\033[34m'


def Print(color, text):
  print('%s%s\033[0m' % (color, text))


def CreateDirs(dir_list):
  for path in dir_list:
    path = os.path.expanduser(path)
    if not os.path.exists(path):
      Print(BLUE, 'Created directory %s' % path)
      os.makedirs(path)


def RunCommands(cmd_list):
  for cmd in cmd_list:
    args = [os.path.expanduser(token) for token in shlex.split(cmd)]
    Print(BLUE, 'Running command %s'
          % ' '.join(shlex.quote(token) for token in args))
    subprocess.check_call(args)
    # Will throw on nonzero return code.


def Install(package_list):
  RunCommands(['sudo apt-get -q=2 --yes install %s' % ' '.join(package_list)])


def MakePrivate(path):
  Print(BLUE, 'Making private %s' % path)
  for (dirpath, dirnames, filenames) in os.walk(os.path.expanduser(path)):
    for filename in filenames:
      fullname = os.path.join(dirpath, filename)
      print(fullname)
      os.chmod(fullname, stat.S_IRUSR | stat.S_IWUSR)


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
  Print(BLUE, 'Updating config file %s' % path)
  f = open(path, 'w')
  for line in current_content:
    f.write('%s\n' % line)
  for line in config_lines:
    if not present_lines[line]:
      print(line)
      f.write('%s\n' % line)
  f.close()


class Passwords(object):

  def __init__(self):
    Print(BLUE, 'Reading passwords')
    self.passwords = {}
    f = open(os.path.expanduser('~/secret/passwords'))
    for line in f:
      line = line.strip()
      key, password = line.split(':')
      self.passwords[key.strip()] = password.strip()
      print(key)

  def Get(self, key):
    return self.passwords[key]

 
class Setup(object):
  def __init__(self, passwords=None):
    self.passwords = passwords
    self.home = os.path.expanduser('~')
    setup_path = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
    # Absolute path to the git root
    # (setup.py is in $abs_git_root/configs/setup.py).
    self.abs_git_root = os.path.dirname(setup_path)
    # Relative path (starting with ~).
    self.rel_git_root = os.path.join(
        '~', os.path.relpath(self.abs_git_root, self.home))

  def AptUpdate(self):
    RunCommands(['sudo apt-get -q=2 --yes update'])

  def InstallUtilities(self):
    Install(['unzip', 'psmisc'])

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
         'source %s' % os.path.join(self.rel_git_root, 'configs/vim/config.vim')
        ])

  def InstallTmux(self):
    Install(['tmux'])
    EnsureConfigLines(
        '~/.tmux.conf',
        ['source-file %s' % os.path.join(self.rel_git_root, 'configs/tmux')])

  def InstallBash(self):
    EnsureConfigLines(
        '~/.bashrc',
        ['source %s' % os.path.join(self.abs_git_root, 'configs/bash')])

  def InstallSecret(self):
    Install(['gnupg'])
    if not os.path.exists(os.path.expanduser('~/secret')):
      RunCommands([
          'gpg --output ~/secret.tgz -d %s' %
              os.path.join(self.abs_git_root, 'configs/secret.tgz.gpg'),
          'tar -xzvf ~/secret.tgz --directory ~',
          'rm ~/secret.tgz'])
    MakePrivate('~/secret')

  def InstallGit(self):
    RunCommands(['cp --no-clobber ~/secret/gitconfig ~/.gitconfig'])

  def InstallVnc(self):
    Install(['x11vnc', 'xvfb', 'xfce4', 'krdc', 'midori', 'evince'])
    CreateDirs(['~/.vnc'])
    RunCommands(['cp --no-clobber ~/secret/vnc_passwd ~/.vnc/passwd'])

  def InstallTws(self):
    name = 'tws-latest-standalone-linux-x64.sh'
    install_dir = '~/installers'
    destination = os.path.join(install_dir, name)
    CreateDirs([install_dir])
    if not os.path.exists(destination):
      RunCommands([
          'curl -Sso %s https://download2.interactivebrokers.com/installers/'
              'tws/latest-standalone/%s' % (destination, name),
          'chmod u+x %s' % destination])

  def InstallIbController(self):
    name = 'IBController-3.2.0.zip'
    install_dir = '~/installers'
    ibcontroller_dir = '~/ibcontroller'
    zip_path = os.path.join(install_dir, name)
    CreateDirs([install_dir, ibcontroller_dir])
    if not os.path.exists(zip_path):
      RunCommands([
          'curl -LSso %s https://github.com/ib-controller/ib-controller/'
              'releases/download/3.2.0/%s' % (zip_path, name)])
    RunCommands(['unzip %s  -d %s' % (zip_path, ibcontroller_dir)])
    
  def InstallAddAptRepository(self):
    """Install the add-apt-repository command-line tool."""
    RunCommands(['sudo apt-get install software-properties-common'])

  def InstallJava8(self):
    """This works for ubuntu but not debian."""
    RunCommands([
        'sudo add-apt-repository ppa:webupd8team/java',
        'sudo apt-get update',
        'sudo apt-get install oracle-java8-installer'])

  def InstallBazel(self):
    bazel_key = 'bazel-release.pub.gpg'
    bazel_key_path = os.path.join('~/installers', bazel_key)
    bazel_list_src = os.path.join(self.abs_git_root, 'configs/bazel.list')
    RunCommands(
        ['sudo cp %s /etc/apt/sources.list.d/bazel.list' % bazel_list_src,
         'curl -LSso %s https://bazel.build/%s' % (
             bazel_key_path, bazel_key),
         'sudo apt-key add %s' % bazel_key_path,
         'sudo apt-get update',
         'sudo apt-get install bazel',
         'sudo apt-get upgrade bazel'])

  def InstallAll(self):
    self.InstallUtilities()
    self.InstallVim()
    self.InstallTmux()
    self.InstallBash()
    self.InstallGit()
    self.InstallAddAptRepository()
    self.InstallJava8()
    self.InstallBazel()
    self.InstallVnc()
    self.InstallTws()
    self.InstallIbController()


if __name__ == '__main__':
  setup = Setup()
  setup.AptUpdate()
  setup.InstallSecret()
  passwords = Passwords()
  setup = Setup(passwords)
  setup.InstallAll()

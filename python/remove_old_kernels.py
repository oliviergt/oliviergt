#!/usr/bin/python

import re
import subprocess
import sys

def GetPackages():
  p = subprocess.Popen(['/usr/bin/dpkg-query',
                        '--show',
                        '--showformat=${db:Status-Abbrev}\t${binary:Package}\n',
                        'linux-*'],
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE)
  out, err = p.communicate()

  returncode = 0
  if err:
    print 'remove_old_kernels: call to dpkg failed'
    print err
    returncode = 1

  if p.returncode:
    print 'remove_old_kernels: dpkg returned error code %s' % p.returncode
    returncode = p.returncode

  if returncode:
    sys.exit(returncode)

  for line in out.split('\n'):
    line = line.strip()
    if line.startswith('ii'):
      package = line.split('\t')[1]
      yield package


def GetCurrentKernelRelease():
  p = subprocess.Popen(['/bin/uname', '-r'],
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE)
  out, err = p.communicate()

  returncode = 0
  if err:
    print 'remove_old_kernels: call to uname failed'
    print err
    returncode = 1

  if p.returncode:
    print 'remove_old_kernels: uname returned error code %s' % p.returncode
    returncode = p.returncode

  if returncode:
    sys.exit(returncode)

  return out.strip()


class Version(object):

  def __init__(self, version_number, prefix, suffix):
    self.version_number = version_number
    self.prefix = prefix
    self.suffix = suffix


def GetVersion(s):
  """Extract version numbers from a string. For example:
  linux-image-3.13.0-70-generic -> [3, 13, 0, 70].
  Return None if no version was found.
  """
  match = re.search('[0-9][0-9.-]*[0-9]', s)
  if not match:
    return None
  version_string = match.group(0)
  prefix = s[:match.start(0)]
  suffix = s[match.start(0):]
  version_number = [int(v) for v in re.split('[.-]', version_string)]
  if len(version_number) < 3:
    # Just a number or two in the package name doesn't make it
    # a version_number.
    return None
  return Version(version_number, prefix, suffix)


def SortKey(s):
  result = GetVersion(s)
  if not result:
    return s
  return result.version_number + [s]

release = GetCurrentKernelRelease()
current_version_number = GetVersion(release).version_number
print 'Current kernel: %s -> %s' % (release, current_version_number)
all_packages = [package for package in GetPackages()]
all_packages.sort(key=SortKey)
previous_version_number = None
for package in all_packages:
  version = GetVersion(package)
  if not version or version.version_number >= current_version_number:
    continue
  if previous_version_number is None:
    previous_version_number = version.version_number
  # The previous version is the greatest version before the current one.
  previous_version_number = max(version.version_number, previous_version_number)

prefix_width = 0
suffix_width = 0
for package in all_packages:
  version = GetVersion(package)
  if not version:
    prefix_width = max(prefix_width, len(package))
    continue
  prefix_width = max(prefix_width, len(version.prefix))
  suffix_width = max(suffix_width, len(version.suffix))
  
format_string = (
    '[%s] %' + str(prefix_width) + 's%-' + str(suffix_width) + 's: %s')
to_remove = []

for package in all_packages:
  version = GetVersion(package)
  if version:
    p = version.prefix
    s = version.suffix
  else:
    p = package
    s = ''
  if not version:
    print format_string % (' Keep ', p, s, 'no version number')
    continue
  if version.version_number == current_version_number:
    print format_string % (' Keep ', p, s, 'the current version')
    continue
  if version.version_number > current_version_number:
    print format_string % (' Keep ', p, s, 'a more recent version')
    continue
  if version.version_number == previous_version_number:
    print format_string % (' Keep ', p, s, 'the previous version')
    continue
  print format_string % ('Remove', p, s, 'an older version')
  to_remove.append(package)

if to_remove:
  command = ['/usr/bin/sudo', '/usr/bin/apt-get', '-y', 'purge'] + to_remove
  print 'Running %s' % (' '.join(command))
  p = subprocess.Popen(command,
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE)
  out, err = p.communicate()
  print out

  returncode = 0
  if err:
    print 'remove_old_kernels: call to sudo apt-get failed'
    print err
    returncode = 1

  if p.returncode:
    print 'remove_old_kernels: sudo apt-get returned error code %s' % p.returncode
    returncode = p.returncode

  if returncode:
    sys.exit(returncode)

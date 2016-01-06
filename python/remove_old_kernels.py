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

  if err:
    print 'remove_old_kernels: call to dpkg failed'
    print err
    sys.exit(1)

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

  if err:
    print 'remove_old_kernels: call to uname failed'
    print err
    sys.exit(1)

  return out.strip()


def GetVersion(s):
  """Extract version numbers from a string. For example:
  linux-image-3.13.0-70-generic -> [3, 13, 0, 70].
  Return None if no version was found.
  """
  match = re.search('[0-9][0-9.-]*[0-9]', s)
  if not match:
    return None
  version_string = match.group(0)
  version = [int(v) for v in re.split('[.-]', version_string)]
  if len(version) < 3:
    # Just a number or two in the package name doesn't make it
    # a version number.
    return None
  return version


release = GetCurrentKernelRelease()
current_version = GetVersion(release)
print 'Current kernel: %s -> %s' % (release, current_version)
prior_packages = []
previous_version = None
for package in GetPackages():
  version = GetVersion(package)
  if not version:
    print 'Keeping %s: no version number' % package
    continue
  if version == current_version:
    print 'Keeping %s: the current version' % package
    continue
  if version > current_version:
    print 'Keeping %s: a more recent version' % package
    continue
  prior_packages.add(package)
  if previous_version is None:
    previous_version = version
  # The previous version is the greatest version before the current one.
  previous_version = max(version, previous_version)

for package in prior_packages:
  version = GetVersion(package)
  if version == previous_version:
    print 'Keeping %s: the previous version' % package
    continue
  print 'Will remove %s: an older version' % package

  






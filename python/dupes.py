from datetime import datetime
from datetime import timedelta
import argparse
import md5
import os
import shutil
import subprocess
import sys
import time

MD5SUM = '/usr/bin/md5sum'


class Status(object):
  def __init__(self):
    self.last_refresh_time = time.time()
    self.last_line_length = 0

  def Print(self, s):
    spaces = ''
    if len(s) < self.last_line_length:
      spaces = ' ' * (self.last_line_length - len(s))
    print '\r|%s|%s' % (s, spaces)
    sys.stdout.flush()
    self.last_line_length = 0

  def Flash(self, s):
    spaces = ''
    if len(s) < self.last_line_length:
      spaces = ' ' * (self.last_line_length - len(s))
    print '\r|%s|%s' % (s, spaces),
    sys.stdout.flush()
    self.last_line_length = len(s)


class FileStats(object):
  def __init__(self, md5hash, size, timestamp):
    self.md5hash = md5hash
    self.size = int(size)
    self.timestamp = int(timestamp)

  def GetHash(self):
    '''This may be None if we don't have read access.'''
    return self.md5hash

  def GetSize(self):
    return self.size

  def GetTimestamp(self):
    return self.timestamp

  def ToString(self):
    return '%s %s %s' % (self.md5hash, self.size, self.timestamp)


class Cache(object):
  '''Maintains a cache of file statistics (md5hash, file size, and timestamp).
  An entry becomes stale if a file's size and timestamp don't match the
  cache entry anymore. The cache auto-saves every 5 minutes, to help recover
  from crashes.
  '''
  def __init__(self, cache_filename):
    self.cache = {}
    self.hash_count = 0
    self.cache_filename = cache_filename
    try:
      f = open(cache_filename, 'r')
    except IOError:
      return
    for line in f:
      tokens = line.split(' ', 3)
      md5hash = tokens[0]
      size = tokens[1]
      timestamp = tokens[2]
      filename = tokens[3][:-1]
      self.cache[filename] = FileStats(md5hash, size, timestamp)
    f.close()
    self.last_save_time = time.time()

  def GetFileStats(self, path):
    if time.time() > self.last_save_time + 5 * 60:
      self.Save()
    stat = os.stat(path)
    timestamp = int(stat.st_mtime)
    size = stat.st_size

    if path in self.cache:
      file_stats = self.cache[path]
      if timestamp == file_stats.GetTimestamp():
        if size == file_stats.GetSize():
          return file_stats

    self.hash_count += 1
    new_stats = FileStats(HashFile(path), size, timestamp)
    self.cache[path] = new_stats
    return new_stats

  def Save(self):
    f = open(self.cache_filename, 'w')
    for filename in sorted(self.cache):
      f.write('%s %s\n' % (self.cache[filename].ToString(), filename))
    f.close()
    self.last_save_time = time.time()

  def GetHashCount(self):
    return self.hash_count
      

class Aggregate(object):
  """Represents aggregate information about a file or folder.

  This includes hash, total size, number of files, and a list of
  paths (multiple paths if the file or folder with this hash is
  duplicated).
  """
  def __init__(self, size, file_count):
    self.size = size
    self.file_count = file_count
    self.paths = set()

  def AddPath(self, path):
    self.paths.add(path)

  def GetFileCount(self):
    return self.file_count

  def GetSize(self):
    return self.size

  def GetPaths(self):
    return self.paths

  def Implies(self, candidate):
    '''Returns true if the present aggregate implies the candidate aggregate.
    For example, if the present aggregate has paths a/b and c/d, and the
    candidate has paths a/b/x and a/b/y, then the candidate is implied.
    '''
    for candidate_path in candidate.GetPaths():
      if not self.HasPrefixForPath(candidate_path):
        return False
    return True

  def HasPrefixForPath(self, candidate_path):
    for path in self.GetPaths():
      if IsPathPrefix(path, candidate_path):
        return True
    return False

  def SomePathMatches(self, substring):
    for path in self.GetPaths():
      if path.find(substring) >= 0:
        return True
    return False


def IsPathPrefix(prefix, path):
  '''Returns true if prefix is prefix of path, in the sense of a filesystem
  path. Please note: 'a' is not a prefix for 'ab', but would be a prefix for
  'a/b', where '/' is the OS path delimiter. Also notice the prefix could be
  longer than the path, for example 'a/' is consider a prefix for 'a'.
  '''
  while prefix.endswith(os.sep):
    prefix = prefix[:-1]
  while path.endswith(os.sep):
    path = path[:-1]
  if prefix == path:
    return True
  return path.startswith(prefix + os.sep)


def Call(args):
  process = subprocess.Popen(args, stdout=subprocess.PIPE)
  return [line for line in process.stdout]


def HashFile(filename):
  '''Returns md5 hash of the file, or None if there was an error.
  For example, the current user may not have permission to read the
  file.
  '''
  output_lines = Call([MD5SUM, filename])
  if len(output_lines) != 1:
    print 'Could not hash %s' % filename
    return None
  tokens = output_lines[0].split(' ')
  if len(tokens) < 1:
    print 'No space in output lines when hashing %s:\n%s' % (
        filename, output_lines[0])
    return None
  return tokens[0]


def IsImplied(aggregate, collection):
  '''Returns true if aggregate is already implied by the provided collection
  of aggregates. For example, the aggregate is already in the collection,
  or, more generally, there is a collection item such that each path in the 
  considered aggregate is a sub-path of the collection item.
  '''
  for item in collection:
    if item.Implies(aggregate):
      return True
  return False

class DefaultSelector(object):
  def Matches(self, aggregate):
    return True

  def Print(self, aggregate):
    print '%s files, %s bytes' % (
        aggregate.GetFileCount(), aggregate.GetSize())
    for path in sorted(aggregate.GetPaths()):
      print '  %s' % path


class GoldenDeleteSelector(object):
  def __init__(self, golden_args, delete_args):
    # Bug: This only works when golden_args and delete_args are absolute paths.
    # The prefix comparison doesn't attempt to make the local path absolute.
    self.golden_args = golden_args
    self.delete_args = delete_args

  def IsGolden(self, path):
    for golden_path in self.golden_args:
      if IsPathPrefix(golden_path, path):
        return True
    return False

  def IsDelete(self, path):
    for delete_path in self.delete_args:
      if IsPathPrefix(delete_path, path):
        return True
    return False

  def Matches(self, aggregate):
    golden_paths = []
    delete_paths = []
    for path in aggregate.GetPaths():
      is_golden = self.IsGolden(path)
      is_delete = self.IsDelete(path)
      if is_golden and is_delete:
        # Should probably check for this right after argument parsing; don't
        # walk the tree if there is an overlap between golden and delete.
        return False
      if is_golden:
        golden_paths.append(path)
      if is_delete:
        delete_paths.append(path)
    if not delete_paths:
      return False
    if not golden_paths:
      return False
    return True

  def Print(self, aggregate):
    golden_paths = []
    delete_paths = []
    for path in aggregate.GetPaths():
      is_golden = self.IsGolden(path)
      is_delete = self.IsDelete(path)
      if is_golden:
        golden_paths.append(path)
      if is_delete:
        delete_paths.append(path)
    for path in sorted(golden_paths):
      print '# %s' % path
    for path in sorted(delete_paths):
      print '/usr/bin/gvfs-trash %s' % self.ShellQuote(path)

  @staticmethod
  def ShellQuote(s):
    return "'" + s.replace("'", "'\\''") + "'"

     

def Main(path_args, golden_args, delete_args):
  if not path_args:
    path_args = []
  if not golden_args:
    golden_args = []
  if not delete_args:
    delete_args = []
  all_args = path_args + golden_args + delete_args

  # Only two modes: identify duplicates, or delete files not present in golden.
  if path_args and (golden_args or delete_args):
    print 'Cannot use positional paths together with --golden or --delete.'
    sys.exit(1)
  if golden_args and not delete_args:
    print 'Must use --delete with --golden.'
    sys.exit(1)
  if delete_args and not golden_args:
    print 'Must use --golden with --delete.'
    sys.exit(1)
  if golden_args:
    selector = GoldenDeleteSelector(golden_args, delete_args)
  else:
    selector = DefaultSelector()

  status = Status()
  cache = Cache('/home/gl/.dupes/cache.txt')
  files = []
  directories = set()

  # First pass: Gather statistics on files and directories.
  for path_argument in all_args:
    if os.path.isdir(path_argument):
      for root, folders, regular_files in os.walk(path_argument, topdown=False):
        for filename in regular_files:
          filename = os.path.join(root, filename)
          if os.path.islink(filename):
            continue
          files.append(filename)
        for dir_name in folders:
          full_dir_name = os.path.join(root, dir_name)
        directories.add(root)
    else:
      files.append(path_argument)

  status.Print('%s files in %s directories' % (len(files), len(directories)))

  # Second pass: actual hashing.
  aggregates = {}
  dir_name_to_hash = {}
  for path_argument in all_args:
    if os.path.isdir(path_argument):  # TODO: handle the else case
      for root, folders, regular_files in os.walk(path_argument, topdown=False):
        status.Flash('Hashing %s' % root)
        if root in dir_name_to_hash:
          # Bug: If a path appears twice in all_args, the following line
          # incorrectly raises an exception.
          raise Exception('%s should not have been visited previously' % root)
        sub_hashes = []
        root_size = 0
        file_count = 0
        cannot_hash = False
        for filename in regular_files:
          filename = os.path.join(root, filename)
          if os.path.islink(filename):
            continue
          file_stats = cache.GetFileStats(filename)
          file_hash = file_stats.GetHash()
          if not file_hash:
            status.Print('Skipping file %s' % filename)
            cannot_hash = True
            continue
          file_size = file_stats.GetSize()
          sub_hashes.append(file_hash)
          root_size += file_size
          file_count += 1
          # print '%s %s' % (file_hash, repr(filename))
          if file_hash in aggregates:
            aggregates[file_hash].AddPath(filename)
          else:
            aggregate = Aggregate(file_size, 1)
            aggregate.AddPath(filename)
            aggregates[file_hash] = aggregate

        for dir_name in folders:
          full_dir_name = os.path.join(root, dir_name)
          if os.path.islink(full_dir_name):
            continue
          if full_dir_name not in dir_name_to_hash:
            # For example, the user doesn't have permission to list
            # the directory. This makes it impossible the to compute
            # a hash for the chain of parents.
            status.Print('Skipping directory %s' % full_dir_name)
            cannot_hash = True
            continue
          subdir_hash = dir_name_to_hash[full_dir_name]
          sub_hashes.append(subdir_hash)
          subdir_aggregate = aggregates[subdir_hash]
          file_count += subdir_aggregate.GetFileCount()
          root_size += subdir_aggregate.GetSize()

        if cannot_hash:
          # A subdirectory was skipped, so we cannot reliably compute
          # a hash for the root directory.
          continue
        root_md5 = md5.new()
        for sub_hash in sorted(sub_hashes):
          root_md5.update(sub_hash)
        root_hash = '/' + root_md5.hexdigest()
        dir_name_to_hash[root] = root_hash

        if root_hash in aggregates:
          if root_size != aggregates[root_hash].GetSize():
            status.Print('%s, %s: size mismath %s != %s' % (
                root_hash, root, root_size, aggregates[root_hash].GetSize()))
            for path in aggregates[root_hash].GetPaths():
              status.Print('  %s' % path)
            sys.exit(1)

          aggregates[root_hash].AddPath(root)
        else:
          aggregate = Aggregate(root_size, file_count)
          aggregate.AddPath(root)
          aggregates[root_hash] = aggregate

  status.Print('%s unique aggregates' % len(aggregates))

  sorted_aggr = sorted(aggregates.values(), key=Aggregate.GetSize, reverse=True)

  count = 0
  printed_aggregate = []
  for aggregate in sorted_aggr:
    if len(aggregate.GetPaths()) < 2:
      continue
    if not selector.Matches(aggregate):
      continue
    if IsImplied(aggregate, printed_aggregate):
      # Think hard whether this really works with golden-delete selector.
      continue
    printed_aggregate.append(aggregate)
    selector.Print(aggregate)
    print
    count += 1
    # if count >= 500:
    #  break

  cache.Save()
  status.Print('Computed %d hashes' % cache.GetHashCount())
  
  sys.exit(0)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Find duplicate files')
  parser.add_argument('paths', metavar='path', nargs='*',
      help='a search path that should be explored')
  parser.add_argument('--golden', metavar='path', nargs='+',
      help=('a list of golden paths; a file will only be deleted if there is '
            'a duplicate copy of it in the golden repository'))
  parser.add_argument('--delete', metavar='path', nargs='+',
      help=('a list of paths; a file in a the delete tree will only be deleted '
            'if there is a duplicate copy of it in the golden subtree'))
  
  args = parser.parse_args()
  Main(args.paths, args.golden, args.delete)

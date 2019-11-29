#!/usr/bin/python
from datetime import datetime
from datetime import timedelta
import argparse
import md5
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time


MD5SUM = [
  ['md5sum'],   # GNU-style
  ['md5', '-r'] # BSD-style
]

def GetConsoleWidth():
  tokens = os.popen('stty size', 'r').read().split()
  if len(tokens) < 2:
    return None
  return int(tokens[1])


class InteractiveConsole(object):
  def __init__(self):
    self.last_refresh_time = time.time()

  def Print(self, s=''):
    print '\033[K%s' % s
    sys.stdout.flush()
    self.last_refresh_time = time.time()

  def Error(self, s):
    print '\033[K\033[91m%s\033[0m' % s
    sys.stdout.flush()
    self.last_refresh_time = time.time()

  def Flash(self, s):
    now = time.time()
    if now < self.last_refresh_time + 1:
      return
    width = GetConsoleWidth()
    if len(s) > width:
      b1 = width / 2 - 1
      b2 = b1 + 3 + len(s) - width
      s = s[:b1] + '...' + s[b2:]
    print '\033[K%s\r' % s,
    sys.stdout.flush()
    self.last_refresh_time = now


class RedirectedConsole(object):
  def __init__(self):
    self.last_refresh_time = time.time()

  def Print(self, s=''):
    print '<info> %s' % s
    self.last_refresh_time = time.time()

  def Error(self, s):
    print '<error> %s' % s
    self.last_refresh_time = time.time()

  def Flash(self, s):
    now = time.time()
    if now < self.last_refresh_time + 1:
      return
    print '%s' % s
    self.last_refresh_time = now


class FileStats(object):
  def __init__(self, path, base_name, md5hash, size, timestamp_seconds):
    self.path = path
    self.base_name = base_name
    self.md5hash = md5hash
    self.size = size
    self.timestamp_seconds = timestamp_seconds

  def GetPath(self):
    return self.path

  def GetBaseName(self):
    return self.base_name

  def GetHash(self):
    return self.md5hash

  def GetSize(self):
    return self.size

  def GetTimestampSeconds(self):
    return self.timestamp_seconds

  def __str__(self):
    return '%s %s %s %s %s' % (
        self.GetPath(),
        self.GetBaseName(),
        self.GetHash(),
        self.GetSize(),
        self.GetTimestampSeconds())


class FileStatsRepository(object):

  def __init__(self, database_filename):
    directory, base_name = os.path.split(database_filename)
    if not os.path.exists(directory):
      os.makedirs(directory)
    self.connection = sqlite3.connect(database_filename)

  def CreateTable(self):
    cursor = self.connection.cursor()
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS file_stats (path text, base_name text, '
        'md5hash text, size integer, timestamp_seconds integer, '
        'PRIMARY KEY (path, base_name))')
    self.connection.commit()

  def Close(self):
    self.connection.close()

  def Upsert(self, file_stats):
    cursor = self.connection.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO file_stats VALUES (?,?,?,?,?)',
        (file_stats.GetPath(),
         file_stats.GetBaseName(),
         file_stats.GetHash(),
         file_stats.GetSize(),
         file_stats.GetTimestampSeconds()))
    self.connection.commit()

  def Get(self, path, base_name):
    cursor = self.connection.cursor()
    cursor.execute(
        'SELECT * FROM file_stats WHERE path=? and base_name=?',
        (path, base_name))
    row = cursor.fetchone()
    if not row:
      return None
    return self.MakeFileStats(row)

  def Lookup(self, md5hash, size):
    cursor = self.connection.cursor()
    cursor.execute(
        'SELECT * FROM file_stats WHERE md5hash=? and size=?',
        (md5hash, size))
    result = []
    for row in cursor.fetchall():
      result.append(self.MakeFileStats(row))
    return result

  def MakeFileStats(self, row):
    return FileStats(row[0], row[1], row[2], row[3], row[4])

  def FilePathMatch(self, name_like):
    cursor = self.connection.cursor()
    cursor.execute(
        'SELECT * FROM file_stats WHERE path || "/" || base_name LIKE ?',
        (name_like,))
    result = []
    for row in cursor.fetchall():
      result.append(self.MakeFileStats(row))
    return result


def Call(args):
  process = subprocess.Popen(
      args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  return [line for line in process.stdout], [line for line in process.stderr]


def HashFile(filename, console):
  '''Returns md5 hash of the file, or None if there was an error.
  For example, the current user may not have permission to read the
  file.
  '''
  success = False
  global MD5SUM
  for md5sum_command in MD5SUM:
    try:
      output_lines, err_lines = Call(md5sum_command + [filename])
      success = True
      break
    except OSError:
      pass
  if not success:
    raise Exception('Did not find md5 command')
  MD5SUM = [md5sum_command]
  if len(output_lines) != 1:
    err = err_lines[0].replace(filename, '').strip()
    console.Error('Could not hash %s: %s' % (filename, err))
    return None
  tokens = output_lines[0].split(' ')
  if len(tokens) < 1:
    console.Print('No space in output lines when hashing %s:\n%s' % (
        filename, output_lines[0]))
    return None
  return tokens[0]


class TreeWalker(object):

  def __init__(self, console):
    self.console = console
    self.exclusion_patterns = [
        re.compile('/\.AppleDouble/'),
        re.compile('\.swp$'),
        re.compile('\.~lock\.'),
        re.compile('/\.DS_Store$'),
        ]

  def IsExcluded(self, filename):
    for pattern in self.exclusion_patterns:
      if pattern.search(filename):
        return True
    return False

  def Utf8Decode(self, s):
    try:
      return s.decode('utf8')
    except UnicodeDecodeError, e:
      self.console.Print('Not an utf8 filename: %s' % repr(s))
    return None

  def MakeAcceptableFile(self, filename):
    if os.path.islink(filename):
      return None
    filename = self.Utf8Decode(filename)
    if not filename:
      return None
    if self.IsExcluded(filename):
      return None
    return filename

  def Walk(self, paths, name, callback):
    """Processes all files / directories recursively, and calls the callback on
    each absolute filename.

    Parameters
    ----------
    paths : list of str
        Each entry can be a file or a directory. Directories will be explored
        recursively and expanded into files. If a path does not exist, it will
        be skipped (an error will be displayed).
    name: str
        Name of the operation, for the progress indicator.
    callback: function
        Function of one parameter (the absolute file name). Will be called on
        each file.
    """
    paths = [os.path.abspath(os.path.expanduser(p)) for p in paths]
    # First pass: Gather statistics on files and directories.
    files = []
    directories = set()
    for path_argument in paths:
      if not os.path.exists(path_argument):
        self.console.Error('Path %s does not exist' % path_argument)
        continue
      if not os.path.isdir(path_argument):
        files.append(path_argument)  # TODO: Do the counting right here.
        continue
      for root, folders, regular_files in os.walk(path_argument, topdown=False):
        for filename in regular_files:
          filename = self.MakeAcceptableFile(os.path.join(root, filename))
          if filename:
            files.append(filename)
            directories.add(root)
            self.console.Flash('%s: %d files, %d directories: %s' % (
                name, len(files), len(directories), root))

    # Second pass: actual processing.
    processed_directories = set()
    file_count = 0
    for path_argument in paths:
      if not os.path.exists(path_argument):
        # Error was already printed above.
        continue
      if not os.path.isdir(path_argument):
        filename = self.MakeAcceptableFile(path_argument)
        if filename:
          callback(filename)  # TODO: Do the counting right here.
        continue
      for root, folders, regular_files in os.walk(path_argument, topdown=False):
        for filename in regular_files:
          filename = self.MakeAcceptableFile(os.path.join(root, filename))
          if filename:
            file_count += 1
            self.console.Flash('%s: file %d/%d, directory %d/%d: %s' % (
                name, file_count, len(files), len(processed_directories),
                len(directories), root))
            callback(filename)
            processed_directories.add(root)


class Dupes(object):

  def  __init__(self, repository, tree_walker, console):
    self.repository = repository
    self.tree_walker = tree_walker
    self.console = console

  def HashFileToDatabase(self, filename):
    """Retrieves timestamp and size from system. If those match the database
    values, the hash from the database is returned. Otherwise, the hash is
    calculated. Returns the file stats object. Returns None if the hash
    could not be computed."""
    stat = os.stat(filename)
    timestamp_seconds = int(stat.st_mtime)
    size = stat.st_size
    path, base_name = os.path.split(filename)
    from_database = self.repository.Get(path, base_name)
    if from_database:
      if (from_database.GetTimestampSeconds() == timestamp_seconds
          and from_database.GetSize() == size):
        return from_database
    md5hash = HashFile(filename, self.console)
    if not md5hash:
      return None
    file_stats = FileStats(path, base_name, md5hash, size, timestamp_seconds)
    self.repository.Upsert(file_stats)
    return file_stats

  def HashPathsToDatabase(self, paths):
    self.tree_walker.Walk(paths, 'hash_to_database', self.HashFileToDatabase)

  def Lookup(self, paths):
    self.tree_walker.Walk(paths, 'lookup', self.LookupFile)

  def LookupFile(self, filename):
    file_stats = self.HashFileToDatabase(filename)
    matches = self.repository.Lookup(file_stats.GetHash(), file_stats.GetSize())
    for other_file_stats in matches:
      self.console.Print(os.path.join(
        other_file_stats.GetPath(), other_file_stats.GetBaseName()))
    self.console.Print()

  def NameLike(self, name_like):
    matches = self.repository.FilePathMatch(name_like)
    for file_stats in matches:
      self.console.Print(os.path.join(
        file_stats.GetPath(), file_stats.GetBaseName()))
    self.console.Print()


def Main(args):
  if GetConsoleWidth() is None:
    console = RedirectedConsole()
  else:
    console = InteractiveConsole()
  database = os.path.expanduser(args.database)
  repository = FileStatsRepository(database)
  repository.CreateTable()
  tree_walker = TreeWalker(console)
  dupes = Dupes(repository, tree_walker, console)
  if args.hash_to_database:
    dupes.HashPathsToDatabase(args.hash_to_database)
  if args.lookup:
    dupes.Lookup(args.lookup)
  if args.name_like:
    dupes.NameLike(args.name_like)
  repository.Close()
  console.Print('Updates saved to %s' % database)


if __name__ == "__main__":
  print 'HOME = %s' % os.environ['HOME']
  print '~ = %s' % os.path.expanduser('~')
  parser = argparse.ArgumentParser(
      description='Find duplicate files',
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--database', metavar='path', nargs='?',
      default='~/.dupes/dupes.db',
      help='the path to the sqlite database file')
  parser.add_argument('--hash_to_database', metavar='path', nargs='*',
      help='a search path that should be explored; hashes will be computed '
      'and added to the database')
  parser.add_argument('--lookup', metavar='path', nargs='*',
      help='a search path that should be explored; all files that match the '
      'hashes and sizes from the search path will be returned')
  parser.add_argument('--name_like', metavar='like_clause', nargs='?',
      help='find all files in repository whose full path matches the given '
      'sql LIKE clause; the search is not case-sensitive. There are two '
      'wildcard characters: the percent sign % represents zero, one or more '
      'characters, whereas the underscore _ represents a single character.')
  
  Main(parser.parse_args())

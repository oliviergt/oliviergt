from datetime import datetime
from datetime import timedelta
import argparse
import md5
import os
import re
import shutil
import subprocess
import sys
import time
import sqlite3

MD5SUM = '/usr/bin/md5sum'

class Status(object):
  def __init__(self):
    self.last_refresh_time = time.time()
    self.last_line_length = 0

  def Print(self, s):
    spaces = ''
    if len(s) < self.last_line_length:
      spaces = ' ' * (self.last_line_length - len(s))
    print '\r%s%s' % (s, spaces)
    sys.stdout.flush()
    self.last_line_length = 0

  def Flash(self, s):
    spaces = ''
    if len(s) < self.last_line_length:
      spaces = ' ' * (self.last_line_length - len(s))
    print '\r%s%s' % (s, spaces),
    sys.stdout.flush()
    self.last_line_length = len(s)


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
    result = cursor.fetchone()
    if not result:
      return None
    return FileStats(result[0], result[1], result[2], result[3], result[4])


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




class Dupes(object):

  def  __init__(self, repository, status):
    self.repository = repository
    self.status = status
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

  def HashFileToDatabase(self, filename):
    """Retrieves timestamp and size from system. If those match the database
    values, the hash from the database is returned. Otherwise, the hash is
    calculated. Returns the file stats object. Returns None if the file is
    excluded or if the hash could not be computed."""
    if self.IsExcluded(filename):
      return None

    stat = os.stat(filename)
    timestamp_seconds = int(stat.st_mtime)
    size = stat.st_size
    path, base_name = os.path.split(filename)
    from_database = self.repository.Get(path, base_name)
    if from_database:
      if (from_database.GetTimestampSeconds() == timestamp_seconds
          and from_database.GetSize() == size):
        return from_database
    md5hash = HashFile(filename)
    if not md5hash:
      return None
    file_stats = FileStats(path, base_name, md5hash, size, timestamp_seconds)
    self.repository.Upsert(file_stats)
    return file_stats

  def Utf8Decode(self, s):
    try:
      return s.decode('utf8')
    except UnicodeDecodeError, e:
      print 'Not an utf8 filename: %s' % repr(s)
    return None

  def HashPathsToDatabase(self, hash_to_database):
    hash_to_database = [os.path.abspath(os.path.expanduser(p))
                        for p in args.hash_to_database]

    # First pass: Gather statistics on files and directories.
    files = []
    directories = set()
    for path_argument in hash_to_database:
      if not os.path.isdir(path_argument):
        files.append(path_argument)
      else:
        for root, folders, regular_files in os.walk(path_argument, topdown=False):
          for filename in regular_files:
            filename = os.path.join(root, filename)
            if os.path.islink(filename):
              continue
            filename = self.Utf8Decode(filename)
            if not filename:
              continue
            if not self.IsExcluded(filename):
              files.append(filename)
              directories.add(root)

    self.status.Print('%s files in %s directories' % (len(files), len(directories)))

    # Second pass: actual hashing.
    hashed_directories = set()
    file_count = 0
    for path_argument in hash_to_database:
      if not os.path.isdir(path_argument):
        self.HashFileToDatabase(path_argument)
      else:
        for root, folders, regular_files in os.walk(path_argument, topdown=False):
          for filename in regular_files:
            filename = os.path.join(root, filename)
            if os.path.islink(filename):
              continue
            filename = self.Utf8Decode(filename)
            if not filename:
              continue
            file_count += 1
            self.status.Flash('Hashing file %d, directory %d: %s' % (
              file_count, len(hashed_directories), root))
            self.HashFileToDatabase(filename)
            hashed_directories.add(root)


def Main(args):
  status = Status()
  database = os.path.expanduser(args.database)
  repository = FileStatsRepository(database)
  repository.CreateTable()
  dupes = Dupes(repository, status)
  if args.hash_to_database:
    dupes.HashPathsToDatabase(args.hash_to_database)
  repository.Close()
  print 'Updates saved to %s' % database


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      description='Find duplicate files',
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--database', metavar='path', nargs='?',
      default='~/.dupes/dupes.db',
      help='the path to the sqlite database file')
  parser.add_argument('--hash_to_database', metavar='path', nargs='*',
      help='a search path that should be explored; hashes will be computed '
      'and added to the database')
  
  args = parser.parse_args()
  Main(args)

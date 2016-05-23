from datetime import datetime
from datetime import timedelta
import argparse
import md5
import os
import shutil
import subprocess
import sys
import time
import sqlite3


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

  def GetMd5Hash(self):
    return self.md5hash

  def GetSize(self):
    return self.size

  def GetTimestampSeconds():
    return self.timestamp_seconds


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
        'md5hash text, size integer, timestamp_seconds integer)')
    self.connection.commit()

  def Close(self):
    self.connection.close()

  def Insert(self, file_stats):
    cursor = self.connection.cursor()
    cursor.execute(
        'INSERT INTO file_stats VALUES (?,?,?,?,?)',
        (file_stats.GetPath(),
         file_stats.GetBaseName(),
         file_stats.GetMd5Hash(),
         file_stats.GetSize(),
         file_stats.GetTimestampSeconds()))
    self.connection.commit()


def Main(args):
  status = Status()
  database = os.path.expanduser(args.database)
  repository = FileStatsRepository(database)
  repository.CreateTable()
  if args.hash_to_database:
    hash_to_database = [os.path.abspath(os.path.expanduser(p))
                        for p in args.hash_to_database]

  files = []
  directories = set()

  # First pass: Gather statistics on files and directories.
  for path_argument in hash_to_database:
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

  for f in sorted(files):
    print f

  status.Print('%s files in %s directories' % (len(files), len(directories)))

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




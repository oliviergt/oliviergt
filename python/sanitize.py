# coding=utf8

import re

LETTER = (
    u'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' +
    u'ÀÁÃÊÍÒÔÙÚàáâãèéêìíòóôõùúýĂăĐđĩũƠơƯự̀́̃̉ẠạẢảẤấẦầẩẫẬậẮắằẳẵẶặẸẹẻẽẾếỀềỂểễệ' +
    u'ỉịọỏỐốỒồỔổỗộớờởỡợỤụủỨứỪừửỮữựỳỵỷỹư ̣')
LET = '[' + LETTER + ']'
NOTLET = '[^(' + LETTER + ']'

def IsLetter(c):
  return re.match(LET, c)

def Sanitize(line):
  line = line.replace('\t', ' ')
  line = re.sub(' +', ' ', line)
  line = re.sub('^ ', '', line)
  line = re.sub(' $', '', line)
  line = re.sub(' (' + NOTLET + ')', '\\1', line)
  return line


reader = open('/Users/oliviergt/Downloads/tho.txt')
writer = open('/Users/oliviergt/tho-clean.txt', 'w')
chars = set()
for line in reader:
  line = line.decode('utf8')
  for c in line:
    if not IsLetter(c):
      chars.add(c)
  writer.write(Sanitize(line).encode('utf8'))

for a in sorted(chars):
  print '%s %s' % (repr(a), a)
print ''.join(sorted(chars))

reader.close()
writer.close()


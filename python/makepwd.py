import M2Crypto
import string
import struct

LETTERS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghipqrstuvwxyz'
N = len(LETTERS)

def GetRandomSymbol():
  while True:
    b = M2Crypto.m2.rand_bytes(1)
    b = struct.unpack('B', b[0])[0]
    if b < N:
      break
  return LETTERS[b]

def GetRandomPassword():
  s = ''
  for i in xrange(4):
    s += GetRandomSymbol()
  s += '.'
  for i in xrange(4):
    s += GetRandomSymbol()
  s += '-'
  for i in xrange(5):
    s += GetRandomSymbol()
  return s


for j in xrange(100):
  print(GetRandomPassword())

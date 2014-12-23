# coding=utf8

import sanitize

import unittest

class DiacriticsTestCase(unittest.TestCase):

  def testKnownLettersShouldNotHaveCombiningMarks(self):
    for c in sanitize.LETTER:
      if ord(c) >= 0x300 and ord(c) <= 0x36F:
	self.fail('Found combining diacritics \\u%04x' % ord(c))


  def testSmallLetterOWithHornAndGrave(self):
    actual = sanitize.NormalizeCombinedCharacters(u'\u01a1\u0300')
    self.assertEqual(actual, u'\u1edd')


def suite():
  suite = unittest.makeSuite(DiacriticsTestCase, 'test')
  return suite

runner = unittest.TextTestRunner()
runner.run(suite())

import versify

import unittest

class VersifyTestCase(unittest.TestCase):

  def testGetParagraphsEmpty(self):
    self.assertEqual(versify.GetParagraphs([]), [])
    self.assertEqual(versify.GetParagraphs(['']), [])
    self.assertEqual(versify.GetParagraphs(['  \t\t\n\n  ']), [])

  def testGetParagraphsSingle(self):
    self.assertEqual(versify.GetParagraphs(['a']), [['a']])
    self.assertEqual(versify.GetParagraphs(['a', 'b']), [['a', 'b']])
    self.assertEqual(versify.GetParagraphs(['a\n', 'b\n']), [['a', 'b']])
    self.assertEqual(versify.GetParagraphs(['\n', 'a', '\n']), [['a']])
    self.assertEqual(versify.GetParagraphs([' ', 'a', ' ']), [['a']])
    self.assertEqual(versify.GetParagraphs(['', 'a', '']), [['a']])
    self.assertEqual(versify.GetParagraphs(['', 'a']), [['a']])
    self.assertEqual(versify.GetParagraphs(['a', '']), [['a']])
    self.assertEqual(versify.GetParagraphs([' \n', 'a', '  \n\n']), [['a']])
    self.assertEqual(
        versify.GetParagraphs( [' \n', ' a ', ' b ', ' c ', '\n \n']),
        [['a', 'b', 'c']])

  def testGetParagraphsDouble(self):
    self.assertEqual(versify.GetParagraphs(['a', '', 'b']), [['a'], ['b']])
    self.assertEqual(
        versify.GetParagraphs(['a', 'b', '', 'c', 'd']),
        [['a', 'b'], ['c', 'd']])
    self.assertEqual(
        versify.GetParagraphs(['', '', 'a', 'b', '', '', 'c', 'd', '', '']),
        [['a', 'b'], ['c', 'd']])


def suite():
  suite = unittest.makeSuite(VersifyTestCase, 'test')
  return suite

runner = unittest.TextTestRunner()
runner.run(suite())

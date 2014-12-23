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

  def testVersifyEmpty(self):
    begin = '\\begin{verse}'
    end = '\\end{verse}'
    self.assertEqual(versify.Versify([]), [])
    self.assertEqual(versify.Versify([[]]), [])

  def testVersifySingleStanza(self):
    begin = '\\begin{verse}'
    end = '\\end{verse}'
    self.assertEqual(versify.Versify([['a']]), [[begin, 'a', end]])
    self.assertEqual(
        versify.Versify([['a', 'b']]), [[begin, 'a', 'b', end]])
    self.assertEqual(
        versify.Versify([['a'], ['b']]), [[begin, 'a\\\\', 'b', end]])
    self.assertEqual(
        versify.Versify([['a'], ['b', 'c'], ['d']]), 
         [[begin, 'a\\\\', 'b', 'c\\\\', 'd', end]])

  def testVersifyTwoStanzas(self):
    begin = '\\begin{verse}'
    end = '\\end{verse}'
    self.assertEqual(
        versify.Versify([['a'], ['~'], ['b']]), [[begin, 'a'], ['b', end]])
    self.assertEqual(
        versify.Versify([['a'], ['b'], ['~'], ['c'], ['d']]), 
        [[begin, 'a\\\\', 'b'], ['c\\\\', 'd', end]])

def suite():
  suite = unittest.makeSuite(VersifyTestCase, 'test')
  return suite

runner = unittest.TextTestRunner()
runner.run(suite())

#!/usr/bin/python

import sys

# In this code, a paragraph is a list of lines. A document is a list of
# paragraphs.


def Escape(lines):
  output = []
  for line in lines:
    line = line.replace('[', '{[}')
    line = line.replace(']', '{]}')
    output.append(line)
  return output


def GetParagraphs(lines):
  '''Group lines into paragraphs. Paragraphs are denoted by empty lines in the
  input.
  '''
  paragraphs = []
  current_paragraph = []
  for line in lines:
    line = line.strip()
    if line:
      current_paragraph.append(line.strip())
    else:
      if current_paragraph:
        paragraphs.append(current_paragraph)
      current_paragraph = []
  if current_paragraph:
    paragraphs.append(current_paragraph)
  return paragraphs


def AddToStanza(stanza, paragraph):
  if not stanza:
    stanza += paragraph
    return
  stanza[-1] = stanza[-1] + '\\\\'
  stanza += paragraph


def Versify(paragraphs):
  '''Turns paragraphs into a LaTeX verse environment. Returns a list of
  paragraphs. Input paragraphs within a stanza are combined into a single
  output paragraph; input paragraphs are separated by a \\ within the
  output stanzas. A '~' paragaph is used as the stanza separator in the input.
  '''
  stanzas = []
  current_stanza = []
  for paragraph in paragraphs:
    if paragraph == ['~']:
      if current_stanza:
        stanzas.append(current_stanza)
      current_stanza = []
    else:
      AddToStanza(current_stanza, paragraph)
  if current_stanza:
    stanzas.append(current_stanza)

  stanzas_count = len(stanzas)
  output = []
  for i in xrange(stanzas_count):
    stanza = stanzas[i]
    if i == 0:
      stanza = ['\\begin{verse}'] + stanza
    if i == stanzas_count - 1:
      stanza = stanza + ['\\end{verse}']
    output.append(stanza)
  return output


def Format(paragraphs):
  output = ''
  for paragraph in paragraphs:
    if output:
      output += '\n'
    for line in paragraph:
      output += line + '\n'
  return output


if __name__ == '__main__':
  print Format(Versify(GetParagraphs(Escape(sys.stdin.readlines()))))

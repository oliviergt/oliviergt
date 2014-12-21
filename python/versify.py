

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

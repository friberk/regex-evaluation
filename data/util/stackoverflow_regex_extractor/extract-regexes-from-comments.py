#!/usr/bin/env python3
# Description:
#   Extracts regexes from comments on posts that are tagged with 'regex'.
#   Takes a file with regex post IDs and extracts regex patterns from comments associated with those posts.
#   Writes them in InternetRegexSource format to --out-file.

# Import our lib
from libLF import log as libLFlog
from libLF import isRegexPattern as libLFisRegexPattern
from libLF import perlStyleToPattern as libLFperlStyleToPattern
from libLF import StackOverflowRegexSource as libLFStackOverflowRegexSource

import argparse
import re
import html
from lxml import etree
from functools import partial

# input: body
# output: [p1, ...]: the (unique) patterns identified in the body. Maybe empty.
def extractPatternsFromCommentText(text):
  #libLFlog('Extracting patterns from: {}'.format(text))

  possiblePatterns = []

  # Match all code blocks in the comment text - typically enclosed in backticks
  # Comments in StackOverflow can contain inline code blocks with `code`
  code_blocks = re.findall(r'`([^`]+)`', text)

  for code in code_blocks:
    # Filter out lines beginning with a comment
    lines = [line for line in code.split('\n') if len(line) and line[0] is not '#' and line[0] is not '%']
    # Discard code blocks that span more than one line
    if 1 < len(lines):
      continue

    # Un-escape special HTML characters like < and >.
    code = html.unescape(code)

    # If they included a leading and trailing slash, remove them.
    code = libLFperlStyleToPattern(code)

    # Filter out things that aren't pattern-like
    if libLFisRegexPattern(code):
      possiblePatterns.append(code)
      #libLFlog('code is a pattern: {}'.format(code))

  return list(set(possiblePatterns))

# Helper function to load regex post IDs from file
def load_regex_post_ids(regex_post_ids_file):
  post_ids = set()
  with open(regex_post_ids_file, 'r') as f:
    for line in f:
      post_ids.add(line.strip())
  return post_ids

# Handler for fast_iter to process comments
def handleEventForComments(outStream, regex_post_ids, elem):
  if elem.tag == 'row':
    post_id = elem.get('PostId')

    # Only process comments for posts that are in our regex post IDs set
    if post_id in regex_post_ids:
      comment_id = elem.get('Id')
      comment_text = elem.get('Text')

      # Extract patterns from comment text
      patterns = extractPatternsFromCommentText(comment_text)
      if patterns:
        libLFlog(f'Comment {comment_id} on post {post_id} had {len(patterns)} patterns')

        # Build a StackOverflowRegexSource with appropriate URI
        source = libLFStackOverflowRegexSource()
        comment_uri = f'https://stackoverflow.com/questions/{post_id}#comment{comment_id}_{post_id}'
        uri_aliases = [
          f'https://stackoverflow.com/q/{post_id}#comment{comment_id}_{post_id}',
          f'http://stackoverflow.com/questions/{post_id}#comment{comment_id}_{post_id}',
          f'http://stackoverflow.com/q/{post_id}#comment{comment_id}_{post_id}'
        ]
        source.initFromRaw(uri=comment_uri, uriAliases=uri_aliases, patterns=patterns)

        # Write to output
        source.type= "StackOverflowCommentRegexSource"
        outStream.write(source.toNDJSON() + '\n')
        return True

  return False

# Fast iterator to efficiently process large XML files
def fast_iter(context, func):
  i = 0
  nFunc = 0
  for event, elem in context:
    if i and i % 10000 == 0:
      libLFlog('fast_iter: i {}'.format(i))

    if func(elem):
      nFunc = nFunc + 1
      if nFunc and nFunc % 10000 == 0:
        libLFlog('fast_iter: special {}'.format(nFunc))

    i += 1

    # Trim the XML tree. We won't need this entry again.
    elem.clear()
    while elem.getprevious() is not None:
      del elem.getparent()[0]
  del context
  return nFunc

def main(comments_xml_file, regex_post_ids_file, out_file):
  # Load the regex post IDs
  libLFlog(f'Loading regex post IDs from {regex_post_ids_file}')
  regex_post_ids = load_regex_post_ids(regex_post_ids_file)
  libLFlog(f'Loaded {len(regex_post_ids)} regex post IDs')

  # Process the comments
  with open(out_file, 'w') as outStream:
    libLFlog(f'Processing comments from {comments_xml_file} for regex patterns')
    context = etree.iterparse(comments_xml_file, events=('end',))
    n_comments_with_regex = fast_iter(context, partial(handleEventForComments, outStream, regex_post_ids))
    libLFlog(f'Found regex patterns in {n_comments_with_regex} comments')

###############################################

# Parse args
parser = argparse.ArgumentParser(description='Extract regexes from comments on regex-themed posts in StackOverflow')
parser.add_argument('--comments-file', '-c', help='Path to Comments.xml file', required=True)
parser.add_argument('--regex-post-ids', '-p', help='Path to file containing regex post IDs (one per line)', required=True)
parser.add_argument('--out-file', '-o', help='Where to write JSON results', required=True)

args = parser.parse_args()

# Here we go!
main(args.comments_file, args.regex_post_ids, args.out_file)
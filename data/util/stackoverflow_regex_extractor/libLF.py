"""Lingua Franca: NDJSON
"""

import json

#####
# ND-JSON
#####

def isNDJSON(ndjson):
  return type(ndjson) is str \
         and len(ndjson) >= 2 \
         and ndjson[0] is '{' \
         and ndjson[-1] is '}' \
         and ndjson.find('\n') is -1

def toNDJSON(obj):
  """Convert this object to an NDJSON-formatted string representation."""
  ndjson = json.dumps(obj, sort_keys=True)
  assert(isNDJSON(ndjson))
  return ndjson

def fromNDJSON(ndjson):
  """Return a simple Python object from an ndjson-encoded string."""
  ndjson = ndjson.strip()
  assert(isNDJSON(ndjson))
  return json.loads(ndjson)

"""Lingua Franca: utils
"""

import time
import sys
import platform
import os

#####
# Logging
#####

def log(msg):
  """Log this message."""
  sys.stderr.write('{} {}/{}: {}\n'.format(time.strftime('%d/%m/%Y %H:%M:%S'), platform.node(), os.getpid(), msg))

  """Lingua Franca: Internet-derived regexes
"""

#####
# InternetRegexSource
#####

class InternetRegexSource:
  """Represents a source of regexes on the internet.

  Members: uri, uriAliases, patterns[]
  You should sub-class from this for particular sources, e.g. RegExLib and StackOverflow.

  Sub-classes should define their type as a string, after calling the super's init.

  Use the factory method when handling arbitrary InternetRegexSource's from files.
  """

  def factory(jsonStr):
    """Create *and initialize* an InternetRegexSource from this ndjson string."""
    # Parse and get the 'type' field.
    obj = fromNDJSON(jsonStr)
    if not 'type' in obj:
      raise ValueError('Error no type in jsonStr: {}'.format(jsonStr))

    # Re-parse based on the appropriate type.
    internetSource = None
    if obj['type'] == "RegExLibRegexSource":
      internetSource = RegExLibRegexSource()
    elif obj['type'] == "StackOverflowRegexSource":
      internetSource = StackOverflowRegexSource()
    else:
      raise ValueError('Error, unexpected type {}'.format(obj['type']))
    internetSource.initFromNDJSON(jsonStr)
    return internetSource

  def __init__(self):
    """Declare an object and then initialize using JSON or "Raw" input."""
    self.initialized = False
    self.type = None

  def initFromRaw(self, uri, uriAliases, patterns):
    """uri: string. A unique identifier for this pattern in its source. Example: "https://stackoverflow.com/a/8270824".
       uriAliases: array of strings. Other unique identifiers for this source. Example: ["https://stackoverflow.com/questions/8270784/how-to-split-a-string-between-letters-and-digits-or-between-digits-and-letters/8270914#8270914", "https://stackoverflow.com/questions/8270784"].
       patterns: array of strings for the one or more patterns in this source. Example: ["[0-9]+|[a-z]+|[A-Z]+"].
    """
    self.initialized = True

    self.uri = uri
    self.uriAliases = uriAliases
    self.patterns = patterns

  def initFromNDJSON(self, jsonStr):
    self.initialized = True

    obj = fromNDJSON(jsonStr)
    self.uri = obj['uri']
    self.uriAliases = obj['uriAliases']
    self.patterns = obj['patterns']
    if 'type' in obj:
      self.type = obj['type']

  def toNDJSON(self):
    assert(self.initialized)
    # Consistent and in ndjson format
    return toNDJSON(self._toDict())

  def _toDict(self):
    obj = { "uri": self.uri,
            "uriAliases": self.uriAliases,
            "patterns": self.patterns
    }
    return obj

class RegExLibRegexSource(InternetRegexSource):
  """RegExLib regex source"""
  def __init__(self):
    super().__init__()
    self.type = "RegExLibRegexSource"

  def _toDict(self):
    obj = super()._toDict()
    obj['type'] = self.type
    return obj

class StackOverflowRegexSource(InternetRegexSource):
  """StackOverflow regex source"""
  def __init__(self):
    super().__init__()
    self.type = "StackOverflowRegexSource"

  def _toDict(self):
    obj = super()._toDict()
    obj['type'] = self.type
    return obj

import re

#####
# Misc regex functions
#####

def perlStyleToPattern(pattern):
  """Convert 's/abc/i'-style regexes to 'abc' patterns.

     Used during extraction of regexes from InternetSource.
  """
  if pattern.count('/') is 2:
    l = pattern.index('/')
    r = pattern.rindex('/')
    if 0 <= l and l < r:
      pattern = pattern[l+1 : r]
  return pattern

def isRegexPattern(string):
  """Returns True if string looks like a regex pattern, else False.

     Tries to exclude things that look like code snippets.

     Searches for any of the common regex feature syntaxes.
     Basically, we are looking for regexes that contain anything more
     advanced than characters.

     Example: We reject /a/ but accept /a+/.

     Uses notation from Chapman&Stolee ISSTA'16 (Table 4),
     which targets Python regexes.
     The syntax is pretty universal so I think this is OK for starters.

     Used during extraction of regexes from InternetSource.
  """

  # Filter: Code snippets.
  # Each of these is a source of false omissions.
  # Regexes that are actually matching source code will be rejected.
  if "(regex)" in string or "<regex>" in string or "[regex]" in string:
    return False
  if (   re.search(r're\.\w+\(', string)
      or re.search(r'RegExp\(', string)
      or re.search(r'preg_\w+\(', string)
      or re.search(r'console\.log', string)
      or re.search(r'\w\s+=\s+\w', string)
  ):
    return False

  # Regex syntax.
  if (False
  # Chapman & Stolee
  or re.search(r'\+', string) # ADD
  or re.search(r'\([\s\S]+\)', string) # CG
  or re.search(r'\*', string) # KLE
  or re.search(r'\[[\s\S]+\]', string) # CCC
  or re.search(r'\.', string) # ANY
  or re.search(r'\[.*\-.*\]', string) # RNG
  or re.search(r'\^', string) # STR
  or re.search(r'\$', string) # END
  or re.search(r'\[\^', string) # NCCC
  or re.search(r'\\s', string) # WSP
  or re.search(r'\|', string) # OR
  or re.search(r'\\d', string) # DEC
  or re.search(r'\\w', string) # WORD
  or re.search(r'\?', string) # QST
  or re.search(r'\+\?', string) # LZY - ADD
  or re.search(r'\*\?', string) # LZY - KLE
  or re.search(r'\(\?:', string) # NCG
  or re.search(r'\(\?P<', string) # PNG
  or re.search(r'{\d+}', string) # SNG
  or re.search(r'\\S', string) # NWSP
  or re.search(r'{\d+,\d+}', string) # DBB
  or re.search(r'\(\?!', string) # NLKA
  or re.search(r'\\b', string) # WNW
  or re.search(r'\\W', string) # NWRD
  or re.search(r'\{\d+,\}', string) # LWB
  or re.search(r'\(\?=', string) # LKA
  or re.search(r'\(\?\w+\)', string) # OPT
  or re.search(r'\(\?<!', string) # NLKB
  or re.search(r'\(\?<=', string) # LKB
  or re.search(r'\\Z', string) # ENDZ
  or re.search(r'\\\d+', string) # BKR
  or re.search(r'\\D', string) # NDEC
  or re.search(r'\(\?P=', string) # BKRN
  or re.search(r'\\v', string) # VWSP
  or re.search(r'\\B', string) # NWNW
  # Escaping special characters is also a good indicator.
  or re.search(r'\\', string)
  or re.search(r'\\(\[|\])', string)
  or re.search(r'\\(\(|\))', string)
  ):
    return True
  return False

def scorePatternWritingDifficulty(pattern):
  """Measure the human difficulty of WRITING a regex pattern.

  If score(r) < score(t), r is easier to write than t.
  When writing regexes, our intuition is that the longer
  the regex, the harder to write.

  Thus we simply use the length of the pattern as a measure of difficulty.
  """
  return len(pattern)

def scorePatternReadingDifficulty(pattern):
  """Measure the human difficulty of READING a regex pattern.

  If score(r) < score(t), r is easier to read than t.
  When reading regexes, our intuition is that the more convoluted
  the regex, the harder to read.

  Thus we want to use some measure of the complexity of the corresponding NFA-ish.
  Some caution here:
    While 'a{100}' has a "complex" NFA by raw size,
    I think this regex is about as easy to read as 'aaaaaa'.
      'a{100}': 100 states and 100 transitions
      'aaaaaa': 6 states and 6 transitions

    On this note, I experimented with the FAdo package but
    str2regexp did not work even in python2 for r'abc+' ??
  """
  # TODO This is too simplistic.
  return len(pattern)

def unescapeDoubleQuotes(strPattern):
  """Convert any \" to ".

  This is the primary difference between Rust string literals and raw string literals.
  If anyone is using the "end of line escape followed by a newline", however,
  we won't notice that.
  We have a similar problem with the Perl /x extended mode."""
  return strPattern.replace('\\"', '"')
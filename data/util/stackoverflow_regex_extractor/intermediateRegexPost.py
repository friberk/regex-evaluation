"""Intermediate regex post representation.

For regex-themed posts whose bodies have not yet been parsed for regexes.
"""

# Import our lib
from libLF import fromNDJSON as libLFfromNDJSON
from libLF import toNDJSON as libLFtoNDJSON

import re

class IntermediateRegexPost:
  def __init__(self):
    self.initialized = False
    pass

  def initFromRaw(self, _id, _parentId, _body, _isQuestion, _isAcceptedAnswer):
    self.initialized = True

    self.id = _id
    self.parentId = _parentId
    self.body = _body
    self.isQuestion = _isQuestion
    self.isAcceptedAnswer = _isAcceptedAnswer

  def initFromNDJSON(self, ndjson):
    self.initialized = True

    obj = libLFfromNDJSON(ndjson)
    self.id = obj['id']
    self.parentId = obj['parentId']
    self.body = obj['body']
    self.isQuestion = obj['isQuestion']
    self.isAcceptedAnswer = obj['isAcceptedAnswer']

  def toNDJSON(self):
    assert(self.initialized)
    obj = {
      'id': self.id,
      'parentId': self.parentId,
      'body': self.body,
      'isQuestion': self.isQuestion,
      'isAcceptedAnswer': self.isAcceptedAnswer,
    }
    return libLFtoNDJSON(obj)

  def getURI(self):
    uri = 'https://www.stackoverflow.com/'
    if self.isQuestion:
      uri += 'questions/'
    else:
      uri += 'a/'
    uri += self.id
    return uri

  def getURIAliases(self):
    uri = self.getURI()

    uriAliases = []
    # Individual transformations
    if self.isQuestion:
      # /questions and /q are the same
      uriAliases.append(re.sub(r'^https://www.stackoverflow.com/questions', 'https://www.stackoverflow.com/q', uri))
      # Additional aliases:
      # https://stackoverflow.com/questions/1041
      #   -> https://stackoverflow.com/questions/1041/easy-to-use-regular-expression-support-in-c
    else:
      # Answer aliases: https://stackoverflow.com/a/1055
      #   -> https://stackoverflow.com/questions/1041/#1055
      #   -> https://stackoverflow.com/questions/1041/1055#1055
      #   -> https://stackoverflow.com/questions/1041/easy-to-use-regular-expression-support-in-c/1055#1055
      pass

    # Mass transformations.
    # www. is optional
    www = [ re.sub(r'^https://www.stackoverflow', 'https://stackoverflow', alias) for alias in uriAliases ]
    uriAliases += www
    # http also works
    http = [ re.sub(r'^https://', 'http://', alias) for alias in uriAliases ]
    uriAliases += http

    return uriAliases

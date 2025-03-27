
import ast
import sys
import json
from typing import List

class RegexpInstance:
    funcName = ''
    pattern = ''
    flags = ''
    lineno = 0

    def __init__(self, func_name_, pattern_, flags_, lineno_):
        self.funcName = func_name_
        self.pattern = pattern_
        self.flags = flags_
        self.lineno = lineno_

    def get_func_name(self):
        return self.funcName

    def get_pattern(self):
        return self.pattern

    def get_flags(self):
        return self.flags

    def get_lineno(self):
        return self.lineno


def log(msg):
    if False:
        sys.stderr.write('{}\n'.format(msg))
    else:
        pass

# If you import re, these are the methods you might call on it.
regexpFuncNames = ['compile', 'search', 'match', 'fullmatch', 'split', 'findall', 'finditer', 'sub', 'subn', 'escape']
regexpFlagNames = ['DEBUG',
                   'I', 'IGNORECASE',
                   'L', 'LOCALE',
                   'M', 'MULTILINE',
                   'S', 'DOTALL',
                   'U', 'UNICODE',
                   'X', 'VERBOSE'
                   ]

# Signatures:
#  compile(pattern, flags=0)
#  search(pattern, string, flags=0)
#  match(pattern, string, flags=0)
#  fullmatch(pattern, string, flags=0)
#  split(pattern, string, maxsplit=0, flags=0)
#  findall(pattern, string, flags=0)
#  finditer(pattern, string, flags=0)
#  sub(pattern, repl, string, count=0, flags=0)
#  subn(pattern, repl, string, count=0, flags=0)
#  escape(pattern)

func_to_hasFlags = {'compile': 1,
                    'search': 1,
                    'match': 1,
                    'fullmatch': 1,
                    'split': 1,
                    'findall': 1,
                    'finditer': 1,
                    'sub': 1,
                    'subn': 1
                    }

# Find flags by checking this position in args, then by looking in the keywords array
func_to_flagsIndex = {'compile': 1,
                      'search': 2,
                      'match': 2,
                      'fullmatch': 2,
                      'split': 3,
                      'findall': 2,
                      'finditer': 2,
                      'sub': 4,
                      'subn': 4
                      }


# Walk an AST rooted at a node corresponding to regexp flags
class ASTWalkerForFlags(ast.NodeVisitor):
    flags = list()
    dynamic = False
    reAliases = list()

    def __init__(self, re_aliases):
        self.flags = list()
        self.dynamic = False
        self.reAliases = re_aliases

    # Programmer API
    def was_dynamic(self):
        return self.dynamic

    def get_flags(self):
        return self.flags

    # AST interface

    # All Attributes should describe 're.X'
    def visit_Attribute(self, node):
        try:
            # Is this an Attribute of the form x.y, where x is an re alias and y is an re pattern flag?
            module_name = node.value.id
            flag_name = node.attr
            if module_name in self.reAliases and flag_name in regexpFlagNames:
                log(f'ASTWalkerForFlags: flag_name {flag_name}')
                self.flags.append(flag_name)
            else:
                log('ASTWalkerForFlags: inappropriate Attribute {}.{}'.format(module_name, flag_name))
                self.dynamic = True
        except:
            self.dynamic = True

    def visit_Num(self, node):
        log(f'ASTWalkerForFlags: got num {node.n}')
        self.flags.append(f'{node.n}')

    # All Names should be 're'
    def visit_Name(self, node):
        # Must be Name node of an Attribute, where name is an re alias
        try:
            # Is this an Attribute of the form x.y, where x is an re alias and y is an re pattern flag?
            module_name = node.id
            if module_name in self.reAliases:
                pass
            else:
                log('ASTWalkerForFlags: Name: unexpected module_name {}'.format(module_name))
                self.dynamic = True
        except Exception as e:
            log('ASTWalkerForFlags: bad Name: {}'.format(e))
            self.dynamic = True

        # Recurse just in case
        ast.NodeVisitor.generic_visit(self, node)

    # BinOps are fine
    def visit_BinOp(self, node):
        # Recurse
        ast.NodeVisitor.generic_visit(self, node)

    # Load context is fine, we get it from BinOp
    def visit_Load(self, node):
        # Recurse just in case
        ast.NodeVisitor.generic_visit(self, node)

    # BitOrs are fine
    def visit_BitOr(self, node):
        # Recurse
        ast.NodeVisitor.generic_visit(self, node)

    # Any other nodes imply some kind of dynamic determination of the flags
    def generic_visit(self, node):
        log('ASTWalkerForFlags: Got an unexpected node, this is dynamic: {}'.format(ast.dump(node)))
        self.dynamic = True


# Walk full AST for regexps
class ASTWalkerForRegexps(ast.NodeVisitor):
    reAliases = list()
    regexps: List[RegexpInstance] = list()

    def __init__(self):
        super().__init__()
        self.reAliases = list()
        self.regexps = list()

    def get_regexps(self):
        return self.regexps

    # ImportFrom: Detect missed aliases for re functions
    def visit_ImportFrom(self, node):
        if node.module == 're':
            log('Potentially-missed regexps: ImportFrom re: {}'.format(ast.dump(node)))

    # Import: Detect aliases for the re module
    def visit_Import(self, node):
        try:
            for alias in node.names:
                if alias.name == 're':
                    if alias.asname is None:
                        name = alias.name
                    else:
                        name = alias.asname

                    log('New alias for re: {}'.format(name))
                    self.reAliases.append(name)
        except:
            pass

    def visit_Call(self, node):
        try:
            # Is this a call of the form x.y, where x is an re alias and y is a regexpFuncName ?
            func_id = node.func.value.id
            func_name = node.func.attr
            if func_id in self.reAliases and func_name in regexpFuncNames:
                log('Got an RE: {}.{}'.format(func_id, func_name))
                log(ast.dump(node))

                # Get pattern
                #if type(node.args[0]) is ast.Str:
                #    log('Pattern is static')
                #    pattern = node.args[0].s
                #else:
                #    log('Pattern is dynamic')
                #    pattern = 'DYNAMIC-PATTERN'
                if type(node.args[0]) is ast.Constant and type(node.args[0].value) is str:
                    log('pattern is static')
                    pattern = node.args[0].value
                    lineno = node.args[0].lineno
                else:
                    log('Pattern is dynamic')
                    pattern = 'DYNAMIC-PATTERN'
                    lineno = node.args[0].lineno

                # Get flags
                func_can_have_flags = False
                dynamic_flags = False
                flag_names = []
                if func_to_hasFlags.get(func_name):  # escape has no flags
                    func_can_have_flags = True
                    flags_node = False

                    # Positional check
                    flag_ix = func_to_flagsIndex.get(func_name)
                    if flag_ix < len(node.args):
                        log('Flags provided to {} using positional argument'.format(func_name))
                        flags_node = node.args[flag_ix]
                    else:
                        # Keywords check
                        log('Flags not provided to {} using positional argument; flag_ix {} length of args {}'.format(
                            func_name, flag_ix, len(node.args)))
                        for kw in node.keywords:
                            if kw.arg == 'flags':
                                log('Flags provided using keywords')
                                flags_node = kw.value
                                break

                    # Did we find flags in positional or keywords?
                    if flags_node:
                        flag_walker = ASTWalkerForFlags(self.reAliases)
                        flag_walker.visit(flags_node)
                        if flag_walker.was_dynamic():
                            dynamic_flags = True
                        else:
                            flag_names = flag_walker.get_flags()
                else:
                    log('{} does not have a flags field'.format(func_name))
                    func_can_have_flags = False

                if func_can_have_flags:
                    if dynamic_flags:
                        flags_string = 'DYNAMIC-FLAGS'
                    else:
                        flags_string = '|'.join(flag_names)
                else:
                    flags_string = 'FLAGLESS'

                log_str = 'func_name <{}>, pattern <{}>, flags <{}>'.format(func_name, pattern, flags_string)
                log(log_str)
                # sys.stdout.write(log_str + '\n')
                self.regexps.append(RegexpInstance(func_name, pattern, flags_string, lineno))
        except Exception as e:
            log('DEBUG: ASTWalkerForRegexps: visit_Call exception: {}'.format(e))

        # Recurse
        ast.NodeVisitor.generic_visit(self, node)


def parse_file(sourcefile: str) -> List[RegexpInstance]:
    # Count lines_of_code
    # lines_of_code = count_loc(sourcefile)
    # log('{} has {} lines_of_code'.format(sourcefile, lines_of_code))

    # Read file and prep an AST.
    try:
        with open(sourcefile, 'r') as FH:
            content = FH.read()
            root = ast.parse(content, sourcefile)

            walker = ASTWalkerForRegexps()
            walker.visit(root)

            # TODO this is the dump command
            # sys.stdout.write(json.dumps(objects) + '\n')
        return walker.get_regexps()

    except Exception as e:
        # Easy-to-parse to stdout
        # err_msg = 'Something went wrong, perhaps try with a different Python interpreter'
        # sys.stdout.write(err_msg + '\n')
        #
        # # More verbose to stderr
        # log(err_msg)
        # log(e)
        #
        # # Byee
        # sys.exit(1)
        return []

def parse_file_json_buffer(sourcefile: str) -> str:
    results = parse_file(sourcefile)
    objects = [
        {
            'source_file': sourcefile,
            'pattern': regexp.pattern,
            'flags': regexp.flags,
            'line_no': regexp.lineno
        } for regexp in results
    ]

    return json.dumps(objects)

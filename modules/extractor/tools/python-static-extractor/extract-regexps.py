# Description: Extract regexps from a python file
# Implementation: AST traversal
#
# Invocation: AST processing is baked into the python interpreter,
#               but we may be working with repositories based on python2 or python3.
#             One version may yield syntax errors in the other.
#             For example, 'print "foo"' works in python2 but not in python3.
#
#             Therefore, invoke first as 'python2 extract-regexps.py'.
#             On syntax errors, invoke as 'python3 extract-regexps.py'
#
# Resources:
#   Python re docs: https://docs.python.org/3/library/re.html
#   Python AST docs: https://docs.python.org/2/library/ast.html
#   AST how-to:  https://suhas.org/function-call-ast-python/
#   JSON: https://docs.python.org/3/library/json.html
#
# Limitations:
#   Detects imports of the module 're' as "import re" and "import re as X"
#   However, will not find regexps if the caller uses "from re import *"
#     and then calls the imported methods directly.
#
# Dependencies:
#   Must define ECOSYSTEM_REGEXP_PROJECT_ROOT
#   cloc must be defined in PATH
#
# Output:
#   Prints a JSON object with keys: filename LoC regexps[]
#     filename is the path provided
#     LoC is the 'code' field computed by cloc
#     regexps is an array of objects, each with keys: funcName pattern flags
#       funcName is the re module function being invoked
#       pattern and flags are each either a string or 'DYNAMIC-{PATTERN|FLAGS}'
#       If the regexp invocation cannot have flags, the flags string will be 'FLAGLESS' instead
import json
import os
import socket
import sys
from concurrent.futures import ThreadPoolExecutor

from parse_request_handler import parse_file


def handle_connection(client: socket.socket):
    conn_stream = client.makefile('r')
    for line in conn_stream:
        line = line.strip()
        if len(line) == 0:
            # we have an empty line, so quite
            client.send(b'[]\r\n')
            client.close()
            print('Closed connection')
            return
        else:
            print(f'Parsing file {line}...')
            regexes = parse_file(line)
            print(f'Got {len(regexes)} regexes')
            objects = [
                {
                    'source_file': line,
                    'pattern': regexp.pattern,
                    'flags': regexp.flags,
                    'line_no': regexp.lineno
                } for regexp in regexes
            ]
            client.send(json.dumps(objects).encode('UTF-8'))
            client.send(b'\r\n')


def main(listening_path: str, concurrency: int):
    print(f"Listening for requests on {listening_path}...")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove(listening_path)
    except Exception:
        pass

    server.bind(listening_path)
    server.listen(16)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        while True:
            print('waiting on a connection...')
            conn, addr = server.accept()
            executor.submit(handle_connection, conn)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} <server listen path> <concurrency>')
        sys.exit(1)

    main(sys.argv[1], int(sys.argv[2]))

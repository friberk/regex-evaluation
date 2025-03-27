import ast
import json
import socket
import socketserver

from extractors import ASTWalkerForRegexps
from regex_instance import RegexpInstance
from socket_stream_reader import SocketStreamReader

from typing import List

class ParseRequestHandler(socketserver.BaseRequestHandler):
    def setup(self):
        print("Client connected")

    def handle(self):
        reader = SocketStreamReader(self.request)
        while True:
            next_line = reader.readline().strip()
            if len(next_line) == 0:
                print("Got empty line")
                self.request.send(b'[]\r\n')
                self.request.close()
                return  # we're done with this connection at this point?

            regexes = parse_file(next_line.decode('UTF-8'))
            if len(regexes) > 0:
                objects = [
                    {
                        'source_file': next_line.decode('UTF-8'),
                        'pattern': regexp.pattern,
                        'flags': regexp.flags,
                        'line_no': regexp.lineno
                    } for regexp in regexes
                ]
                self.request.send(json.dumps(objects).encode('UTF-8'))
                self.request.send(b'\r\n')


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

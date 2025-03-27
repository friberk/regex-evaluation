
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

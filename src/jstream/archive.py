class Json:
    def __init__(self, oa):
        self.oa = oa
    def is_object(self):
        return type(self.oa) is Object
    def is_array(self):
        return type(self.oa) is Array

class Object:
    def __init__(self, members: list['Pair']):
        self.members: list[Pair] = members

class Pair:
    def __init__(self, key: str, val):
        self.key = key
        self.value = val

class Array:
    def __init__(self, elements):
        self.elements = elements

class ParserException(Exception):
    pass

'''
If the characters leading up to, and including,
`c` can be parsed, return the AST, otherwise 
throw a ParserException.

Any parse(c) -> throws ParserException:
       
'''
class ParserCombinator:
    def __init__(self, parsers):
        self.level = 0
        self.parsers = parsers

    def parse(self, c):
        new_parsers = []
        for p in self.parsers:
            try:
                return p.parse(c)
            except ParserException:
                pass
            new_parsers.append(p)
        self.parsers = new_parsers

class JsonParser(ParserCombinator):
    def __init__(self):
        super().__init__([ObjectParser(), ArrayParser()])

class ObjectParser:
    def __init__(self):
        self.captured_str = []
        self.mem_parser = MembersParser()
        self.last_ret = None

    def parse(self, c):
        self.captured_str.append(c)
        if self.captured_str == ["{", "}"]:
            return Object([])
        if self.captured_str[0] == "{" and \
            c == "}" and self.last_ret != None:
            return Object(self.last_ret)
        self.last_ret = None
        if 1 < len(self.captured_str):
            self.last_ret = self.mem_parser.parse(c)
        raise ParserException()

class ArrayParser:
    def __init__(self):
        self.captured = []
        self.mem_parser = MembersParser()
        self.last_ret = None

    def parse(self, c):
        self.captured.append(c)
        if self.captured == ["[", "]"]:
            return Array([])
        if c == "]" and self.captured[0] == "[" and \
            self.last_ret != None:
            return Array(self.last_ret)
        self.last_ret = None
        if self.captured[0] == "[" and 1 < len(self.captured):
            self.last_ret = self.mem_parser.parse(c)
        raise ParserException()


class MembersParser:
    def __init__(self):
        self.pairs = []
        self.pair_parser = PairParser()
        self.last_ret = None

    def parse(self, c):
        if c == "," and self.last_ret != None:
            self.pair_parser = PairParser()
            return
        self.last_ret = None
        self.last_ret = self.pair_parser.parse(c)
        self.pairs.append(self.last_ret)
        return self.pairs

class PairParser:
    def __init__(self):
        self.captured = []
        self.value_parser = ValueParser()
        self.key = None

    def parse(self, c):
        self.captured.append(c)
        if 1 < len(self.captured) and c == "\"" and \
            self.captured[0] == "\"" and \
            self.captured[-2] != "\\" and \
            self.key == None:
            self.key = "".join(self.captured[1:-1])
            raise ParserException()

        if self.key == None:
            raise ParserException()

        if self.captured[-2] == ":":
            self.captured.pop()
        
        return Pair(self.key, self.value_parser.parse(c))

class ElementParser:
    def __init__(self):
        self.val_arr = []

    def parse(self, c):

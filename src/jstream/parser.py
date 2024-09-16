'''

<Json> ::= <Object>
         | <Array>

<Object> ::= '{' '}'
           | '{' <Members> '}'

<Members> ::= <Pair>
            | <Pair> ',' <Members>

<Pair> ::= String ':' <Value>

<Array> ::= '[' ']'
          | '[' <Elements> ']'

<Elements> ::= <Value>
             | <Value> ',' <Elements>

<Value> ::= String
          | Number
          | <Object>
          | <Array>
          | true
          | false
          | null

'''

from collections.abc import Generator
from enum import Enum
from typing import Any, ClassVar
from .tokenizer import Separator

class TokenParser:
    def __init__(self, predicate):
        self.predicate = predicate
        self.done = False
    def parse_step(self, tok):
        if not self.done and self.predicate(tok):
            yield tok, 1
        if self.done:
            yield None, None
        self.done = True

def is_separator(target):
    return lambda c : type(c) is Separator and c.c == target

def is_char(target):
    return lambda c : c == target

def is_type(typ):
    return lambda o : type(o) is typ

class ParserCombinator:
    def __init__(self, *parsers):
        self.parsers = parsers
        self.parser_instances = [p() for p in parsers]
        self.ast = []
    
    def parse_generator(self, gen) -> Generator[tuple[Any, int]]:
        for tok in gen:
            yield from self.parse_step(tok)

    def ast_gen(self):
        for a in self.ast:
            yield a

    def parse_step(self, tok):
        for parser in self.parser_instances:
            for ast_node, toks_consumed in parser.parse_step(tok):
                if toks_consumed == None:
                    continue
                yield ast_node, toks_consumed

class Rule:
    def __init__(self, formatter, *parser_pairs):
        assert(len(parser_pairs) % 2 == 0 and len(parser_pairs) > 0)
        self.parser_pairs = parser_pairs
        self.active_parsers = [(0, self.get_parser(0), [])]
        self.n = len(parser_pairs) // 2
        self.formatter = formatter
        self.tot = 0

    def get_parser(self, ind):
        return self.parser_pairs[2*ind](*self.parser_pairs[2*ind+1])

    def parse_step(self, node):
        nparsers = len(self.active_parsers)
        self.tot += 1
        indx_marked_for_deletion = []
        for i in range(nparsers):
            cn, p, ra = self.active_parsers[i]
            for r, toks in p.parse_step(node):
                if toks == None: # parser has finished
                    indx_marked_for_deletion.append(i)
                    continue
                if cn+1 == self.n:
                    b = ra + [r]
                    yield self.formatter(*b), self.tot
                    continue
                self.active_parsers.append((
                    cn+1,
                    self.get_parser(cn+1),
                    ra + [r],
                ))
        for i in reversed(indx_marked_for_deletion):
            del self.active_parsers[i]


class JsonParser(ParserCombinator):
    def __init__(self):
        super().__init__(ValueParser)

class ObjectParser(ParserCombinator):
    def __init__(self):
        super().__init__(ObjectParserR1, ObjectParserR2)

# <Object> ::= '{' '}'
class ObjectParserR1(Rule):
    def __init__(self):
        super().__init__(
            lambda *_: {}, 
            TokenParser, [is_separator("{")],
            TokenParser, [is_separator("}")],
        )

# <Object> ::= '{' <Members> '}'
class ObjectParserR2(Rule):
    def __init__(self):
        super().__init__(
            lambda *a : a[1],
            TokenParser, [is_separator("{")],
            MembersParser, [],
            TokenParser, [is_separator("}")],
        )
            
# <Members> ::= <Pair>
class MembersParser(ParserCombinator):
    def __init__(self):
        super().__init__(PairParser, MembersParserR2)
        
# <Members> ::= <Pair> ',' <Members> 
class MembersParserR2(Rule):
    def __init__(self):
        def formatter(ps, _, ms):
            for k, v in ms.items():
                ps[k] = v
            return ps
        super().__init__(
            formatter,
            PairParser, [],
            TokenParser, [is_separator(",")],
            MembersParser, [],
        )

# <Pair> ::= String ':' <Value>
class PairParser(Rule):
    def __init__(self):
        super().__init__(
            lambda s, _, v: {s:v},
            TokenParser, [is_type(str)],
            TokenParser, [is_separator(":")],
            ValueParser, [],
        )

class ArrayParser(ParserCombinator):
    def __init__(self):
        super().__init__(ArrayParserR1, ArrayParserR2)

# <Array> ::= '[' ']'
class ArrayParserR1(Rule):
    def __init__(self):
        super().__init__(
            lambda *_: [], 
            TokenParser, [is_separator("[")],
            TokenParser, [is_separator("]")],
        )

# <Array> ::= '[' <Elements> ']'
class ArrayParserR2(Rule):
    def __init__(self):
        super().__init__(
            lambda *a: a[1],
            TokenParser, [is_separator("[")],
            ElementsParser, [],
            TokenParser, [is_separator("]")],
        )

class ElementsParser(ParserCombinator):
    def __init__(self):
        super().__init__(ElementsParserR1, ElementsParserR2)

# <Elements> ::= <Value>
class ElementsParserR1(Rule):
    def __init__(self):
        def formatter(v):
            return [v]
        super().__init__(
            formatter,
            ValueParser, [],
        )
# <Elements> ::= <Value> ',' <Elements>
class ElementsParserR2(Rule):
    def __init__(self):
        def formatter(v, _, elms):
            elms = [v] + elms
            return elms
        super().__init__(
            formatter,
            ValueParser, [],
            TokenParser, [is_separator(",")],
            ElementsParser, [],
        )

# <Value> ::= String
#           | Number
#           | <Object>
#           | <Array>
#           | true
#           | false
#           | null
def is_value(c):
    return type(c) is str or \
            type(c) is int or \
            type(c) is float or \
            type(c) is dict or \
            type(c) is list or \
            type(c) is bool or \
            c == None

class ValueParser(ParserCombinator):
    def __init__(self):
        super().__init__(ValuePrimitiveParser, ObjectParser, ArrayParser)

class ValuePrimitiveParser(Rule):
    def __init__(self):
        super().__init__(
            lambda *a: a[0],
            TokenParser, [is_value],
        )



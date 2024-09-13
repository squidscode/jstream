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
        self.ast.append(tok)
        has_reduced = False
        tot = 0
        for parser in self.parser_instances:
            # print(f"Checking {type(parser)=}")
            for ast_node, toks_consumed in parser.parse_step(tok):
                # print(f"Consumed {ast_node=}, {toks_consumed=}")
                self.ast = [ast_node] + self.ast[toks_consumed:]
                has_reduced = True
                tot += toks_consumed
        if has_reduced:
            yield self.ast[0], tot
        # print(f"New {self.ast=}")

class Rule:
    def __init__(self, formatter, *pgen):
        def parsers_gen():
            i = 0
            while i < len(pgen):
                yield pgen[i](*pgen[i+1])
                i += 2
        parsers = parsers_gen()
        self.sentinel = object()
        self.cur_parser = next(parsers, None)
        self.parsed_output = []
        self.total = 0
        self.formatter = formatter
        self.parsers = parsers

    def parse_step(self, node):
        # print(f"[{type(self).__name__}] parsing node: {node}")
        if self.cur_parser == None:
            return
        nxt_out = next(self.cur_parser.parse_step(node), self.sentinel)
        if nxt_out is self.sentinel:
            return
        # print(f"{nxt_out=}")
        pout, pntoks = nxt_out
        self.total += pntoks
        self.parsed_output.append(pout)
        # print(f"[{type(self).__name__}] Prev {self.cur_parser=}")
        self.cur_parser = next(self.parsers, None)
        # print(f"[{type(self).__name__}] New {self.cur_parser=}")
        if self.cur_parser == None:
            yield self.formatter(*self.parsed_output), self.total

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

# <Elements> ::= <Value>
class ElementsParser(ParserCombinator):
    def __init__(self):
        super().__init__(ValueParser, ElementsParserR2)

# <Elements> ::= <Value> ',' <Elements>
class ElementsParserR2(Rule):
    def __init__(self):
        def formatter(v, _, elms):
            return [v] + elms
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



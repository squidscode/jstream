'''
JStream is a minimal copy of the `json` standard library,
exposing the same API as the standard library, but enabling
the ability to parse json as a stream of characters.

The following functions all either take in an iterator of characters
as its input or return a generator object of characters.

>>> jstream.dumpg(...)
>>> jstream.loadg(...)
'''

from collections.abc import Generator

from src.jstream.parser import JsonParser
from src.jstream.tokenizer import JsonLexer
import json

def dumps(gen: Generator):
    for j in gen:
        print(json.dumps(j))

def loads(gen: Generator):
    lexer = JsonLexer()
    def lex_gen():
        yield from lexer.generator(gen)
        yield from lexer.flush()
    parser = JsonParser()
    for obj, _ in parser.parse_generator(lex_gen()):
        yield obj


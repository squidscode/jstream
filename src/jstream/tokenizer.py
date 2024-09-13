'''
! ------------------------------------------------- Sets

{Unescaped} = {All Valid} - {&1 .. &19} - ["\\]
{Hex} = {Digit} + [ABCDEFabcdef]
{Digit9} = {Digit} - [0]

! ------------------------------------------------- Terminals

Number = '-'?('0'|{Digit9}{Digit}*)('.'{Digit}+)?([Ee][+-]?{Digit}+)?
String = '"'({Unescaped}|'\\'(["\\/bfnrt]|'u'{Hex}{Hex}{Hex}{Hex}))*'"'
true = true
false = false
null = null

! ------------------------------------------------- Rules
'''

import re

Unescaped = r"[\w ]"
Hex = "[0123456789ABCDEFabcdef]"
Digit9 = "[123456789]"
Digit = "[0123456789]"
rnumber = f"-?(0|{Digit9}{Digit}*)(\\.{Digit}+)?([Ee][+-]?{Digit}+)?"
rstring = f"\"({Unescaped}|\\\\([\"\\/bfnrt]|u{Hex}{Hex}{Hex}{Hex}))*\""
rjson_separators = "[][{}:,]"
rtrue = "true"
rfalse = "false"
rnull = "null"
rwhitespace = "\\s+"

class Separator:
    def __init__(self, c):
        self.c = c

class JsonLexer:
    def __init__(self):
        self.last_match = None       
        identity = lambda x : x
        self.s = []
        self.transformers = {
            rjson_separators: lambda sep: Separator(sep),
            rnumber: lambda x : (float(x) if "." in x or "e" in x or "E" in x else int(x)),
            rstring: identity,
            rtrue: lambda x : bool(x),
            rfalse: lambda x : bool(x), 
            rnull: lambda _ : None,
        }
        self.whitespace = re.compile(rwhitespace)
        self.regs = {
            s: re.compile(s) for s, _ in 
            self.transformers.items()
        }
        self.last_match = None
        self.lag = 2

    def generator(self, gen):
        for c in gen:
            yield from self.parse(c)
        yield from self.flush()

    def parses(self, s):
        for c in s:
            yield from self.parse(c)

    def parse(self, c):
        assert(len(c) == 1)
        self.s.append(c)
        yield from self.process()

    def flush(self):
        yield from self.parses("\n" * (self.lag + 1))

    def process(self):
        st = "".join(self.s)
        # print(f"process({st})")
        if (m := self.whitespace.match(st)) and m != None:
            self.s = self.s[m.span()[1]:]
            st = st[m.span()[1]:]

        for rs, r in self.regs.items():
            if (cur_match := r.match(st)) and cur_match != None:
                # print(f"{cur_match=}, {self.last_match=}")
                if self.last_match != None and cur_match.span() == self.last_match.span() \
                    and cur_match.span()[1] < len(st) - self.lag:
                    _, idx = cur_match.span()
                    captured = st[:idx]
                    self.s = self.s[idx:]
                    self.last_match = None
                    # print("Found:", cur_match)
                    yield self.transformers[rs](captured)
                # print(f"Resetting last_match: {cur_match}")
                self.last_match = cur_match
                return
        self.last_match = None


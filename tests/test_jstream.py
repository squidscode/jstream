import src.jstream as jstream
import unittest
import src.jstream.parser as parser
import src.jstream.tokenizer as tokenizer

def f(s):
    for c in s:
        yield c

class IntegrationTest(unittest.TestCase):
    def test_jstream_loads(self):
        self.assertEqual(list(jstream.loads(f(""))), [])
        
        self.assertEqual(list(jstream.loads(f("10"))), [10])
        self.assertEqual(list(jstream.loads(f("10.1"))), [10.1])
        
        self.assertEqual(list(jstream.loads(f("10.1e10"))), [10.1e10])
        self.assertEqual(list(jstream.loads(f("0.123456789e9"))), [0.123456789e9])
        self.assertEqual(list(jstream.loads(f("{}"))), [{}])
        
        self.assertEqual(list(jstream.loads(f('{"hi": "bye"}'))), [{"hi": "bye"}])
        self.assertEqual(list(jstream.loads(f('{"hi": 10}'))), [{"hi": 10}])
        self.assertEqual(list(jstream.loads(f('{"hi": [10,12]}'))), [{"hi": [10,12]}])
        self.assertEqual(list(jstream.loads(f(
            '{"command": "hello", "client id": 1203000400, "data": [10, 34, 24]}'
        ))), [
            {"command": "hello", "client id": 1203000400, "data": [10,34, 24]},
        ])


class ParserTests(unittest.TestCase):
    def test_json_parser(self):
        pass

    def test_object_parser(self):
        def parse(*toks):
            p = parser.ObjectParser()
            a = []
            for tok in toks:
                a.extend(p.parse_step(tok))
            return a

    def test_object_parser1(self):
        p = parser.ObjectParserR1()
        a = []
        a.extend(p.parse_step(tokenizer.Separator("{")))
        a.extend(p.parse_step(tokenizer.Separator("}")))
        self.assertEqual(a, [({}, 2)])

        a.extend(p.parse_step(tokenizer.Separator("{")))
        a.extend(p.parse_step(tokenizer.Separator("}")))
        self.assertEqual(a, [({}, 2)])

    def test_object_parser2(self):
        def parse(*toks):
            p = parser.ObjectParserR2()
            a = []
            for tok in toks:
                a.extend(p.parse_step(tok))
            return a
        self.assertEqual(parse(
            tokenizer.Separator("{"),
            "hi",
            tokenizer.Separator(":"),
            "bye",
            tokenizer.Separator("}"),
            ),
            [({"hi": "bye"}, 5)]
        )

    def test_members_parser(self):
        pass

    def test_members_parser2(self):
        pass

    def test_pair_parser(self):
        pass

    def test_array_parser(self):
        p = parser.ArrayParser()
        a = []
        a.extend(p.parse_step(tokenizer.Separator("[")))
        a.extend(p.parse_step(tokenizer.Separator("]")))
        self.assertEqual(a, [([], 2)])
        a.extend(p.parse_step(tokenizer.Separator("[")))
        a.extend(p.parse_step(19))
        a.extend(p.parse_step(tokenizer.Separator("]")))
        self.assertEqual(a, [([], 2)])

        p = parser.ArrayParser()
        a = []
        a.extend(p.parse_step(tokenizer.Separator("[")))
        a.extend(p.parse_step(10))
        a.extend(p.parse_step(tokenizer.Separator("]")))
        self.assertEqual(a, [([10], 3)])

        p = parser.ArrayParser()
        a = []
        a.extend(p.parse_step(tokenizer.Separator("[")))
        a.extend(p.parse_step(10))
        a.extend(p.parse_step(tokenizer.Separator(",")))
        a.extend(p.parse_step(10))
        a.extend(p.parse_step(tokenizer.Separator("]")))
        self.assertEqual(a, [([10, 10], 5)])

    def test_array_parser1(self):
        p = parser.ArrayParserR1()
        a = []
        a.extend(p.parse_step(tokenizer.Separator("[")))
        a.extend(p.parse_step(tokenizer.Separator("]")))
        self.assertEqual(a, [([], 2)])

    def test_array_parser2(self):
        p = parser.ArrayParserR2()
        a = []
        a.extend(p.parse_step(tokenizer.Separator("[")))
        a.extend(p.parse_step(tokenizer.Separator("]")))
        self.assertEqual(a, [])

        p = parser.ArrayParserR2()
        a = []
        a.extend(p.parse_step(tokenizer.Separator("[")))
        a.extend(p.parse_step(10))
        a.extend(p.parse_step(tokenizer.Separator("]")))
        self.assertEqual(a, [([10], 3)])

        p = parser.ArrayParserR2()
        a = []
        a.extend(p.parse_step(tokenizer.Separator("[")))
        a.extend(p.parse_step(10))
        a.extend(p.parse_step(tokenizer.Separator(",")))
        a.extend(p.parse_step(10))
        a.extend(p.parse_step(tokenizer.Separator("]")))
        self.assertEqual(a, [([10,10], 5)])

    def test_elements_parser(self):
        pass

    def test_elements_parser_r1(self):
        def parse(val):
            p = parser.ElementsParserR1()
            return list(p.parse_step(val))
        g = parse({})
        self.assertEqual(g, [([{}], 1)])
        g = parse([])
        self.assertEqual(g, [([[]], 1)])
        g = parse(1)
        self.assertEqual(g, [([1], 1)])
        g = parse("string")
        self.assertEqual(g, [(["string"], 1)])

    def test_elements_parser2(self):
        comma = tokenizer.Separator(",")
        def parse(*vals):
            p = parser.ElementsParserR2()
            a = []
            for v in vals:
                a.extend(p.parse_step(v))
            return a
        g = parse({}, comma, 1)
        self.assertEqual(g, [([{}, 1], 3)])
        g = parse([], comma, 2)
        self.assertEqual(g, [([[], 2], 3)])
        g = parse(1, comma, 10)
        self.assertEqual(g, [([1, 10], 3)])
        g = parse("string", comma, "s", comma, "r")
        self.assertEqual(g, [(["string", "s"], 3), (["string", "s", "r"], 5)])

    def test_value_parser(self):
        pass

    def test_value_primitive_parser(self):
        def parse(val):
            p = parser.ValuePrimitiveParser()
            return list(p.parse_step(val))
        g = parse("I am a string literal")
        self.assertEqual(g, [("I am a string literal", 1)])
        g = parse(10)
        self.assertEqual(g, [(10, 1)])
        def check_double_pair(g, p):
            self.assertTrue(len(g) == 1)
            self.assertTrue(len(g[0]) == 2)
            self.assertAlmostEqual(p[0], g[0][0])
            self.assertEqual(p[1], g[0][1])
        g = parse(10.1)
        check_double_pair(g, (10.1, 1))
        g = parse(123456789.5e10)
        check_double_pair(g, (123456789.5e10, 1))
        g = parse({})
        self.assertEqual(g, [({}, 1)])
        g = parse([])
        self.assertEqual(g, [([], 1)])
        g = parse(True)
        self.assertEqual(g, [(True, 1)])
        g = parse(False)
        self.assertEqual(g, [(False, 1)])
        g = parse(None)
        self.assertEqual(g, [(None, 1)])

        # Check that a mutliple values cannot be parsed.
        p = parser.ValuePrimitiveParser()
        g = p.parse_step("")
        g2 = p.parse_step(2)
        self.assertEqual(list(g), [("", 1)])
        self.assertEqual(list(g2), [])


# Parser for Object Diagrams textual concrete syntax

from lark import Lark, logger, Transformer
from lark.indenter import Indenter
from services.od import OD
from services.scd import SCD
from uuid import UUID

grammar = r"""
%import common.WS_INLINE
%ignore WS_INLINE
%ignore COMMENT

%declare _INDENT _DEDENT

?start: (_NL | object )*

IDENTIFIER: /[A-Za-z_][A-Za-z_0-9]*/
COMMENT: /#.*/

# newline
_NL: /(\r?\n[\t ]*)+/

literal: INT
       | STR
       | BOOL
       | CODE

INT: /[0-9]+/
STR: /"[^"]*"/
   | /'[^']*'/
BOOL: "True" | "False"
CODE: /`[^`]*`/

object: [IDENTIFIER] ":" IDENTIFIER [link_spec] _NL [_INDENT slot+ _DEDENT]
link_spec: "(" IDENTIFIER "->" IDENTIFIER ")"
slot: IDENTIFIER "=" literal _NL
"""


class TreeIndenter(Indenter):
    NL_type = '_NL'
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 4

parser = Lark(grammar, parser='lalr', postlex=TreeIndenter())

# internal use only
# just a dumb wrapper to distinguish between code and string
class _Code:
    def __init__(self, code):
        self.code = code

# given a concrete syntax text string, and a meta-model, parses the CS
def parse_od(state, cs_text, mm):
    tree = parser.parse(cs_text)

    m = state.create_node()
    od = OD(mm, m, state)

    int_mm_id = UUID(state.read_value(state.read_dict(state.read_root(), "Integer")))

    class T(Transformer):
        def __init__(self, visit_tokens):
            super().__init__(visit_tokens)
            self.obj_counter = 0

        def IDENTIFIER(self, token):
            return str(token)
        
        def INT(self, token):
            return int(token)

        def BOOL(self, token):
            return token == "True"

        def STR(self, token):
            return str(token[1:-1]) # strip the "" or ''

        def CODE(self, token):
            return _Code(str(token[1:-1])) # strip the ``

        def literal(self, el):
            return el[0]

        def link_spec(self, el):
            [src, tgt] = el
            return (src, tgt)
        
        def slot(self, el):
            [attr_name, value] = el
            return (attr_name, value)
        
        def object(self, el):
            [obj_name, type_name, link] = el[0:3]
            if obj_name == None:
                # object/link names are optional
                #  generate a unique name if no name given
                obj_name = f"__o{self.obj_counter}"
                self.obj_counter += 1
            if link == None:
                obj_node = od.create_object(obj_name, type_name)
            else:
                src, tgt = link
                if tgt == "Integer":
                    if state.read_dict(m, "Integer") == None:
                        scd = SCD(m, state)
                        scd.create_model_ref("Integer", int_mm_id)
                od.create_link(obj_name, type_name, src, tgt)
            # Create slots
            slots = el[3:]
            for attr_name, value in slots:
                value_name = f"{obj_name}.{attr_name}"
                # watch out: in Python, 'bool' is subtype of 'int'
                #  so we must check for 'bool' first
                if isinstance(value, bool):
                    tgt = od.create_boolean_value(value_name, value)
                elif isinstance(value, int):
                    tgt = od.create_integer_value(value_name, value)
                elif isinstance(value, str):
                    tgt = od.create_string_value(value_name, value)
                elif isinstance(value, _Code):
                    tgt = od.create_actioncode_value(value_name, value.code)
                else:
                    raise Exception("Unimplemented type "+value)
                od.create_slot(attr_name, obj_name, tgt)

            return obj_name

    t = T(visit_tokens=True).transform(tree)

    return m

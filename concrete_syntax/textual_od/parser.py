# Parser for Object Diagrams textual concrete syntax

from lark import Lark, logger, Transformer
from lark.indenter import Indenter
from api.od import ODAPI
from services.scd import SCD
from concrete_syntax.common import _Code
from uuid import UUID

grammar = r"""
%import common.WS
%ignore WS
%ignore COMMENT

?start: object*

IDENTIFIER: /[A-Za-z_][A-Za-z_0-9]*/
COMMENT: /#[^\n]*/

literal: INT
       | STR
       | BOOL
       | CODE
       | INDENTED_CODE

INT: /[0-9]+/
STR: /"[^"]*"/
   | /'[^']*'/
BOOL: "True" | "False"
CODE: /`[^`]*`/
INDENTED_CODE: /```[^`]*```/

type_name: IDENTIFIER

#        name (optional)      type        
object: [IDENTIFIER]     ":"  type_name [link_spec | rev_link_spec] ["{" slot* "}"]

link_spec:     "(" IDENTIFIER "->" IDENTIFIER ")"
rev_link_spec: "(" IDENTIFIER "<-" IDENTIFIER ")"

slot: IDENTIFIER "=" literal ";"
"""

parser = Lark(grammar, parser='lalr', propagate_positions=True)

class DefaultNameGenerator:
    def __init__(self):
        self.counter = 0

    def __call__(self, type_name):
        name = f"__{type_name}_{self.counter}"
        self.counter += 1
        return name

# given a concrete syntax text string, and a meta-model, parses the CS
# Parameter 'type_transform' is useful for adding prefixes to the type names, when parsing a model and pretending it is an instance of a prefixed meta-model.
def parse_od(state,
    m_text, # text to parse
    mm, # meta-model of model that will be parsed. The meta-model must already have been parsed.
    type_transform=lambda type_name: type_name,
    name_generator=DefaultNameGenerator(), # exception to raise if anonymous (nameless) object/link occurs in the model. Main reason for this is to forbid them in LHS of transformation rules.
):
    tree = parser.parse(m_text)

    m = state.create_node()
    od = ODAPI(state, m, mm)

    primitive_types = {
        type_name : UUID(state.read_value(state.read_dict(state.read_root(), type_name)))
            for type_name in ["Integer", "String", "Boolean", "ActionCode"]
    }

    class T(Transformer):
        def __init__(self, visit_tokens):
            super().__init__(visit_tokens)

        def IDENTIFIER(self, token):
            return (str(token), token.line)
        
        def INT(self, token):
            return (int(token), token.line)

        def BOOL(self, token):
            return (token == "True", token.line)

        def STR(self, token):
            return (str(token[1:-1]), token.line) # strip the "" or ''

        def CODE(self, token):
            return (_Code(str(token[1:-1])), token.line) # strip the ``

        def INDENTED_CODE(self, token):
            skip = 4 # strip the ``` and the following newline character
            space_count = 0
            while token[skip+space_count] == " ":
                space_count += 1
            lines = token.split('\n')[1:-1]
            for line in lines:
                if len(line) >= space_count and line[0:space_count] != ' '*space_count:
                    raise Exception("wrong indentation of INDENTED_CODE")
            unindented_lines = [l[space_count:] for l in lines]
            return (_Code('\n'.join(unindented_lines)), token.line)

        def literal(self, el):
            return el[0]

        def link_spec(self, el):
            [(src, src_line), (tgt, _)] = el
            return (src, tgt, src_line)

        def rev_link_spec(self, el):
            [(tgt, tgt_line), (src, _)] = el # <-- reversed :)
            return (src, tgt, tgt_line)

        def type_name(self, el):
            type_name, line = el[0]
            if type_name in primitive_types:
                return (type_name, line)
            else:
                return (type_transform(type_name), line)
        
        def slot(self, el):
            [(attr_name, line), (value, _)] = el
            return (attr_name, value, line)
        
        def object(self, el):
            [obj, (type_name, line), link] = el[0:3]
            slots = el[3:]
            try:
                if obj != None:
                    (obj_name, _) = obj
                else:
                    # anonymous object - auto-generate a name
                    obj_name = name_generator(type_name)
                if state.read_dict(m, obj_name) != None:
                    msg = f"Element '{obj_name}:{type_name}': name '{obj_name}' already in use."
                    raise Exception(msg + " Names must be unique")
                    # print(msg + " Ignoring.")
                    return
                if link == None:
                    obj_node = od.create_object(obj_name, type_name)
                else:
                    (src, tgt, _) = link
                    if tgt in primitive_types:
                        if state.read_dict(m, tgt) == None:
                            scd = SCD(m, state)
                            scd.create_model_ref(tgt, primitive_types[tgt])
                    src_obj = od.get(src)
                    tgt_obj = od.get(tgt)
                    obj_node = od.create_link(obj_name, type_name, src_obj, tgt_obj)
                # Create slots
                for attr_name, value, line in slots:
                    if isinstance(value, _Code):
                        od.set_slot_value(obj_node, attr_name, value.code, is_code=True)
                    else:
                        od.set_slot_value(obj_node, attr_name, value)

                return obj_name
            except Exception as e:
                # raising a *new* exception (instead of adding a note to the existing exception) because Lark will also raise a new exception, and ignore our note:
                raise Exception(f"at line {line}:\n  " + m_text.split('\n')[line-1] + "\n"+ str(e)) from e

    t = T(visit_tokens=True).transform(tree)

    return m

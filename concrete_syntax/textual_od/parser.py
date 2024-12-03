# Parser for Object Diagrams textual concrete syntax

from lark import Lark, logger
from lark.indenter import Indenter
from api.od import ODAPI
from services.scd import SCD
from concrete_syntax.common import _Code, TBase
from uuid import UUID

grammar = r"""
%import common.WS
%ignore WS
%ignore COMMENT

?start: object*

IDENTIFIER: /[A-Za-z_][A-Za-z_0-9]*/
COMMENT: /#[^\n]*\n/

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
object: [IDENTIFIER]     ":"  type_name [link_spec] ["{" slot* "}"]

link_spec: "(" IDENTIFIER "->" IDENTIFIER ")"

slot: IDENTIFIER "=" literal ";"
"""

parser = Lark(grammar, parser='lalr')

# given a concrete syntax text string, and a meta-model, parses the CS
# Parameter 'type_transform' is useful for adding prefixes to the type names, when parsing a model and pretending it is an instance of a prefixed meta-model.
def parse_od(state, m_text, mm, type_transform=lambda type_name: type_name):
    tree = parser.parse(m_text)

    m = state.create_node()
    od = ODAPI(state, m, mm)

    primitive_types = {
        type_name : UUID(state.read_value(state.read_dict(state.read_root(), type_name)))
            for type_name in ["Integer", "String", "Boolean", "ActionCode"]
    }

    class T(TBase):
        def __init__(self, visit_tokens):
            super().__init__(visit_tokens)
            self.obj_counter = 0 # used for generating unique names for anonymous objects

        def link_spec(self, el):
            [src, tgt] = el
            return (src, tgt)

        def type_name(self, el):
            type_name = el[0]
            if type_name in primitive_types:
                return type_name
            else:
                return type_transform(el[0])
        
        def slot(self, el):
            [attr_name, value] = el
            return (attr_name, value)
        
        def object(self, el):
            [obj_name, type_name, link] = el[0:3]
            slots = el[3:]
            if state.read_dict(m, obj_name) != None:
                msg = f"Element '{obj_name}:{type_name}': name '{obj_name}' already in use."
                # raise Exception(msg + " Names must be unique")
                print(msg + " Ignoring.")
                return
            if obj_name == None:
                # object/link names are optional
                #  generate a unique name if no name given
                obj_name = f"__{type_name}_{self.obj_counter}"
                self.obj_counter += 1
            if link == None:
                obj_node = od.create_object(obj_name, type_name)
            else:
                src, tgt = link
                if tgt in primitive_types:
                    if state.read_dict(m, tgt) == None:
                        scd = SCD(m, state)
                        scd.create_model_ref(tgt, primitive_types[tgt])
                src_obj = od.get(src)
                tgt_obj = od.get(tgt)
                obj_node = od.create_link(obj_name, type_name, src_obj, tgt_obj)
            # Create slots
            for attr_name, value in slots:
                if isinstance(value, _Code):
                    od.set_slot_value(obj_node, attr_name, value.code, is_code=True)
                else:
                    od.set_slot_value(obj_node, attr_name, value)

            return obj_name

    t = T(visit_tokens=True).transform(tree)

    return m

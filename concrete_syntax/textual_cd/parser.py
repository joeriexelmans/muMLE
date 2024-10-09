from lark import Lark, logger
from concrete_syntax.common import _Code, TBase
from uuid import UUID
from services.scd import SCD
from services.od import OD

grammar = r"""
%import common.WS
%ignore WS
%ignore COMMENT

?start: (class_ | association | global_constraint)*

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

INT_OR_INF: INT | "*"

multiplicity: "[" INT ".." INT_OR_INF "]"

ABSTRACT: "abstract"

superclasses: IDENTIFIER ("," IDENTIFIER)*

attrs: attr*

constraint: CODE | INDENTED_CODE

class_: [ABSTRACT] "class" IDENTIFIER [multiplicity] ["(" superclasses ")"]  ["{" attrs [constraint] "}"]

association: "association" IDENTIFIER  [multiplicity] IDENTIFIER "->" IDENTIFIER [multiplicity] ["{" [constraint] "}"]

OPTIONAL: "optional"

attr: [OPTIONAL] IDENTIFIER IDENTIFIER [constraint] ";"

global_constraint: "global" IDENTIFIER constraint
"""

parser = Lark(grammar, parser='lalr')

def _handle_missing_multiplicity(multiplicity):
    if multiplicity != None:
        return multiplicity
    else:
        return (None, None)


def parse_cd(state, m_text):
    type_model_id = state.read_dict(state.read_root(), "SCD")
    scd_mmm = UUID(state.read_value(type_model_id))

    m = state.create_node()
    cd = SCD(m, state)
    od = OD(scd_mmm, m, state)

    def _add_constraint_to_obj(obj_name, constraint):
        c = od.create_actioncode_value(f"{obj_name}.constraint", constraint.code)
        od.create_slot("constraint", obj_name, c)

    primitive_types = {
        type_name : UUID(state.read_value(state.read_dict(state.read_root(), type_name)))
            for type_name in ["Integer", "String", "Boolean"]
    }

    class T(TBase):
        def __init__(self, visit_tokens):
            super().__init__(visit_tokens)
            self.obj_counter = 0

        def ABSTRACT(self, el):
            return True

        def INT_OR_INF(self, el):
            return float('inf') if el == "*" else int(el)

        def multiplicity(self, el):
            [lower, upper] = el
            return (lower, upper)

        def superclasses(self, el):
            return list(el)

        def attrs(self, el):
            return list(el)

        def constraint(self, el):
            return el[0]

        def attr(self, el):
            [optional, attr_type, attr_name, constraint] = el
            return (optional == "optional", attr_type, attr_name, constraint)

        def global_constraint(self, el):
            [name, constraint] = el
            od.create_object(name, "GlobalConstraint")
            _add_constraint_to_obj(name, constraint)

        def class_(self, el):
            [abstract, class_name, multiplicity, super_classes, attrs, constraint] = el
            (lower, upper) = _handle_missing_multiplicity(multiplicity)
            cd.create_class(class_name, abstract, lower, upper)
            if super_classes != None:
                for super_class in super_classes:
                    cd.create_inheritance(class_name, super_class)
            if constraint != None:
                _add_constraint_to_obj(class_name, constraint)
            if attrs != None:
                for attr in attrs:
                    (optional, attr_type, attr_name, constraint) = attr
                    # TODO: only create type ref if it doesn't exist yet
                    cd.create_model_ref(attr_type, primitive_types[attr_type])
                    cd.create_attribute_link(class_name, attr_type, attr_name, optional)
                    if constraint != None:
                        _add_constraint_to_obj(f"{class_name}_{attr_name}", constraint)

        def association(self, el):
            [assoc_name, src_multiplicity, src_name, tgt_name, tgt_multiplicity, constraint] = el
            (src_lower, src_upper) = _handle_missing_multiplicity(src_multiplicity)
            (tgt_lower, tgt_upper) = _handle_missing_multiplicity(tgt_multiplicity)
            cd.create_association(assoc_name, src_name, tgt_name, src_lower, src_upper, tgt_lower, tgt_upper)
            if constraint != None:
                _add_constraint_to_obj(class_name, constraint)

    tree = parser.parse(m_text)
    t = T(visit_tokens=True).transform(tree)

    return m

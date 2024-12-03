import os.path
from framework.conformance import Conformance, render_conformance_check_result
from concrete_syntax.textual_od import parser
from concrete_syntax.common import indent
from transformation.rule import Rule

# parse model and check conformance
def parse_and_check(state, m_cs, mm, descr: str, check_conformance=True, type_transform=lambda type_name: type_name):
    try:
        m = parser.parse_od(
            state,
            m_text=m_cs,
            mm=mm,
            type_transform=type_transform,
        )
    except Exception as e:
        e.add_note("While parsing model " + descr)
        raise
    try:
        if check_conformance:
            conf = Conformance(state, m, mm)
            errors = conf.check_nominal()
            if len(errors) > 0:
                print(render_conformance_check_result(errors))
    except Exception as e:
        e.add_note("In model " + descr)
        raise
    return m

# get file contents as string
def read_file(filename):
    with open(filename) as file:
        return file.read()

KINDS = ["nac", "lhs", "rhs"]

# load model transformation rules
def load_rules(state, get_filename, rt_mm_ramified, rule_names, check_conformance=True):
    rules = {}

    files_read = []

    for rule_name in rule_names:
        rule = {}

        def parse(kind):
            filename = get_filename(rule_name, kind)
            descr = "'"+filename+"'"
            if kind == "nac":
                suffix = ""
                nacs = []
                try:
                    while True:
                        base, ext = os.path.splitext(filename)
                        processed_filename = base+suffix+ext
                        nac = parse_and_check(state, read_file(processed_filename), rt_mm_ramified, descr, check_conformance)
                        nacs.append(nac)
                        suffix = "2" if suffix == "" else str(int(suffix)+1)
                        files_read.append(processed_filename)
                except FileNotFoundError:
                    if suffix == "":
                        print(f"Warning: rule {rule_name} has no NAC ({filename} not found)")
                return nacs
            elif kind == "lhs" or kind == "rhs":
                try:
                    m = parse_and_check(state, read_file(filename), rt_mm_ramified, descr, check_conformance)
                    files_read.append(filename)
                    return m
                except FileNotFoundError as e:
                    print(f"Warning: using empty {kind} ({filename} not found)")
                    # Use empty model as fill-in:
                    return parse_and_check(
                        state,
                        "",
                        rt_mm_ramified,
                        descr="'"+filename+"'",
                        check_conformance=check_conformance)

        rules[rule_name] = Rule(*(parse(kind) for kind in KINDS))

    print("Rules loaded:\n" + indent('\n'.join(files_read), 4))

    return rules

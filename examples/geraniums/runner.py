from examples.geraniums.renderer import render_geraniums_dot
from transformation.ramify import ramify

from models.eval_context import eval_context

from transformation.schedule.rule_scheduler import *

if __name__ == "__main__":
    import os
    THIS_DIR = os.path.dirname(__file__)

    # get file contents as string
    def read_file(filename):
        with open(THIS_DIR+'/'+filename) as file:
            return file.read()


    state = DevState()
    scd_mmm = bootstrap_scd(state)

    mm_cs           =         read_file('metamodels/mm.od')
    m_cs            =         read_file('models/example2.od')

    mm = parser_cd.parse_cd(
        state,
        m_text=mm_cs,
    )
    m = parser_od.parse_od(
        state, m_text=m_cs, mm=mm
    )
    conf_err = Conformance(
        state, m, mm
    ).check_nominal()
    print(render_conformance_check_result(conf_err))
    mm_ramified = ramify(state, mm)

    action_generator = RuleSchedular(state, mm, mm_ramified, verbose=True, directory="examples/geraniums", eval_context=eval_context)
    od = ODAPI(state, m, mm)
    render_geraniums_dot(od, f"{THIS_DIR}/geraniums.dot")

    # if action_generator.load_schedule(f"petrinet.od"):
    # if action_generator.load_schedule("schedules/combinatory.drawio"):
    if action_generator.load_schedule("schedules/schedule.drawio"):

        action_generator.generate_dot("../dot.dot")
        code, message = action_generator.run(od)
        print(f"{code}: {message}")
    render_geraniums_dot(od, f"{THIS_DIR}/geraniums_final.dot")
from state.devstate import DevState
from bootstrap.scd import bootstrap_scd
import models

state = DevState()
scd_mmm = bootstrap_scd(state)

mm, mm_rt, m, m_rt_initial = models.get_fibonacci(state, scd_mmm)
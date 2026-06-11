from time import sleep
from process import Process
from processBootstrap import ProcessBootstrap
from rt_process import RT_Process
from helpers import get_module_path


workflow_dir = get_module_path("models", "")
p = ProcessBootstrap(workflow_dir / "RTmodel.md")
# p.generate_dot("dot.dot")

RT_obj : RT_Process = p.generate_runtime_object(get_module_path("addons", "runtime_env.py"), get_module_path("models", ""))
RT_obj.start(step_trough=True)
# RT_obj.step()
# RT_obj.step()
RT_obj.step()
RT_obj.step()
# RT_obj : RT_Process = p.generate_runtime_object(get_module_path("addons", "runtime_env.py"))
# RT_obj.load(s)
# RT_obj.start(step_trough=True)
# RT_obj.step()
# RT_obj.step()

# sleep(10)
# RT_obj.stop()
p.visualise(RT_obj.rt_key, "RTdot.dot")

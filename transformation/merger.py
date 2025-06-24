from api.od import ODAPI
from uuid import UUID
from concrete_syntax.textual_od import parser, renderer
from services.scd import SCD
from util.timer import Timer

PRIMITIVE_TYPES = set(["Integer", "String", "Boolean", "ActionCode", "Bytes"])

# Merges N models. The models must have the same meta-model.
# Care should be taken to avoid naming collisions before calling this function.
def merge_models(state, mm, models: list[UUID]):
    with Timer("merge_models"):
        primitive_types = {
            type_name : UUID(state.read_value(state.read_dict(state.read_root(), type_name)))
                for type_name in ["Integer", "String", "Boolean", "ActionCode", "Bytes"]
        }

        merged = state.create_node()
        merged_odapi = ODAPI(state, m=merged, mm=mm)

        scd_mmm = UUID(state.read_value(state.read_dict(state.read_root(), "SCD")))

        mm_odapi = ODAPI(state, m=mm, mm=scd_mmm)
        types = mm_odapi.get_all_instances("Class", include_subtypes=True)
        all_objs = []
        for type_name, type_obj in types:
            for model in models:
                m_odapi = ODAPI(state, m=model, mm=mm)
                for obj_name, obj in m_odapi.get_all_instances(type_name, include_subtypes=False):
                    all_objs.append((obj_name, obj, type_name, m_odapi))
        todo = all_objs

        have = {}

        mapping = {}
        while len(todo) > 0:
            next_round = []
            # if 'mm' is SCD, class_name will be 'Class', 'Association', ...
            for tup in todo:
                obj_name, obj, type_name, m_odapi = tup
                prefixed_obj_name = obj_name
                if obj_name in PRIMITIVE_TYPES:
                    if prefixed_obj_name in have:
                        # Don't rename primitive types. Instead, merge them.
                        mapping[obj] = mapping[have[prefixed_obj_name]]
                        continue
                while prefixed_obj_name in have:
                    prefixed_obj_name = prefixed_obj_name + '_bis' # make name unique
                if prefixed_obj_name != obj_name:
                    print(f"Warning: renaming {obj_name} to {prefixed_obj_name} to avoid naming collision.")
                if type_name == "ModelRef":
                    model = state.read_value(obj)
                    scd = SCD(merged, state)
                    created_obj = scd.create_model_ref(prefixed_obj_name, model)
                    merged_odapi._ODAPI__recompute_mappings() # dirty!!
                else:
                    # create node or edge
                    if state.is_edge(obj):
                        source, target = state.read_edge(obj)
                        if source not in mapping or target not in mapping:
                            next_round.append(tup)
                            continue # try again later...
                        else:
                            created_obj = merged_odapi.create_link(prefixed_obj_name, type_name, mapping[source], mapping[target])
                    else:
                        created_obj = merged_odapi.create_object(prefixed_obj_name, type_name)
                mapping[obj] = created_obj
                have[obj_name] = obj
                # copy slots
                for attr_name in m_odapi.get_slots(obj):
                    value = m_odapi.get_slot_value(obj, attr_name)
                    is_code = m_odapi.slot_has_code(obj, attr_name)
                    merged_odapi.set_slot_value(created_obj, attr_name, value, is_code=is_code)
            if len(next_round) == len(todo):
                raise Exception("We got stuck!")
            todo = next_round

        return merged
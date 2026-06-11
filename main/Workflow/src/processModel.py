from typing import Dict, Any

from pydantic import BaseModel, RootModel, Field


class NodeModel(RootModel[Dict[str, Any]]):
    pass

class ProcessModel(BaseModel):
    Place: dict[str, NodeModel] = Field(default_factory=dict)
    Port: dict[str, NodeModel] = Field(default_factory=dict)
    Port_flow_out: list[Dict[str, Any]] = Field(default_factory=list)
    Port_data_out: list[Dict[str, Any]] = Field(default_factory=list)
    Port_flow_in: list[Dict[str, Any]] = Field(default_factory=list)
    Port_data_in: list[Dict[str, Any]] = Field(default_factory=list)
    Transition: list[Dict[str, Any]] = Field(default_factory=list)
    Data_flow: list[Dict[str, Any]] = Field(default_factory=list)

    RTState: dict[str, NodeModel] = Field(default_factory=dict)
    Running: list[Dict[str, Any]] = Field(default_factory=list)
    Port_data: dict[str, NodeModel] = Field(default_factory=list)
    Port_data_connect: list[Dict[str, Any]] = Field(default_factory=list)
    RT_data_connect: list[Dict[str, Any]] = Field(default_factory=list)

    def to_class_diagram(self):
        a = f"{
        "\n".join(
            ["\n".join(
                [f"{name}:{var} {{{
                "".join(
                    [f"\n\t{key} = {f"\"{value}\"" if isinstance(value, str) else value};"
                     for key, value in node.root.items()]
                )}\n}}"
                 for name, node in getattr(self, var).items()]
            )
                for var in ["Place", "Port", "RTState", "Port_data"]])
        }\n\n{
        "\n".join(
            ["\n".join(
                [f":{var} ({values["source"]} -> {values["target"]}) {{{
                "".join([f"\n\t{param}=\"{values[param]}\";"
                         for param in (values.keys() - {"source", "target"})])
                }\n}}"
                 for values in getattr(self, var)]
            )
                for var in ["Transition", "Data_flow", "Port_flow_in", "Port_flow_out", "Port_data_in", "Port_data_out", "Running", "RT_data_connect", "Port_data_connect"]])
        }"
        print(a)
        return a


def create_workflow(content: dict) -> ProcessModel:
    kwargs = {
        "Place": {
            f"a{n['id']}": {"Name": n["meta"]["label"], "Process": n["meta"]["activity"], "Start": n["meta"]["start"], "Sync": n["meta"]["sync"]}             for n in content["nodes"]},
        "Port": {f"a{n['id']}{key}{port['id']}": {"Name": port['name']} for n in content["nodes"] for key, value in
                 n["ports"].items() for port in value},
        "RTState": {
            "rt_state": {}
        },
        "Running": [{'source': 'rt_state', 'target': f"a{n['id']}", "Id": ''} for n in content["nodes"] if
                    n["meta"]["start"]],
        "Transition": [{"source": f"a{n["source"]}{n["sourceHandle"]}", "target": f"a{n["target"]}{n["targetHandle"]}"}
                       for n in content["edges"] if n["sourceHandle"][:4] == "flow"],
        "Data_flow": [{"source": f"a{n["source"]}{n["sourceHandle"]}", "target": f"a{n["target"]}{n["targetHandle"]}"}
                      for n in content["edges"] if n["sourceHandle"][:4] == "data"],
        "Port_data_connect": [{"source": f"d{n["id"]}data_out{port["id"]}", "target": f"a{n["id"]}data_out{port["id"]}"}
                              for n in content["nodes"] for key, value in n["ports"].items() if key == "data_out" for
                              port in value]
    }
    kwargs["Port_data"] = {d["source"]: {"Value": "None"} for d in kwargs["Port_data_connect"]}
    kwargs["RT_data_connect"] = [{"source": "rt_state", "target": d} for d in kwargs["Port_data"]]
    for field, key in [("Port_data_in", "data_in"), ("Port_data_out", "data_out"), ("Port_flow_in", "flow_in"),
                       ("Port_flow_out", "flow_out")]:
        kwargs[field] = (
        [{"source": f"a{n["id"]}", "target": f"a{n['id']}{key}{port['id']}"} for n in content["nodes"] for port in
         n["ports"][key]])

    return ProcessModel(**kwargs)
from state.base import State
from bootstrap.scd import bootstrap_scd
from services import implemented as services
from framework.conformance import Conformance
from uuid import UUID


class Manager:
    def __init__(self, state: State):
        self.current_model = None
        self.current_context = None
        self.state = state
        bootstrap_scd(state)
        scd_node = self.state.read_dict(self.state.read_root(), "SCD")
        for key_node in self.state.read_dict_keys(self.state.read_root()):
            model_node = self.state.read_dict_node(self.state.read_root(), key_node)
            self.state.create_edge(model_node, scd_node)

    def get_models(self):
        for key_node in self.state.read_dict_keys(self.state.read_root()):
            yield self.state.read_value(key_node)

    def instantiate_model(self, type_model_name: str, name: str):
        root = self.state.read_root()
        type_model_node = self.state.read_dict(root, type_model_name)
        if type_model_node is None:
            raise RuntimeError(f"No type model with name {type_model_name} found.")
        else:
            # check if model is a linguistic type model
            scd_node = self.state.read_dict(self.state.read_root(), "SCD")
            incoming = self.state.read_incoming(scd_node)
            incoming = [self.state.read_edge(e)[0] for e in incoming]
            if type_model_node not in incoming:
                raise RuntimeError(f"Model with name {type_model_name} is not a type model.")
        if name in map(self.state.read_value, self.state.read_dict_keys(root)):
            raise RuntimeError(f"Model with name {name} already exists.")
        new_model_root = self.state.create_node()
        new_model_node = self.state.create_nodevalue(str(new_model_root))
        self.state.create_dict(root, name, new_model_node)
        self.state.create_edge(new_model_node, type_model_node)
        self.current_model = (name, new_model_root)
        if type_model_name not in services:
            raise RuntimeError(f"Services for type {type_model_name} not implemented.")
        self.current_context = services[type_model_name](self.current_model[1], self.state)

    def select_model(self, name: str):
        root = self.state.read_root()
        model_node = self.state.read_dict(root, name)
        if model_node is None:
            raise RuntimeError(f"No model with name {name} found.")
        model_root = UUID(self.state.read_value(model_node))
        self.current_model = (name, model_root)

    def close_model(self):
        self.current_model = None
        self.current_context = None

    def get_types(self):
        root = self.state.read_root()
        if self.current_model is None:
            raise RuntimeError(f"No model currently selected.")
        name, model = self.current_model
        model_id = self.state.read_dict(root, name)
        outgoing = self.state.read_outgoing(model_id)
        outgoing = [e for e in outgoing if len(self.state.read_outgoing(e)) == 0]
        elements = [self.state.read_edge(e)[1] for e in outgoing]
        for e in elements:
            incoming = self.state.read_incoming(e)
            label_edge, = [e for e in incoming if len(self.state.read_outgoing(e)) == 1]
            label_edge, = self.state.read_outgoing(label_edge)
            _, label_node = self.state.read_edge(label_edge)
            yield self.state.read_value(label_node)

    def select_context(self, name: str):
        if name not in self.get_types():
            raise RuntimeError(f"No type {name} that currently selected model conforms to.")
        if name not in services:
            raise RuntimeError(f"Services for type {name} not implemented.")
        self.current_context = services[name](self.current_model[1], self.state)
        self.current_context.from_bottom()

    def close_context(self):
        self.current_context.to_bottom()
        self.current_context = None

    def get_services(self):
        if self.current_model is None:
            raise RuntimeError(f"No model currently selected.")
        if self.current_context is None:
            raise RuntimeError(f"No context currently selected.")
        yield from [
            getattr(self.current_context, func)
            for func in dir(self.current_context)
            if callable(getattr(self.current_context, func))
            and not func.startswith("__")
            and not func == "from_bottom"
            and not func == "to_bottom"
        ]

    def check_conformance(self, type_model_name: str, model_name: str):
        root = self.state.read_root()
        type_model_node = self.state.read_dict(root, type_model_name)
        if type_model_node is None:
            raise RuntimeError(f"No type model with name {type_model_name} found.")
        model_node = self.state.read_dict(root, model_name)
        if model_node is None:
            raise RuntimeError(f"No model with name {model_node} found.")
        types = self.state.read_outgoing(model_node)
        types = [self.state.read_edge(e)[1] for e in types]
        if type_model_node not in types:
            conf = Conformance(self.state,
                               UUID(self.state.read_value(model_node)),
                               UUID(self.state.read_value(type_model_node))).check_structural(log=True)
            if conf:
                self.state.create_edge(model_node, type_model_node)
            return conf
        else:
            return Conformance(self.state,
                               UUID(self.state.read_value(model_node)),
                               UUID(self.state.read_value(type_model_node))).check_nominal(log=True)

    def dump_state(self):
        import pickle
        with open("state.p", "wb") as file:
            pickle.dump(self.state, file)

    def load_state(self):
        import pickle
        with open("state.p", "rb") as file:
            self.state = pickle.load(file)


if __name__ == '__main__':
    from state.devstate import DevState
    s = DevState()
    m = Manager(s)
    m.select_model("SCD")
    m.select_context("SCD")
    for f in m.get_services():
        print(f)

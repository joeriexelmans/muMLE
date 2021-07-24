from state.base import State
from uuid import UUID


class Manager:
    def __init__(self, state: State):
        self._state = state
        bottom = self._state.create_node()
        bottom_id = self._state.create_nodevalue(str(bottom))
        bottom_label = self._state.create_nodevalue("Bottom")
        to_uuid = self._state.create_edge(self._state.read_root(), bottom_id)
        to_label = self._state.create_edge(self._state.read_root(), bottom_label)
        self._state.create_edge(to_label, bottom_id)
        self._state.create_edge(to_uuid, bottom_label)

    @property
    def models(self):
        root = self._state.read_root()
        for key in self._state.read_dict_keys(root):
            try:
                UUID(key)  # checks whether the key is a valid UUID
                name_node = self._state.read_dict(root, key)
                name = self._state.read_value(name_node)
                yield key, name
            except ValueError:
                pass


if __name__ == '__main__':
    from state.devstate import DevState
    m = Manager(DevState())
    print(list(m.models))

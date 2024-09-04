from uuid import UUID
from state.base import State
from services.bottom.V0 import Bottom
from services.primitives.float_type import Float


class PointCartesian:
    """
    Implements services for the point cartesian LTM.
    Implementation is done in terms of Python data structures
    """
    def __init__(self, model: UUID, state: State):
        type_model_id = state.read_dict(state.read_root(), "PointCartesian")
        self.type_model = UUID(state.read_value(type_model_id))
        self.model = model
        self.state = state

        self.point = None

    def create_point(self, x: float, y: float):
        """
        Creates a point.

        Args:
            x: x coordinate
            y: y coordinate

        Returns:
            Nothing.
        """
        if self.point == None:
            self.point = (x, y)
        else:
            raise RuntimeError("A PointCartesian model can contain at most 1 point.")

    def read_point(self):
        """
        Reads point.

        Returns:
            Textual representation of the point data.
        """
        if self.point == None:
            raise RuntimeError("No point found in model.")
        else:
            return f"(X = {self.point[0]}, Y = {self.point[1]})"

    def delete_point(self):
        """
        Deletes point.

        Returns:
            Nothing.
        """
        self.point = None

    def apply_movement(self, delta_x: float, delta_y: float):
        """
        Moves point.

        Args:
            delta_x: change in x dimension
            delta_y: change in y dimension

        Returns:
            Nothing.
        """
        if self.point != None:
            self.point = (self.point[0] + delta_x, self.point[1] + delta_y)
        else:
            raise RuntimeError("No point found in model.")

    def to_bottom(self):
        """
        Converts implementation specific model representation to 
        canonical representation.

        Returns:
            Nothing.
        """
        bottom = Bottom(self.state)
        # clear residual model
        for element in bottom.read_outgoing_elements(self.model):
            bottom.delete_element(element)
        # create primitive models
        c1_model = bottom.create_node()
        c2_model = bottom.create_node()
        Float(c1_model, self.state).create(self.point[0])
        Float(c2_model, self.state).create(self.point[1])
        # instantiate Point class
        point_node = bottom.create_node()  # create point node
        bottom.create_edge(self.model, point_node, "point")  # attach to model
        morph_node, = bottom.read_outgoing_elements(self.type_model, "PointCartesian")  # retrieve type
        bottom.create_edge(point_node, morph_node, "Morphism")  # create morphism link
        # instantiate c1 attribute
        c1_node = bottom.create_node(str(c1_model))
        bottom.create_edge(self.model, c1_node, "point.c1")
        c1_link = bottom.create_edge(point_node, c1_node)
        bottom.create_edge(self.model, c1_link, "point.c1_link")
        ltm_point_node, = bottom.read_outgoing_elements(self.type_model, "Float")
        ltm_point_link, = bottom.read_outgoing_elements(self.type_model, "PointCartesian_c1")
        bottom.create_edge(c1_node, ltm_point_node, "Morphism")
        bottom.create_edge(c1_link, ltm_point_link, "Morphism")
        # instantiate c2 attribute
        c2_node = bottom.create_node(str(c2_model))
        bottom.create_edge(self.model, c2_node, "point.c2")
        c2_link = bottom.create_edge(point_node, c2_node)
        bottom.create_edge(self.model, c2_link, "point.c2_link")
        ltm_point_node, = bottom.read_outgoing_elements(self.type_model, "Float")
        ltm_point_link, = bottom.read_outgoing_elements(self.type_model, "PointCartesian_c2")
        bottom.create_edge(c2_node, ltm_point_node, "Morphism")
        bottom.create_edge(c2_link, ltm_point_link, "Morphism")

    def from_bottom(self):
        """
        Converts canonical representation to 
        implementation specific model representation.

        Returns:
            Nothing.
        """
        bottom = Bottom(self.state)
        keys = bottom.read_keys(self.model)
        x_key, = filter(lambda k: k.endswith(".c1"), keys)
        y_key, = filter(lambda k: k.endswith(".c2"), keys)
        x_ref_node, = bottom.read_outgoing_elements(self.model, x_key)
        y_ref_node, = bottom.read_outgoing_elements(self.model, y_key)
        x_model = UUID(bottom.read_value(x_ref_node))
        y_model = UUID(bottom.read_value(y_ref_node))
        x_val_node, = bottom.read_outgoing_elements(x_model)
        y_val_node, = bottom.read_outgoing_elements(y_model)
        self.point = (bottom.read_value(x_val_node), bottom.read_value(y_val_node))


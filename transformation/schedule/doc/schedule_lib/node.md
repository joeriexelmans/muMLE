## Node Module

Defines the abstract base Node class for graph-based structures. Each Node is assigned
a unique identifier via an external IdGenerator. The class provides an interface for
managing execution state and generating DOT graph representations using Jinja2 templates.

### Class: `Node`

- **Attributes**
  - `id: int`: A unique identifier assigned to each instance upon initialization.

- **Methods**
  - `get_id` 
    - returns: `int`, The unique node ID
    
    Retrieves the unique identifier of the node.

  - `generate_stack_frame`
    - exec_id: `int`, The ID of the execution context.
    - returns: `None`
      
    Initializes a new state frame for a specific execution context.
    Designed to be overridden in subclasses that use execution state.
    
  - `delete_stack_frame`
    - exec_id: `int`, The ID of the execution context.
    - returns: `None`
      
    Deletes the state frame for a specific execution context.
    Designed to be overridden in subclasses that use execution state.
    
  - `generate_dot`
    - nodes: `list[str]`, A list to append DOT node definitions to.
    - edges: `list[str]`, A list to append DOT edges definitions to.
    - visited: `set[str]`, A set of already visited node IDs to avoid duplicates or recursion.
    - template: `list[str]`, A Jinja2 template used to format the node's DOT representation.
    - returns: `None`
      
    Generates the DOT graph representation for this node and its relationships.
    Must be implemented in subclasses.
    
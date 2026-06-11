import React from "react";
import {NodeTemplate} from "../../models/Graph.jsx";
import {useGraph} from "../../hooks/Graph.jsx";
// import NodeTemplate from "../../models/Graph.jsx"

export default function GraphPanel({ Graph, API, lastClickPosition }) {
    const [graph, setGraph] = Graph
    const getLowestFreeId = (nodes) => {
      const existingIds = new Set(nodes.map(n => parseInt(n.id, 10)));
      let id = 1;

      while (existingIds.has(id)) {
        id++;
      }

      return id;
    };


    // --- Add Node ---
    const addNode = () => {
        const newId = getLowestFreeId(graph.nodes);
        const newNode = NodeTemplate(newId, "custom", lastClickPosition.x, lastClickPosition.y)
        setGraph(prev => ({
            ...prev,
            nodes: [...prev.nodes, newNode]
        }));
    };

    const {loadGraph, saveGraph} = useGraph(graph, setGraph, API);

    return (
        <div className="graph-pannel">
            {/*<button className="save-graph" onClick={loadGraph}>*/}
            {/*    💾 Load*/}
            {/*</button>*/}
            {/*<button className="save-graph" onClick={saveGraph}>*/}
            {/*    💾 Save*/}
            {/*</button>*/}
            <button className="add-node" onClick={addNode}>
                ➕ Add Node
            </button>
        </div>
    );
}
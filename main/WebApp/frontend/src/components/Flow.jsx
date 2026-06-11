import React, {useCallback, useMemo, useRef} from "react";
import ReactFlow, {
  Background,
  Controls,
  applyNodeChanges,
  applyEdgeChanges
} from "reactflow";

import "reactflow/dist/style.css";
import "./Flow.css"
import CustomNode from "../assets/CustomNode.jsx";
import {EdgeTemplate} from "../models/Graph.jsx";


export default function GraphViewer({
    Graph,
    setSelectedNode,
    setLastClickPosition
                                    }) {
    const [graph, setGraph] = Graph;
    const nodeTypes = useMemo(() => ({custom: CustomNode}), []);
    const reactFlowInstanceRef = useRef(null);

    const memoNodes = useMemo(() => {
            return graph.nodes.map(n => ({
                id: n.id,
                type: n.type || "custom",
                position: n.position,
                data: {
                    ...n.data,
                },
                width: n.width,
                height: n.height,
                selected: n.selected,
            }))
        },
        [graph]
    );
    // Handle user dragging nodes
    const onNodesChange = useCallback(
        (changes) => {
            setGraph(prev => ({
                ...prev,
                nodes: applyNodeChanges(changes, prev.nodes).map(n => ({
                    ...n,
                    data: {
                        ...n.data,
                        width: n.width,
                        height: n.height
                    }
                }))
            }));
        },
        [setGraph]
    );

    const isValidConnection = useCallback((connection) => {
        const {sourceHandle, targetHandle} = connection;

        if (!sourceHandle || !targetHandle)
            return false;

        const isFlow =
            sourceHandle.startsWith("flow_") &&
            targetHandle.startsWith("flow_");

        const isData =
            sourceHandle.startsWith("data_") &&
            targetHandle.startsWith("data_");
        console.log(connection)
        return isFlow || isData;
    }, []);

    // Handle edge changes (optional)
    const onEdgesChange = useCallback(
        (changes) => {
            console.log(changes)
            setGraph(prev => ({
                ...prev,
                edges: applyEdgeChanges(changes, prev.edges)
            }));
        },
        [setGraph]
    );

    const getLowestFreeId = (nodes) => {
        const existingIds = new Set(nodes.map(n => parseInt(n.id, 10)));
        let id = 1;

        while (existingIds.has(id)) {
            id++;
        }

        return id.toString();
    };

    const onConnect = useCallback(
        (connection) => {
            const newId = getLowestFreeId(graph.edges);
            const newEdge = EdgeTemplate(newId, connection.source, connection.sourceHandle, connection.target, connection.targetHandle)
            console.log(connection)
            setGraph(prev => ({
                ...prev,
                edges: [...prev.edges, newEdge]
            }));
        }, [graph.edges, setGraph]
    );

    const onSelectionChange = useCallback(({nodes}) => {
        // Only keep ONE selected node
        setSelectedNode(nodes.length === 1 ? nodes[0].id : null);
    }, [setSelectedNode]);

    const onCanvasClick = (event) => {
        setLastClickPosition(reactFlowInstanceRef.current.screenToFlowPosition({x: event.clientX, y: event.clientY}));
    };


    return (
        <div style={{width: "100%", height: "100%"}}>
            <ReactFlow
                nodes={memoNodes}
                edges={graph.edges}
                nodeTypes={nodeTypes}
                onInit={(instance) => {
                    reactFlowInstanceRef.current = instance;
                }}
                isValidConnection={isValidConnection}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onSelectionChange={onSelectionChange}
                onClick={onCanvasClick}
                snapToGrid
                snapGrid={[5, 5]}
            >
                <Background
                    variant="dots"
                    gap={20}
                    size={1}
                />
                <Controls/>
            </ReactFlow>

        </div>
    );
}
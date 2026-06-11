import React, {useEffect, useState} from "react";
import MyTextArea from "../../assets/MyTextArea.jsx";
import MyCheckBox from "../../assets/MyCheckBox.jsx";
import PortsEditor from "./PortsEditor.jsx"
import Panel from "./panel.jsx"
import "./NodePanel.css"

export function GraphPanel({Graph, selectedNode}) {
    const [localData, setLocalData] = useState(null);
    const [portsOpen, setPortsOpen] = useState(true);
    const [graph, setGraph] = Graph;

    useEffect(() => {
        setLocalData(() => graph.nodes.find(n => n.id === selectedNode) || null)
    }, [graph.nodes, selectedNode]);

    useEffect(() => {
        if (!localData) return;
        const node = graph.nodes.find(n => n.id === localData.id);
        const same =
            node.data.meta.label === localData.data.meta.label &&
            node.data.meta.description === localData.data.meta.description &&
            node.data.meta.activity === localData.data.meta.activity &&
            node.data.meta.start === localData.data.meta.start &&
            node.data.meta["sync"] === localData.data.meta["sync"] &&
            JSON.stringify(node.data.ports) === JSON.stringify(localData.data.ports);
        if (same) return;
        const timeout = setTimeout(() => {
            setGraph(prev => ({
                ...prev,
                nodes: prev.nodes.map(n =>
                    n.id === localData.id
                        ? {
                            ...n,
                            data: {
                                ...localData.data,
                                ports: Object.fromEntries(
                                    Object.entries(localData.data.ports).map(([key, value]) => [
                                        key,
                                        [...value]
                                    ])
                                ),
                            },
                            width: n.width + 0.1
                        }
                        : n,
                ),
            }));
        }, 200);

        return () => clearTimeout(timeout);
    }, [localData, setGraph]);

    if (!localData) {
        return (
            <div className="node-panel">
                <h3>No node selected</h3>
            </div>
        );
    }

    const updateMeta = (key, value) => {
        setLocalData(prev => ({
            ...prev,
            data: {
                ...prev.data,
                meta: {
                    ...prev.data.meta,
                    [key]: value
                },
            },
        }));
    };

    const updatePorts = (ports) => {
        setLocalData(prev => ({
            ...prev,
            data: {
                ...prev.data,
                ports,
            },
        }));
    };

    return (
        <Panel title="Node Inspector">
            <div className="node-panel-title">
                Node: {localData.type}_{localData.id}
            </div>
            <div className="node-section">
                <label>Name</label>
                <MyTextArea
                    value={localData.data.meta.label}
                    onChange={(e) =>
                        updateMeta("label", e.target.value)
                    }
                />
            </div>
            <div className="node-section">
                <label>Description</label>
                <MyTextArea
                    value={localData.data.meta.description}
                    onChange={(e) =>
                        updateMeta("description", e.target.value)
                    }
                />
            </div>
            <div className="node-section">
                <label>Activity Reference</label>
                <MyTextArea
                    value={localData.data.meta.activity}
                    onChange={(e) =>
                        updateMeta("activity", e.target.value)
                    }
                />
            </div>
            <div className="node-section">
                <MyCheckBox
                    value={localData.data.meta.start}
                    onChange={(e) =>
                        updateMeta("start", e.target.checked)
                    }
                />
                <span> Start node</span>
            </div>
            <div className="node-section">
                <MyCheckBox
                    value={localData.data.meta["sync"]}
                    onChange={(e) =>
                        updateMeta("sync", e.target.checked)
                    }
                />
                <span> Sync Inputs</span>
            </div>
            <div className="node-section">
                <button
                    className="ports-toggle"
                    onClick={() => setPortsOpen(v => !v)}
                >
                    {portsOpen ? "▼" : "▶"} Ports
                </button>

                {portsOpen && (
                    <PortsEditor
                        ports={localData.data.ports}
                        onChange={updatePorts}
                    />
                )}
            </div>
        </Panel>
    );
}
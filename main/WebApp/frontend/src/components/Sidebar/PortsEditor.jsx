import React from "react";
import MyTextArea from "../../assets/MyTextArea.jsx";
import "./PortsEditor.css";

export default function PortsEditor({ ports, onChange }) {

    const updatePortName = (category, index, value) => {
        const next = {
            ...ports,
            [category]: [...ports[category]]
        };

        next[category][index].name = value;
        onChange(next);
    };

    const removePort = (category, index) => {
        const next = {
            ...ports,
            [category]: ports[category].filter((_, i) => i !== index)
        };

        onChange(next);
    };

    const addPort = (category) => {
        const existing = ports[category] || [];

        const exists = (id) => existing.some(p => p.id === id);

        let id = existing.length + 1;

        while (exists(id)) {
            id += 1;
        }

        const next = {
            ...ports,
            [category]: [
                ...existing,
                {
                    id,
                    name: `new_port_${id}`
                }
            ]
        };

        onChange(next);
    };

    const movePort = (category, index, direction) => {
        const arr = [...ports[category]];

        const target = index + direction;

        if (target < 0 || target >= arr.length)
            return;

        [arr[index], arr[target]] = [arr[target], arr[index]];

        onChange({
            ...ports,
            [category]: arr
        });
    };

    const categories = [
        ["flow_in", "Flow In"],
        ["flow_out", "Flow Out"],
        ["data_in", "Data In"],
        ["data_out", "Data Out"]
    ];

    return (
        <>
            {categories.map(([key, label]) => (
                <div key={key} className="ports-category">
                    <div className="ports-title">
                        {label}
                    </div>

                    {ports[key].map((port, index) => (
                        <div
                            key={`${key}-${index}`}
                            className="port-row"
                        >
                            <button
                                className="port-btn"
                                onClick={() =>
                                    movePort(key, index, -1)
                                }
                            >
                                ↑
                            </button>

                            <button
                                className="port-btn"
                                onClick={() =>
                                    movePort(key, index, 1)
                                }
                            >
                                ↓
                            </button>
                            <MyTextArea
                                value={port.name}
                                onChange={(e) =>
                                    updatePortName(
                                        key,
                                        index,
                                        e.target.value
                                    )
                                }
                            />
                            <button
                                className="port-btn port-btn-danger"
                                onClick={() =>
                                    removePort(key, index)
                                }
                            >
                                ✕
                            </button>
                        </div>
                    ))}

                    <button
                        className="add-port-btn"
                        onClick={() => addPort(key)}
                    >
                        + Add Port
                    </button>
                </div>
            ))}
        </>
    );
}
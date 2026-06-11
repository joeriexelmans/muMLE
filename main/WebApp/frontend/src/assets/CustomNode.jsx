import { Handle, Position, NodeResizer, useUpdateNodeInternals } from "reactflow";
import "./CustomNode.css";
import NodeHandles from "./CustomNodeHandle.jsx";
import {useEffect} from "react";
import CustomNodeHandle from "./CustomNodeHandle.jsx";

const CustomNode = ({ data, selected }) => {
    const updateNodeInternals = useUpdateNodeInternals();
    const { ports, meta } = data;
    const { label, description } = meta;

    const isRunning = data.runtime?.running;

    const rowHeight = 20;
    const categories = [
        {
            key: "flow_in",
            side: "left",
            type: "target",
            color: "var(--node-handle-flow-in)",
            offset: 0
        },
        {
            key: "flow_out",
            side: "right",
            type: "source",
            color: "var(--node-handle-flow-out)",
            offset: 0
        },
        {
            key: "data_in",
            side: "left",
            type: "target",
            color: "var(--node-handle-data-in)",
            offset: 1
        },
        {
            key: "data_out",
            side: "right",
            type: "source",
            color: "var(--node-handle-data-out)",
            offset: 1
        }
    ];

    const heightMin =
        (Math.max(
            ports.flow_in.length,
            ports.flow_out.length
        ) + Math.max(
            ports.data_in.length,
            ports.data_out.length
        ) + !(Math.max(
            ports.data_in.length,
            ports.data_out.length
        ) === 0)
        + 2) * rowHeight;
    const offset_dist =(Math.max(
            ports.flow_in.length,
            ports.flow_out.length,
        ) + 1) * rowHeight

    useEffect(() => {
        console.log("node")
        updateNodeInternals(data.id);
    }, [data]);
    return (
        <>
            <NodeResizer
                isVisible={selected}
                minWidth={80}
                minHeight={heightMin}
            />

            <div
                className="custom-node-wrapper"
                style={{
                    height: Math.max(heightMin, data.height),
                    width: Math.max(data.width, 60)
                }}
            >
                {/* NODE BODY */}
                <div className={`custom-node ${isRunning ? "running" : ""}`}>
                    <div className="label">
                        <strong>{label}</strong>
                    </div>
                    <div className="seperator"/>
                    <div>
                        {description}
                    </div>
                </div>

                <CustomNodeHandle
                    ports={ports}
                    categories={categories}
                    rowHeight={rowHeight}
                    offsetDist={offset_dist}
                    nodeWidth={data.width}
                />
            </div>
        </>
    );
};

export default CustomNode;
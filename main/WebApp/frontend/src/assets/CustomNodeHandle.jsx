import { Handle, Position } from "reactflow";
import {useEffect} from "react";

const NodeHandles = ({
    ports,
    categories,
    rowHeight,
    offsetDist,
    nodeWidth,
}) => {
    return (
        <>
            {categories.map((category) => {
                const portsList = ports[category.key];
                const isLeft = category.side === "left";

                return portsList.map((port, index) => (
                    <div
                        key={`${category.key}-${port.id}`}
                        className="handle-wrapper"
                        style={{
                            top: `${
                                (index + 2) * rowHeight +
                                category.offset * offsetDist
                            }px`,
                            left: isLeft ? 0 : `${nodeWidth}px`
                        }}
                    >
                        <Handle
                            className={`handle ${
                                isLeft
                                    ? "handle-left"
                                    : "handle-right"
                            }`}
                            type={category.type}
                            position={
                                isLeft
                                    ? Position.Left
                                    : Position.Right
                            }
                            id={category.key + port.id}
                            style={{
                                background: category.color
                            }}
                        />

                        <div className="handle-tooltip-wrapper">
                            <div className="handle-tooltip">
                                {port.name}
                            </div>
                        </div>
                    </div>
                ));
            })}
        </>
    );
};

export default NodeHandles;
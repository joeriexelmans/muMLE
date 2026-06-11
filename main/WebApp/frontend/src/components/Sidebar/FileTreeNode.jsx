import React, {useState} from "react";
import { FaProjectDiagram } from "react-icons/fa";

export function FileNode({ node, path, fileTreeHook, Overlay, loadGraph, saveGraph}) {
    if (!node) {
        return <div>Loading...</div>;
    }
    const full_path = path + "/" + node.name
    const isDirectory = node.type === "directory"
    const handleClickDir = () => {
        if (isDirectory) {
            fileTreeHook.toggle(full_path);
        }
    };
    const handleRightClickFlow = (e, node) => {
        e.preventDefault();
        Overlay.show({
            x: e.clientX,
            y: e.clientY,
            data: node,
            render: ({hide, data}) => (
                <div>
                    <div
                        style={{padding: 6, cursor: "pointer"}}
                        onClick={() => {
                            loadGraph(full_path.slice(full_path.indexOf("/", 1) + 1))
                            console.log("Load:", data);
                            hide();
                        }}
                    >
                        Load
                    </div>
                    <div
                        style={{padding: 6, cursor: "pointer"}}
                        onClick={() => {
                            saveGraph(full_path.slice(full_path.indexOf("/", 1) + 1))
                            console.log("Save:", data);
                            hide();
                        }}
                    >
                        Save
                    </div>
                </div>
            )
        });
    }
    const handleRightClickDir = (e, node) => {
        e.preventDefault();
        Overlay.show({
            x: e.clientX,
            y: e.clientY,
            data: node,
            render: ({hide, data}) => (
                <div>
                    <div
                        style={{padding: 6, cursor: "pointer"}}
                        onClick={async () => {
                            const dirname = prompt("Directory name");
                            if (dirname) {
                                const dir = `${full_path}/${dirname}`;
                                await fileTreeHook.createDirectory(
                                    dir.slice(dir.indexOf("/", 1) + 1)
                                );
                                await fileTreeHook.reload_fileTree()
                            }
                            hide();
                        }}
                    >
                        📁 New Directory
                    </div>

                    <div
                        style={{padding: 6, cursor: "pointer"}}
                        onClick={async () => {
                            const filename = prompt("Workflow name");
                            if (filename) {
                                const file = `${full_path}/${filename}.wf`;
                                await saveGraph(
                                    file.slice(file.indexOf("/", 1) + 1)
                                );
                                await fileTreeHook.reload_fileTree();
                            }
                            hide();
                        }}
                    >
                        🔀 Save as
                    </div>
                </div>
            ),
        });
    };

    const textStyle = {
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
    };

    if (isDirectory) {
        const expanded = !fileTreeHook.isExpanded(full_path);
        return (
            <div style={{paddingLeft: 16}}>
                <div
                    style={textStyle}
                    onClick={handleClickDir}
                    onContextMenu={(e) => handleRightClickDir(e, node)}
                >
                    {expanded ? "📂" : "📁"} {node.name}
                </div>

                {expanded && (
                    <div>
                        {node.children?.map((child, idx) => (
                            <FileNode key={idx} node={child} path={full_path} fileTreeHook={fileTreeHook}
                                      Overlay={Overlay} loadGraph={loadGraph} saveGraph={saveGraph}/>
                        ))}
                    </div>
                )}
            </div>
        );
    } else {
        if (node.name.endsWith(".wf")) {
            return <div style={{paddingLeft: 16, ...textStyle}}
                        onContextMenu={(e) => handleRightClickFlow(e, node)}>🔀 {node.name}</div>;
        }
        return <div style={{paddingLeft: 16, ...textStyle}}>📄 {node.name}</div>;
    }
}
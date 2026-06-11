import React, {useState} from "react";
import { FileNode } from "./FileTreeNode.jsx";
import {useGraph} from "../../hooks/Graph.jsx";
import Panel from "./panel.jsx"

function FileTreePanel ({ fileTreeHook, Graph, API, Overlay}) {
    const [graph, setGraph] = Graph
    const {loadGraph, saveGraph} = useGraph(graph, setGraph, API);

    return (
    <Panel title="File lib">
        <FileNode
            node={fileTreeHook.fileTree} path={""}
            fileTreeHook={fileTreeHook}
            loadGraph={loadGraph}
            saveGraph={saveGraph}
            Overlay={Overlay}
        />
    </Panel>)
}

export default FileTreePanel;
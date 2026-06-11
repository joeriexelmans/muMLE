import React from "react";
import { Workflow } from "../../hooks/Workflow.jsx";
import "./WorkflowPanel.css";
import Panel from "./panel.jsx"

export default function WorkflowPanel({ Graph, API }) {
    const [graph, setGraph] = Graph;

    const {
        createProcess,
        createRunObj,
        runtimeStart,
        runtimeStep,
        runtimePause,
        runtimeStop
    } = Workflow(graph, setGraph, API);

    const processId = graph.runConfig?.processId;
    const runtimeId = graph.runConfig?.runtimeId;
    const selectedFile = graph.runConfig?.selectedFile;

    return (
        <Panel title="Workflow Player">
            <div className={"row"}>
                <button
                    className={"button"}
                    onClick={() => createProcess(selectedFile)}
                >
                    📦 Create Process
                </button>

                <button
                    className={"button"}
                    disabled={!processId}
                    onClick={() => createRunObj(processId)}
                >
                    ⚙️ Init Runtime
                </button>
            </div>
            <div className={"player"}>
                <button
                    className={"control"}
                    disabled={!runtimeId}
                    onClick={() => runtimeStart(runtimeId)}
                >
                    ▶
                </button>

                <button
                    className={"control"}
                    disabled={!runtimeId}
                    onClick={() => runtimePause(runtimeId)}
                >
                    ⏸
                </button>

                <button
                    className={"control"}
                    disabled={!runtimeId}
                    onClick={() => runtimeStep(runtimeId)}
                >
                    ⏭
                </button>

                <button
                    className={`${"control"} ${"stop"}`}
                    disabled={!runtimeId}
                    onClick={() => runtimeStop(runtimeId)}
                >
                    ⏹
                </button>
            </div>
        </Panel>
    );
}
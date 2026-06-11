import React, { useState, useRef } from 'react';
import './Sidebar.css';
import DataTypesPanel from "./Sidebar/DataTypesPanel.jsx";
import GraphPanel from "./Sidebar/GraphPanel.jsx";
import {GraphPanel as NodePanel} from "./Sidebar/NodePanel.jsx";
import ThemeToggle from "../hooks/ThemeToggle.jsx";
import FileTreePanel from "./Sidebar/FileTreePanel.jsx";
import WorkflowPanel from "./Sidebar/WorkflowPanel.jsx";
export default function Sidebar({
    API,
    Graph,
    fileTreeHook,
    selectedNode,
    lastClickPosition,
    Overlay,
}) {
  const [width, setWidth] = useState(280);
  const [collapsed, setCollapsed] = useState(false);
  const sidebarRef = useRef(null);
  const resizingRef = useRef(false);

  const onMouseDown = (e) => {
    e.preventDefault();
    resizingRef.current = true;
  };
  const onMouseUp = () => {
    resizingRef.current = false;
  };
  const onMouseMove = (e) => {
    if (resizingRef.current && !collapsed) {
      const newWidth = e.clientX - sidebarRef.current.getBoundingClientRect().left;
      if (newWidth > 100 && newWidth < 600)
        setWidth(newWidth);
    }
  };

  React.useEffect(() => {
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

  return (
      <div
          ref={sidebarRef}
          className={`sidebar ${collapsed ? 'collapsed' : ''}`}
          style={{width: collapsed ? 40 : width}}
      >
        {/* Collapse button */}
        <button
            className="toggle-collapse"
            onClick={() => setCollapsed(!collapsed)}
            style={{transform: collapsed ? 'rotate(180deg)' : 'rotate(0deg)'}}
        > ◀
        </button>
        {!collapsed && (
            <div>
              <FileTreePanel
                  Graph={Graph}
                  API={API}
                  fileTreeHook={fileTreeHook}
                  Overlay={Overlay}
              />
              <GraphPanel
                  Graph={Graph}
                  API={API}
                  lastClickPosition={lastClickPosition}
              />
              {/*<DataTypesPanel*/}
              {/*    Graph={Graph}*/}
              {/*/>*/}
              <NodePanel
                  Graph={Graph}
                  selectedNode={selectedNode}
              />
                <WorkflowPanel
                Graph={Graph}
                API={API}
                />
            </div>
        )}
        {!collapsed &&
            <div
                className="resizer"
                onMouseDown={onMouseDown}
            />
        }
        <ThemeToggle/>
      </div>
  );
}
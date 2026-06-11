import React, {useEffect, useState} from 'react';
import 'reactflow/dist/style.css';

import { NodeTemplate, EdgeTemplate, DataTypeTemplate, GraphTemplate } from './models/Graph.jsx';
import Sidebar from "./components/sidebar.jsx";
import Flow from "./components/Flow.jsx"
import {useFileTree} from "./hooks/FileTree.jsx";
import {OverlayMenu, OverlayRenderer} from "./hooks/OverlayMenu.jsx";
import { useUpdateNodeInternals } from "reactflow";


export default function App() {
  const API = import.meta.env.VITE_BACKEND_URL;
  const Graph = useState(GraphTemplate());
  const [selectedNode, setSelectedNode] = useState(null);
  const [lastClickPosition, setLastClickPosition] = useState({ x: 0, y: 0 });
  const fileTree = useFileTree(API, Graph)
  const { overlay, show, hide } = OverlayMenu();

  useEffect(() => {
      console.log("Graph updated:", Graph);
    }, [Graph]);

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw' }}>
      <Sidebar
          API={API}
          Graph={Graph}
          selectedNode={selectedNode}
          lastClickPosition = {lastClickPosition}
          fileTreeHook={fileTree}
          Overlay={{show, hide}}
      />
      <Flow
        Graph={Graph}
        setSelectedNode={setSelectedNode}
        setLastClickPosition={setLastClickPosition}
      />
        <OverlayRenderer overlay={overlay} hide={hide} />
    </div>
  );
}

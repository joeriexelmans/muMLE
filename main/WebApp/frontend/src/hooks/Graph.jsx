/* eslint-disable no-unused-vars */
import { useCallback } from 'react';
import axios from "axios";
import {EdgeTemplate, NodeTemplate, RunConfigTemplate} from "../models/Graph.jsx";

export const useGraph = (graph, setGraph, API) => {
  const sanitizeGraph = (graph) => {
    return {
      // ...graph,
      nodes: graph.nodes.map(node => {
        const {
          id,
          type,
          position,
          data,
          ...rest
        } = node;
        return {
          id, type, position, ...data
        };
      }),
      edges: graph.edges.map(edge => {
        const {
          selected,
          ...rest
        } = edge;
        return {
          ...rest,
        };
      }),
    }
  }


  const rehydrateGraph = (graph, filename) => {
    return {
      nodes: graph.nodes.map(node => {
        console.log(node)
        return NodeTemplate(node.id, node.type, node.position.x, node.position.y, node.width, node.height, {'ports': node.ports, 'meta': node.meta})
      }),
      edges: graph.edges.map(edge => {
        return EdgeTemplate(edge.id, edge.source, edge.sourceHandle, edge.target, edge.targetHandle)
      }),
      runConfig: RunConfigTemplate(filename),
      version: 0
    };
  }

  // --- Load Graph ---
  const loadGraph = useCallback(async (filename) => {
    try {
      const res = await axios.get(API +'file/' + filename);
      setGraph({
        ...rehydrateGraph(JSON.parse(res.data.content), filename),
      });
    } catch (err) {
      console.error('Error loading graph:', err);
    }
  }, [API]);

  // --- Save Graph ---
  const saveGraph = useCallback(async (filename) => {
    try {
      console.log(sanitizeGraph(graph))
      await axios.put(API + 'file/' + filename, {'content': sanitizeGraph(graph), 'type': 'json'});
      alert('Graph saved!');
      graph.runConfig.selectedFile = filename
      setGraph(graph)
    } catch (err) {
      console.error('Error saving graph:', err);
    }
  }, [graph, API]);

  return { loadGraph, saveGraph };
};
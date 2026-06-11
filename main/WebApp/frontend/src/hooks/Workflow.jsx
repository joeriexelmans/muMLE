/* eslint-disable no-unused-vars */
import { useCallback } from 'react';
import axios from "axios";

export const Workflow = (graph, setGraph, API) => {
  // --- Create WF Process ---
  const createProcess = useCallback(async (filename) => {
    try {
      const res = await axios.post(API + 'process/create', {"path": filename});
      setGraph(prev => ({
        ...prev,
        runConfig: {
          ...prev.runConfig,
          processId: res.data.process_id,
          runtimeId: null
        }
      }));
    } catch (err) {
      console.error('Error creating Process:', err);
    }
  }, [API]);

  // --- Create Runn Obj ---
  const createRunObj = useCallback(async (processId) => {
    try {
      const res = await axios.post(API + 'process/init-runtime',
          {
            "process_id": processId,
            "envirement": ""
          })
      setGraph(prev => ({
        ...prev,
        runConfig: {
          ...prev.runConfig,
          runtimeId: res.data.runtime_id
        }
      }));
    } catch (err) {
      console.error('Error creating RunnObj:', err);
    }
  }, [API]);

  const runtimeStart = useCallback(async (processId) => {
    try {
      const res = await axios.post(API + 'process/start',
          {
            "process_id": processId,
            "step_through": true
          })
      getRuntimeInfo(processId)
    } catch (err) {
      console.error('Error starting runtime:', err);
    }
  }, [API]);
  const runtimeStep = useCallback(async (processId) => {
    try {
      const res = await axios.post(API + 'process/step',
          {
            "process_id": processId,
          })
      await getRuntimeInfo(processId)
    } catch (err) {
      console.error('Error step runtime:', err);
    }
  }, [API]);
  const runtimePause = useCallback(async (processId) => {
    try {
      const res = await axios.post(API + 'process/pause',
          {
            "process_id": processId,
          })
    } catch (err) {
      console.error('Error step runtime:', err);
    }
  }, [API]);

  const runtimeStop = useCallback(async (processId) => {
    try {
      const res = await axios.post(API + 'process/stop',
          {
            "process_id": processId,
          })
    } catch (err) {
      console.error('Error step runtime:', err);
    }
  }, [API]);
  const getRuntimeInfo = useCallback(async (processId) => {
    try {
      const res = await axios.post(
          API + 'process/runtimeinfo',
          {
            process_id: processId,
            output_file: "string"
          }
      );

      const runningStates = res.data?.Running ?? [];

      const runningNodeIds = runningStates
          .map(item => item.state)
          .filter(Boolean)
          .map(state => state.replace(/^[a-zA-Z]+/, ""));

      setGraph(prev => ({
        ...prev,
        nodes: prev.nodes.map(node => ({
          ...node,
          data: {
            ...node.data,
            runtime: {
              ...(node.data.runtime || {}),
              running: runningNodeIds.includes(node.id)
            }
          }
        }))
      }));
    console.log(graph)
    } catch (err) {
      console.error('Error step runtime:', err);
    }
  }, [API, setGraph]);

  return {createProcess, createRunObj, runtimeStart, runtimeStep, runtimePause, runtimeStop}
};
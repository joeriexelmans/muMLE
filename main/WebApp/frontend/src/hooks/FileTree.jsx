import {useCallback, useEffect, useState} from "react";
import axios from "axios";

export const useFileTree = (API, Graph) => {
  const [graph, setGraph] = Graph;
  const [fileTree, setFileTree] = useState(null);

  const reload_fileTree = useCallback(async () => {
    try {
      const res = await axios.get(API + 'files/');
      setFileTree(res.data);
    } catch (err) {
      console.error('Error reloading fileTree:', err);
    }
  }, [API]);

  useEffect(() => {
    reload_fileTree();
  }, [reload_fileTree]);

  const [expandedMap, setExpandedMap] = useState({});

  const toggle = useCallback((path) => {
    setExpandedMap(prev => ({
      ...prev,
      [path]: !prev[path]
    }));
  }, []);

  const isExpanded = useCallback(
      (path) => !!expandedMap[path],
      [expandedMap]
  );

  const createDirectory = useCallback((dir) => {
    try {
      axios.put(API + 'files/' + dir)
    } catch (err) {
      console.error('Error creating directory:', err);
    }
  }, [API]);

  return {fileTree, reload_fileTree, expandedMap, toggle, isExpanded, createDirectory};
}
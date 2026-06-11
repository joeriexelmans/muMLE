export const NodeTemplate = (id, type, x=0, y=0, width=120, height=100, data= {}) => ({
  id: id.toString(),
  type: type,
  data: {
    width: width,
    height: height,
    ports: {
      flow_in: [{id: 1, name: "inputFlow"}],
      flow_out: [{id: 1, name: "outputFlow"}],
      data_in: [],
      data_out: [],
      ...(data?.ports || {})
    },
    meta: {
      label: "activity " + id,
      description: "Your activity details",
      activity: "activity_ref",
      start: false,
      sync: false,
      ...(data?.meta || {})
    },
    version: 0,
    runtime: {
      running: false
    },
  },
  position: {x: x, y: y},
  width: width,
  height: height,
  selected: false,
  dragging: false,
});




export const EdgeTemplate = (id, source, sourceHandle, target, targetHandle) => ({
  id: id,
  selected: false,
  source: source,
  sourceHandle: sourceHandle,
  target: target,
  targetHandle: targetHandle
});

export const DataTypeTemplate = (name = '') => ({
  name
});

export const RunConfigTemplate = (selectedFile) => ({
  selectedFile: selectedFile,
  processId: null,
  runtimeId: null
});

export const GraphTemplate = () => ({
  nodes: [],
  edges: [],
  // datatypes: []

  runConfig: RunConfigTemplate(null),
  version:0
});


import React from "react";
import { useDatatypes } from "../../hooks/Datatypes.jsx";

export default function DataTypesPanel({ graph, setGraph }) {


  const { datatypes } = graph;

  const { add, remove, update, moveUp, moveDown } = useDatatypes(
  (updater) => {
    setGraph(prev => ({
      ...prev,
      datatypes: updater(prev.datatypes)
    }));
  }
);


  return (
    <div className="datatypes">
      <h4>Datatypes</h4>
      {datatypes.map((dt, i) => (
        <div className="datatype-row" key={i}>
          <input
            type="text"
            value={dt.name}
            onChange={(e) => update(i, e.target.value)}
          />

          <div className="edit-menu">
            <button className="btn edit-icon">✎</button>
            <div className="menu">
              <button className="menu-item" onClick={() => moveUp(i)}>↑</button>
              <button className="menu-item" onClick={() => moveDown(i)}>↓</button>
              <button className="menu-item danger" onClick={() => remove(i)}>✖</button>
            </div>
          </div>
        </div>
      ))}
      <button onClick={add} className="btn add">➕</button>
    </div>
  );
}

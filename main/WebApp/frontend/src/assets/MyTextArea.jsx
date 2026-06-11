import React from "react";
import "./MyTextArea.css"

const MyTextArea = ({ value, onChange }) => {
    const startResize = (e) => {
        e.preventDefault();
        const textarea = e.target.previousSibling;
        const startY = e.clientY;
        const startHeight = textarea.offsetHeight;

        const onMouseMove = (e) => {
            const newHeight = startHeight + (e.clientY - startY);
            textarea.style.height = newHeight + "px";
        };

        const onMouseUp = () => {
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseup", onMouseUp);
        };

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    };
    return (
        <div className="textarea-wrapper">
          <textarea
              className="textarea"
              value={value}
              onChange={e => onChange(e)}
              rows={1}
          />
            <div
                className="textarea-resizer"
                onMouseDown={startResize}
            />
        </div>
    );
}

export default MyTextArea;
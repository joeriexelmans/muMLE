import React from "react";
import "./MyCheckbox.css";

const MyCheckbox = ({ value, onChange }) => {
    return (
        <div className="checkbox-wrapper">
            <input
                type="checkbox"
                className="checkbox"
                checked={value}
                onChange={(e) => onChange(e)}
            />
            <span className="checkbox-label">
                {value}
            </span>
        </div>
    );
};

export default MyCheckbox;
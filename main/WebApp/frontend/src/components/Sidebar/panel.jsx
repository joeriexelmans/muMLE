import "./Panel.css";

export default function Panel({ title, children }) {
    return (
        <div className="panel">
            <div className="title">{title}</div>
            {children}
        </div>
    );
}
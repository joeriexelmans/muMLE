import { useCallback, useState } from "react";


export function OverlayMenu() {
    const [overlay, setOverlay] = useState(null);

    const show = useCallback((payload) => {
        setOverlay(payload);
    }, []);

    const hide = useCallback(() => {
        setOverlay(null);
    }, []);

    return {overlay, show, hide};
}

export function OverlayRenderer({ overlay, hide }) {
  if (!overlay) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: overlay.y,
        left: overlay.x,
        background: "var(--control-bg)",
        color: "var(--text-primary)",
        border: "1px solid #ccc",
        borderRadius: 6,
        padding: 6,
        zIndex: 9999,
        minWidth: 120
      }}
      onMouseLeave={hide}
    >
      {typeof overlay.render === "function"
        ? overlay.render({ hide, data: overlay.data })
        : null}
    </div>
  );
}
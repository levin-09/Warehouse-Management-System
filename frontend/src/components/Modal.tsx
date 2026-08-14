import type { ReactNode } from "react";

export function Modal({ title, onClose, children, footer }: {
  title: string; onClose: () => void; children: ReactNode; footer?: ReactNode;
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3 className="modal-title">{title}</h3>
        {children}
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}

export function EmptyState({ icon, text }: { icon?: string; text: string }) {
  return (
    <div className="empty">
      <div style={{ fontSize: 32 }}>{icon ?? "📭"}</div>
      <p>{text}</p>
    </div>
  );
}

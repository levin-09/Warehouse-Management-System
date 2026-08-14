import { useEffect, useState } from "react";
import { getReturns, processReturn, getOrders } from "../api/endpoints";
import type { Return as R, Order } from "../api/types";
import { Table, Spinner } from "../components/ui";
import { Modal } from "../components/Modal";
import { useToast } from "../lib/toast";
import { statusChip, formatDate } from "../lib/status";

export default function Returns() {
  const [returns, setReturns] = useState<R[]>([]);
  const [loading, setLoading] = useState(true);
  const [showProcess, setShowProcess] = useState(false);
  const toast = useToast();
  const load = async () => {
    setLoading(true);
    try { setReturns(await getReturns()); }
    catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Returns</h1><p className="page-sub">Customer return processing</p></div>
        <button className="btn btn-primary" onClick={() => setShowProcess(true)}>+ Process Return</button>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <Table headers={["Ref", "Order", "Status", "Reason", "Items", "Completed"]}>
            {returns.map((r) => (
              <tr key={r.id}>
                <td style={{ fontWeight: 600 }}>{r.return_ref}</td>
                <td>{r.original_order_ref}</td>
                <td><span className={`chip ${statusChip(r.status)}`}>{r.status}</span></td>
                <td>{r.return_reason || "—"}</td>
                <td>{r.items.length}</td>
                <td>{formatDate(r.completed_at)}</td>
              </tr>
            ))}
          </Table>
        )}
      </div>
      {showProcess && <ProcessReturn onClose={() => setShowProcess(false)} onSaved={async (d) => {
        try { await processReturn(d); toast("Return processed", "success"); setShowProcess(false); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
    </div>
  );
}

function ProcessReturn({ onClose, onSaved }: { onClose: () => void; onSaved: (d: any) => void }) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [processedBy, setProcessedBy] = useState("");
  const [f, setF] = useState<any>({ original_order_id: "", return_reason: "", items: [{ product_id: "", quantity: 1, condition: "resellable", damage_grade: "", action_taken: "" }] });
  useEffect(() => { getOrders().then(setOrders); }, []);
  const set = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  const setItem = (i: number, k: string, v: any) => setF((s: any) => ({ ...s, items: s.items.map((x: any, idx: number) => idx === i ? { ...x, [k]: v } : x) }));
  const submit = () => onSaved({
    ...f,
    processed_by: processedBy,
    items: f.items.map((it: any) => ({ ...it, damage_grade: it.damage_grade || undefined, action_taken: it.action_taken || undefined })),
  });
  return (
    <Modal title="Process Return" onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={submit}>Process</button>
    </>}>
      <div className="form-group"><label>Original order *</label>
        <select className="select" value={f.original_order_id} onChange={(e) => set("original_order_id", e.target.value)}>
          <option value="">Select order</option>{orders.map((o) => <option key={o.id} value={o.id}>{o.order_ref}</option>)}
        </select></div>
      <div className="form-group"><label>Reason</label><input className="input" value={f.return_reason} onChange={(e) => set("return_reason", e.target.value)} /></div>
      <div className="form-group"><label>Processed by (user id, optional)</label><input className="input" value={processedBy} onChange={(e) => setProcessedBy(e.target.value)} /></div>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>Items</div>
      {f.items.map((it: any, i: number) => (
        <div key={i} className="card" style={{ padding: 12, marginBottom: 10 }}>
          <div className="flex gap" style={{ marginBottom: 8 }}>
            <input className="input" placeholder="Product id *" value={it.product_id} onChange={(e) => setItem(i, "product_id", e.target.value)} />
            <input className="input" style={{ width: 70 }} type="number" value={it.quantity} onChange={(e) => setItem(i, "quantity", parseInt(e.target.value) || 1)} />
          </div>
          <div className="grid grid-3 gap">
            <div className="form-group"><label>Condition</label>
              <select className="select" value={it.condition} onChange={(e) => setItem(i, "condition", e.target.value)}>
                <option value="resellable">resellable</option><option value="damaged">damaged</option><option value="unsellable">unsellable</option>
              </select></div>
            <div className="form-group"><label>Damage grade</label>
              <select className="select" value={it.damage_grade} onChange={(e) => setItem(i, "damage_grade", e.target.value)}>
                <option value="">None</option><option>A</option><option>B</option><option>C</option><option>D</option>
              </select></div>
            <div className="form-group"><label>Action</label>
              <select className="select" value={it.action_taken} onChange={(e) => setItem(i, "action_taken", e.target.value)}>
                <option value="">Auto</option>
                <option value="restocked_to_good">restock to good</option>
                <option value="placed_in_damaged">place in damaged</option>
                <option value="returned_to_seller">return to seller</option>
                <option value="disposed">dispose</option>
              </select></div>
          </div>
        </div>
      ))}
      <button className="btn btn-secondary btn-sm" onClick={() => setF((s: any) => ({ ...s, items: [...s.items, { product_id: "", quantity: 1, condition: "resellable", damage_grade: "", action_taken: "" }] }))}>+ Add item</button>
    </Modal>
  );
}

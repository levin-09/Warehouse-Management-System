import { useEffect, useState } from "react";
import { getShipments, getSellers, getWarehouses, getProducts, createShipmentDraft, confirmShipment } from "../api/endpoints";
import type { Shipment, Seller, Warehouse, Product } from "../api/types";
import { Table, Spinner } from "../components/ui";
import { Modal } from "../components/Modal";
import { useToast } from "../lib/toast";
import { statusChip, formatDate } from "../lib/status";

export default function Shipments() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDraft, setShowDraft] = useState(false);
  const [confirming, setConfirming] = useState<Shipment | null>(null);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [s, w] = await Promise.all([getShipments(), getWarehouses()]);
      setShipments(s); setWarehouses(w);
    } catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const whName = (id: string) => warehouses.find((w) => w.id === id)?.name ?? id.slice(0, 6);

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Shipments</h1><p className="page-sub">Inbound receiving</p></div>
        <button className="btn btn-primary" onClick={() => setShowDraft(true)}>+ Create Draft</button>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <Table headers={["Ref", "Status", "Warehouse", "Carrier", "Items", "Received", ""]}>
            {shipments.map((s) => (
              <tr key={s.id}>
                <td style={{ fontWeight: 600 }}>{s.shipment_ref}</td>
                <td><span className={`chip ${statusChip(s.status)}`}>{s.status}</span></td>
                <td>{whName(s.warehouse_id)}</td>
                <td>{s.carrier || "—"}</td>
                <td>{s.items.length}</td>
                <td>{formatDate(s.received_at)}</td>
                <td>{s.status === "draft" && <button className="btn btn-sm btn-primary" onClick={() => setConfirming(s)}>Receive</button>}</td>
              </tr>
            ))}
          </Table>
        )}
      </div>
      {showDraft && <DraftDialog warehouses={warehouses} onClose={() => setShowDraft(false)} onSaved={async (d) => {
        try { await createShipmentDraft(d); toast("Draft created", "success"); setShowDraft(false); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
      {confirming && <ConfirmDialog shipment={confirming} onClose={() => setConfirming(null)} onSaved={async (d) => {
        try { await confirmShipment(d); toast("Shipment received", "success"); setConfirming(null); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
    </div>
  );
}

function DraftDialog({ warehouses, onClose, onSaved }: { warehouses: Warehouse[]; onClose: () => void; onSaved: (d: any) => void }) {
  const [sellers, setSellers] = useState<Seller[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [f, setF] = useState<any>({ shipment_ref: "", seller_id: "", warehouse_id: "", carrier: "", notes: "", items: [{ product_id: "", quantity_expected: 0 }] });
  useEffect(() => { getSellers().then(setSellers); getProducts().then(setProducts); }, []);
  const set = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  const setItem = (i: number, k: string, v: any) => setF((s: any) => {
    const items = s.items.map((x: any, idx: number) => idx === i ? { ...x, [k]: v } : x);
    return { ...s, items };
  });
  return (
    <Modal title="Create Shipment Draft" onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={() => onSaved(f)}>Create Draft</button>
    </>}>
      <div className="form-group"><label>Shipment ref *</label><input className="input" value={f.shipment_ref} onChange={(e) => set("shipment_ref", e.target.value)} /></div>
      <div className="form-group"><label>Seller</label>
        <select className="select" value={f.seller_id} onChange={(e) => set("seller_id", e.target.value)}>
          <option value="">Select</option>{sellers.map((s) => <option key={s.id} value={s.id}>{s.company_name}</option>)}
        </select></div>
      <div className="form-group"><label>Warehouse</label>
        <select className="select" value={f.warehouse_id} onChange={(e) => set("warehouse_id", e.target.value)}>
          <option value="">Select</option>{warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select></div>
      <div className="form-group"><label>Carrier</label><input className="input" value={f.carrier} onChange={(e) => set("carrier", e.target.value)} /></div>
      <div className="form-group"><label>Notes</label><textarea className="textarea" value={f.notes} onChange={(e) => set("notes", e.target.value)} /></div>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>Line items</div>
      {f.items.map((it: any, i: number) => (
        <div className="flex gap" key={i} style={{ marginBottom: 8 }}>
          <select className="select" value={it.product_id} onChange={(e) => setItem(i, "product_id", e.target.value)}>
            <option value="">Product</option>{products.map((p) => <option key={p.id} value={p.id}>{p.product_name}</option>)}
          </select>
          <input className="input" style={{ width: 90 }} type="number" placeholder="Qty" value={it.quantity_expected} onChange={(e) => setItem(i, "quantity_expected", parseInt(e.target.value) || 0)} />
        </div>
      ))}
      <button className="btn btn-secondary btn-sm" onClick={() => setF((s: any) => ({ ...s, items: [...s.items, { product_id: "", quantity_expected: 0 }] }))}>+ Add item</button>
    </Modal>
  );
}

function ConfirmDialog({ shipment, onClose, onSaved }: { shipment: Shipment; onClose: () => void; onSaved: (d: any) => void }) {
  const [items, setItems] = useState(shipment.items.map((it) => ({ product_id: it.product_id, quantity_received: it.quantity_expected, quantity_damaged: 0, damage_grade: "", damage_notes: "" })));
  const [notes, setNotes] = useState(shipment.notes || "");
  const setItem = (i: number, k: string, v: any) => setItems((arr) => arr.map((x, idx) => idx === i ? { ...x, [k]: v } : x));
  return (
    <Modal title={`Receive ${shipment.shipment_ref}`} onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={() => onSaved({
        shipment_ref: shipment.shipment_ref,
        received_by: shipment.warehouse_id,
        items: items.map((it) => ({ ...it, damage_grade: it.damage_grade || undefined })),
        notes,
      })}>Confirm Receipt</button>
    </>}>
      {items.map((it, i) => (
        <div key={i} className="card" style={{ padding: 14, marginBottom: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>{it.product_id}</div>
          <div className="grid grid-2 gap">
            <div className="form-group"><label>Received</label><input className="input" type="number" value={it.quantity_received} onChange={(e) => setItem(i, "quantity_received", parseInt(e.target.value) || 0)} /></div>
            <div className="form-group"><label>Damaged</label><input className="input" type="number" value={it.quantity_damaged} onChange={(e) => setItem(i, "quantity_damaged", parseInt(e.target.value) || 0)} /></div>
          </div>
          <div className="form-group"><label>Damage grade</label>
            <select className="select" value={it.damage_grade} onChange={(e) => setItem(i, "damage_grade", e.target.value)}>
              <option value="">None</option><option>A</option><option>B</option><option>C</option><option>D</option>
            </select></div>
          <div className="form-group"><label>Damage notes</label><input className="input" value={it.damage_notes} onChange={(e) => setItem(i, "damage_notes", e.target.value)} /></div>
        </div>
      ))}
      <div className="form-group"><label>Receipt notes</label><textarea className="textarea" value={notes} onChange={(e) => setNotes(e.target.value)} /></div>
    </Modal>
  );
}

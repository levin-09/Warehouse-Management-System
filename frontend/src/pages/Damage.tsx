import { useEffect, useState } from "react";
import { getDamageRecords, createDamageRecord, getProducts, getWarehouses } from "../api/endpoints";
import type { DamageRecord, Product, Warehouse } from "../api/types";
import { Table, Spinner } from "../components/ui";
import { Modal } from "../components/Modal";
import { useToast } from "../lib/toast";

export default function Damage() {
  const [records, setRecords] = useState<DamageRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const toast = useToast();
  const load = async () => {
    setLoading(true);
    try { setRecords(await getDamageRecords()); }
    catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Damage Records</h1><p className="page-sub">Damage assessments</p></div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ Log Damage</button>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <Table headers={["Grade", "Product", "Qty", "Carrier", "Notes", "Notified"]}>
            {records.map((r) => (
              <tr key={r.id}>
                <td><span className="chip chip-danger">{r.damage_grade}</span></td>
                <td style={{ fontWeight: 600 }}>{r.product_name}</td>
                <td>{r.quantity_damaged}</td>
                <td>{r.carrier || "—"}</td>
                <td>{r.damage_notes || "—"}</td>
                <td>{r.seller_notified ? <span className="chip chip-success">Yes</span> : <span className="chip chip-neutral">No</span>}</td>
              </tr>
            ))}
          </Table>
        )}
      </div>
      {showAdd && <AddDamage onClose={() => setShowAdd(false)} onSaved={async (d) => {
        try { await createDamageRecord(d); toast("Damage logged", "success"); setShowAdd(false); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
    </div>
  );
}

function AddDamage({ onClose, onSaved }: { onClose: () => void; onSaved: (d: any) => void }) {
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [f, setF] = useState<any>({ shipment_id: "", shipment_ref: "", product_id: "", warehouse_id: "", quantity_damaged: 1, damage_grade: "B", damage_notes: "", carrier: "", carrier_tracking: "", action_taken: "" });
  useEffect(() => { getProducts().then(setProducts); getWarehouses().then(setWarehouses); }, []);
  const set = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  const submit = () => onSaved({ ...f, shipment_id: f.shipment_id || undefined });
  return (
    <Modal title="Log Damage" onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={submit}>Save</button>
    </>}>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Product *</label>
          <select className="select" value={f.product_id} onChange={(e) => set("product_id", e.target.value)}>
            <option value="">Select</option>{products.map((p) => <option key={p.id} value={p.id}>{p.product_name}</option>)}
          </select></div>
        <div className="form-group"><label>Warehouse *</label>
          <select className="select" value={f.warehouse_id} onChange={(e) => set("warehouse_id", e.target.value)}>
            <option value="">Select</option>{warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
          </select></div>
      </div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Quantity damaged *</label><input className="input" type="number" value={f.quantity_damaged} onChange={(e) => set("quantity_damaged", parseInt(e.target.value) || 0)} /></div>
        <div className="form-group"><label>Grade *</label>
          <select className="select" value={f.damage_grade} onChange={(e) => set("damage_grade", e.target.value)}>
            <option>A</option><option>B</option><option>C</option><option>D</option>
          </select></div>
      </div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Shipment id</label><input className="input" value={f.shipment_id} onChange={(e) => set("shipment_id", e.target.value)} /></div>
        <div className="form-group"><label>Shipment ref</label><input className="input" value={f.shipment_ref} onChange={(e) => set("shipment_ref", e.target.value)} /></div>
      </div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Carrier</label><input className="input" value={f.carrier} onChange={(e) => set("carrier", e.target.value)} /></div>
        <div className="form-group"><label>Carrier tracking</label><input className="input" value={f.carrier_tracking} onChange={(e) => set("carrier_tracking", e.target.value)} /></div>
      </div>
      <div className="form-group"><label>Action taken</label>
        <select className="select" value={f.action_taken} onChange={(e) => set("action_taken", e.target.value)}>
          <option value="">Auto</option>
          <option value="moved_to_good">move to good</option>
          <option value="placed_in_discount_zone">discount zone</option>
          <option value="held_for_seller">hold for seller</option>
          <option value="carrier_claim">carrier claim</option>
        </select></div>
      <div className="form-group"><label>Notes</label><textarea className="textarea" value={f.damage_notes} onChange={(e) => set("damage_notes", e.target.value)} /></div>
    </Modal>
  );
}

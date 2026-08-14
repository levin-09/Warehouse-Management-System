import { useEffect, useState } from "react";
import { getBinLocations, getWarehouses, createBinLocation } from "../api/endpoints";
import type { BinLocation, Warehouse } from "../api/types";
import { Table, Spinner } from "../components/ui";
import { Modal } from "../components/Modal";
import { useToast } from "../lib/toast";

export default function Bins() {
  const [bins, setBins] = useState<BinLocation[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const toast = useToast();
  const load = async () => {
    setLoading(true);
    try { const [b, w] = await Promise.all([getBinLocations(), getWarehouses()]); setBins(b); setWarehouses(w); }
    catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const whName = (id: string) => warehouses.find((w) => w.id === id)?.name ?? id.slice(0, 6);

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Bin Locations</h1><p className="page-sub">Physical storage mapping</p></div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ Add Bin</button>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <Table headers={["Bin code", "Warehouse", "Position", "Capacity", "Units", "Status"]}>
            {bins.map((b) => (
              <tr key={b.id}>
                <td style={{ fontWeight: 600 }}>{b.bin_code}</td>
                <td>{whName(b.warehouse_id)}</td>
                <td>{b.aisle}-{b.row}-{b.shelf}-{b.bin}</td>
                <td>{b.max_capacity}</td>
                <td>{b.current_units}</td>
                <td>{b.is_occupied ? <span className="chip chip-warning">Occupied</span> : <span className="chip chip-success">Empty</span>}</td>
              </tr>
            ))}
          </Table>
        )}
      </div>
      {showAdd && <AddBin warehouses={warehouses} onClose={() => setShowAdd(false)} onSaved={async (d) => {
        try { await createBinLocation(d); toast("Bin added", "success"); setShowAdd(false); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
    </div>
  );
}

function AddBin({ warehouses, onClose, onSaved }: { warehouses: Warehouse[]; onClose: () => void; onSaved: (d: any) => void }) {
  const [f, setF] = useState<any>({ warehouse_id: "", bin_code: "", aisle: "", row: "", shelf: "", bin: "", product_id: "", max_capacity: 100, current_units: 0, is_occupied: false });
  const set = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  return (
    <Modal title="Add Bin Location" onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={() => onSaved(f)}>Create</button>
    </>}>
      <div className="form-group"><label>Warehouse</label>
        <select className="select" value={f.warehouse_id} onChange={(e) => set("warehouse_id", e.target.value)}>
          <option value="">Select</option>{warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select></div>
      <div className="form-group"><label>Bin code (e.g. A-03-2-B)</label><input className="input" value={f.bin_code} onChange={(e) => set("bin_code", e.target.value)} /></div>
      <div className="grid grid-4 gap">
        {["aisle", "row", "shelf", "bin"].map((k) => (
          <div className="form-group" key={k}><label>{k}</label><input className="input" value={f[k]} onChange={(e) => set(k, e.target.value)} /></div>
        ))}
      </div>
      <div className="form-group"><label>Product id (optional)</label><input className="input" value={f.product_id} onChange={(e) => set("product_id", e.target.value)} /></div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Max capacity</label><input className="input" type="number" value={f.max_capacity} onChange={(e) => set("max_capacity", parseInt(e.target.value) || 0)} /></div>
        <div className="form-group"><label>Current units</label><input className="input" type="number" value={f.current_units} onChange={(e) => set("current_units", parseInt(e.target.value) || 0)} /></div>
      </div>
      <div className="form-group"><label>Occupied</label>
        <select className="select" value={String(f.is_occupied)} onChange={(e) => set("is_occupied", e.target.value === "true")}>
          <option value="false">Empty</option><option value="true">Occupied</option>
        </select></div>
    </Modal>
  );
}

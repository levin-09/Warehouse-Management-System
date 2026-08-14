import { useEffect, useState } from "react";
import { getWarehouses, createWarehouse, updateWarehouse, getInventory } from "../api/endpoints";
import type { Warehouse } from "../api/types";
import { Spinner } from "../components/ui";
import { Modal } from "../components/Modal";
import { useToast } from "../lib/toast";
import { Building2, MapPin, Clock, Truck, Plus, Pencil } from "lucide-react";

export default function Warehouses() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<Warehouse | null>(null);
  const [activeId, setActiveId] = useState<string>("");
  const [unitsByWarehouse, setUnitsByWarehouse] = useState<Record<string, number>>({});
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [w, inv] = await Promise.all([getWarehouses(), getInventory()]);
      setWarehouses(w);
      if (!activeId && w.length) setActiveId(w[0].id);
      const units: Record<string, number> = {};
      inv.forEach((i) => { units[i.warehouse_id] = (units[i.warehouse_id] ?? 0) + (i.quantity_available ?? 0); });
      setUnitsByWarehouse(units);
    }
    catch (e: any) { toast(e.response?.data?.detail || "Failed to load warehouses", "error"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const active = warehouses.find((w) => w.id === activeId) ?? warehouses[0];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Warehouses <span style={{ color: "var(--muted)", fontWeight: 500 }}>({warehouses.length})</span></h1>
          <p className="page-sub">Manage your warehouse locations, hours and carriers</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}><Plus size={16} /> Add Warehouse</button>
      </div>

      {loading ? <Spinner /> : (
        <div className="grid grid-3">
          {/* Left: list of warehouses */}
          <div className="card card-pad" style={{ gridColumn: "span 1" }}>
            <h3 style={{ margin: "0 0 14px", fontFamily: "Poppins", fontSize: 15, fontWeight: 600 }}>All Warehouses</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {warehouses.map((w) => (
                <button
                  key={w.id}
                  onClick={() => setActiveId(w.id)}
                  style={{
                    textAlign: "left", cursor: "pointer", width: "100%",
                    padding: "14px 16px", borderRadius: 14,
                    border: activeId === w.id ? "2px solid var(--accent)" : "1px solid var(--border)",
                    background: activeId === w.id ? "#FFFBEF" : "#fff",
                    display: "flex", alignItems: "center", gap: 12,
                  }}
                >
                  <span style={{ width: 40, height: 40, borderRadius: 12, background: "#1C3D4F", color: "#fff", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>
                    <Building2 size={20} />
                  </span>
                  <span style={{ flex: 1 }}>
                    <span style={{ display: "block", fontWeight: 600, fontFamily: "Poppins" }}>{w.name}</span>
                    <span style={{ display: "block", color: "var(--muted)", fontSize: 12 }}>{w.city}, {w.state}</span>
                  </span>
                  <span className={`chip ${w.is_active ? "chip-success" : "chip-neutral"}`} style={{ fontSize: 11 }}>
                    {w.is_active ? "Active" : "Inactive"}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Right: active warehouse detail */}
          {active && (
            <div className="card card-pad" style={{ gridColumn: "span 2" }}>
              <div className="flex between align-center" style={{ marginBottom: 20 }}>
                <div>
                  <h3 style={{ margin: 0, fontFamily: "Poppins", fontSize: 20, fontWeight: 600 }}>{active.name}</h3>
                  <p style={{ margin: "2px 0 0", color: "var(--muted)" }}>
                    <MapPin size={14} style={{ verticalAlign: "-2px" }} /> {active.address}, {active.city}, {active.state}
                  </p>
                </div>
                <button className="btn btn-sm btn-secondary" onClick={() => setEditing(active)}><Pencil size={14} /> Edit</button>
              </div>

              {/* Key stats */}
              <div className="grid grid-3 mb">
                <div style={{ background: "#F7F8F4", borderRadius: 14, padding: "14px 16px" }}>
                  <div style={{ color: "var(--muted)", fontSize: 12 }}>Units in stock</div>
                  <div style={{ fontSize: 22, fontWeight: 700 }}>{unitsByWarehouse[active.id] ?? 0}</div>
                </div>
                <div style={{ background: "#F7F8F4", borderRadius: 14, padding: "14px 16px" }}>
                  <div style={{ color: "var(--muted)", fontSize: 12 }}>Carriers</div>
                  <div style={{ fontSize: 22, fontWeight: 700 }}>{active.carrier_schedules.length}</div>
                </div>
                <div style={{ background: "#F7F8F4", borderRadius: 14, padding: "14px 16px" }}>
                  <div style={{ color: "var(--muted)", fontSize: 12 }}>Status</div>
                  <div style={{ fontSize: 22, fontWeight: 700 }}>{active.is_active ? "Active" : "Inactive"}</div>
                </div>
              </div>

              {/* Details */}
              <div className="grid grid-2">
                <div style={{ border: "1px solid var(--border)", borderRadius: 14, padding: 16 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, fontWeight: 600, fontFamily: "Poppins" }}>
                    <Clock size={16} color="var(--accent)" /> Operating Hours
                  </div>
                  {active.operating_hours ? (
                    <div style={{ fontSize: 14 }}>{active.operating_hours.open} – {active.operating_hours.close}</div>
                  ) : (
                    <div style={{ color: "var(--muted)", fontSize: 13 }}>Not set</div>
                  )}
                </div>
                <div style={{ border: "1px solid var(--border)", borderRadius: 14, padding: 16 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, fontWeight: 600, fontFamily: "Poppins" }}>
                    <Truck size={16} color="var(--accent)" /> Carrier Schedules
                  </div>
                  {active.carrier_schedules.length ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {active.carrier_schedules.map((c, i) => (
                        <div key={i} style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--border)", paddingBottom: 6 }}>
                          <span style={{ fontWeight: 600 }}>{c.carrier}</span>
                          <span style={{ color: "var(--muted)", fontSize: 13 }}>{c.pickup_time} · {c.days.join(", ")}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ color: "var(--muted)", fontSize: 13 }}>No carriers scheduled</div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {showAdd && <WarehouseForm title="Add Warehouse" initial={{} as Warehouse} onClose={() => setShowAdd(false)} onSave={async (d) => {
        try { await createWarehouse(d); toast("Warehouse created", "success"); setShowAdd(false); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
      {editing && <WarehouseForm title="Edit Warehouse" initial={editing} onClose={() => setEditing(null)} onSave={async (d) => {
        try { await updateWarehouse(editing.id, d); toast("Warehouse updated", "success"); setEditing(null); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
    </div>
  );
}

function WarehouseForm({ title, initial, onClose, onSave }: { title: string; initial: Warehouse; onClose: () => void; onSave: (d: any) => void }) {
  const [f, setF] = useState<any>({
    name: initial.name ?? "",
    city: initial.city ?? "",
    state: initial.state ?? "",
    address: initial.address ?? "",
    is_active: initial.is_active ?? true,
    carrier_schedules: initial.carrier_schedules?.map((c) => ({ ...c })) ?? [],
    operating_hours: initial.operating_hours ? { ...initial.operating_hours } : { open: "07:00", close: "19:00" },
  });
  const set = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  const setSchedule = (i: number, k: string, v: any) => setF((s: any) => ({
    ...s, carrier_schedules: s.carrier_schedules.map((c: any, idx: number) => idx === i ? { ...c, [k]: v } : c),
  }));
  const setHours = (k: string, v: any) => setF((s: any) => ({ ...s, operating_hours: { ...s.operating_hours, [k]: v } }));

  const submit = () => onSave({
    ...f,
    carrier_schedules: f.carrier_schedules.filter((c: any) => c.carrier),
    operating_hours: f.operating_hours.open || f.operating_hours.close ? f.operating_hours : null,
  });

  return (
    <Modal title={title} onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={submit}>Save</button>
    </>}>
      <div className="form-group"><label>Name *</label><input className="input" value={f.name} onChange={(e) => set("name", e.target.value)} /></div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>City *</label><input className="input" value={f.city} onChange={(e) => set("city", e.target.value)} /></div>
        <div className="form-group"><label>State *</label><input className="input" value={f.state} onChange={(e) => set("state", e.target.value)} /></div>
      </div>
      <div className="form-group"><label>Address *</label><input className="input" value={f.address} onChange={(e) => set("address", e.target.value)} /></div>
      <div style={{ fontWeight: 600, margin: "8px 0" }}>Operating hours</div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Open</label><input className="input" type="time" value={f.operating_hours.open} onChange={(e) => setHours("open", e.target.value)} /></div>
        <div className="form-group"><label>Close</label><input className="input" type="time" value={f.operating_hours.close} onChange={(e) => setHours("close", e.target.value)} /></div>
      </div>
      <div style={{ fontWeight: 600, margin: "8px 0" }}>Carrier schedules</div>
      {f.carrier_schedules.map((c: any, i: number) => (
        <div key={i} className="card" style={{ padding: 12, marginBottom: 10 }}>
          <div className="grid grid-2 gap">
            <div className="form-group"><label>Carrier</label><input className="input" value={c.carrier} onChange={(e) => setSchedule(i, "carrier", e.target.value)} /></div>
            <div className="form-group"><label>Pickup time</label><input className="input" type="time" value={c.pickup_time} onChange={(e) => setSchedule(i, "pickup_time", e.target.value)} /></div>
          </div>
          <div className="form-group"><label>Days (comma separated)</label>
            <input className="input" value={c.days.join(", ")} onChange={(e) => setSchedule(i, "days", e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean))} />
          </div>
          <button className="btn btn-sm btn-danger" onClick={() => setF((s: any) => ({ ...s, carrier_schedules: s.carrier_schedules.filter((_: any, idx: number) => idx !== i) }))}>Remove</button>
        </div>
      ))}
      <button className="btn btn-secondary btn-sm" onClick={() => setF((s: any) => ({ ...s, carrier_schedules: [...s.carrier_schedules, { carrier: "", pickup_time: "", days: [] }] }))}>+ Add carrier</button>
      <div className="form-group mt"><label>Active</label>
        <select className="select" value={String(f.is_active)} onChange={(e) => set("is_active", e.target.value === "true")}>
          <option value="true">Active</option><option value="false">Inactive</option>
        </select></div>
    </Modal>
  );
}

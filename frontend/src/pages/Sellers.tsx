import { useEffect, useState } from "react";
import { getSellers, createSeller, updateSeller } from "../api/endpoints";
import type { Seller } from "../api/types";
import { Table, Spinner } from "../components/ui";
import { Modal } from "../components/Modal";
import { useToast } from "../lib/toast";
import { formatCurrency } from "../lib/status";

export default function Sellers() {
  const [sellers, setSellers] = useState<Seller[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<Seller | null>(null);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try { setSellers(await getSellers()); }
    catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Sellers</h1><p className="page-sub">Dan's seller clients and their billing rates</p></div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ Add Seller</button>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <Table headers={["Company", "Contact", "Email", "Phone", "Storage/day", "Fulfill/order", "Receiving/unit", "Low stock", "Active", ""]}>
            {sellers.map((s) => (
              <tr key={s.id}>
                <td style={{ fontWeight: 600 }}>{s.company_name ?? "—"}</td>
                <td>{s.contact_name ?? "—"}</td>
                <td>{s.email ?? "—"}</td>
                <td>{s.phone ?? "—"}</td>
                <td>{formatCurrency(s.billing_rates?.storage_per_unit_per_day)}</td>
                <td>{formatCurrency(s.billing_rates?.fulfillment_per_order)}</td>
                <td>{formatCurrency(s.billing_rates?.receiving_per_unit)}</td>
                <td>{s.low_stock_threshold_default ?? 0}</td>
                <td>{s.is_active ? <span className="chip chip-success">Active</span> : <span className="chip chip-neutral">Inactive</span>}</td>
                <td><button className="btn btn-sm btn-secondary" onClick={() => setEditing(s)}>Edit</button></td>
              </tr>
            ))}
          </Table>
        )}
      </div>
      {showAdd && <SellerForm title="Add Seller" initial={{}} onClose={() => setShowAdd(false)} onSave={async (d) => {
        try { await createSeller(d); toast("Seller created", "success"); setShowAdd(false); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
      {editing && <SellerForm title="Edit Seller" initial={editing} onClose={() => setEditing(null)} onSave={async (d) => {
        try { await updateSeller(editing.id, d); toast("Seller updated", "success"); setEditing(null); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
    </div>
  );
}

function SellerForm({ title, initial, onClose, onSave }: {
  title: string;
  initial: Partial<Seller> & { portal_password?: string };
  onClose: () => void;
  onSave: (d: any) => void;
}) {
  const [f, setF] = useState<any>({
    company_name: initial.company_name ?? "",
    contact_name: initial.contact_name ?? "",
    email: initial.email ?? "",
    phone: initial.phone ?? "",
    billing_rates: {
      storage_per_unit_per_day: initial.billing_rates?.storage_per_unit_per_day ?? 0.05,
      fulfillment_per_order: initial.billing_rates?.fulfillment_per_order ?? 3.50,
      receiving_per_unit: initial.billing_rates?.receiving_per_unit ?? 0.25,
    } as any,
    low_stock_threshold_default: initial.low_stock_threshold_default ?? 20,
    is_active: initial.is_active ?? true,
  });
  const [portal_password, setPortalPassword] = useState("");
  const set = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  const setRate = (k: string, v: any) => setF((s: any) => ({ ...s, billing_rates: { ...s.billing_rates, [k]: parseFloat(v) || 0 } }));

  const submit = () => {
    const payload: any = {
      company_name: f.company_name,
      contact_name: f.contact_name,
      email: f.email,
      phone: f.phone,
      billing_rates: f.billing_rates,
      low_stock_threshold_default: parseInt(f.low_stock_threshold_default) || 20,
      is_active: f.is_active,
    };
    if (portal_password) payload.portal_password = portal_password;
    onSave(payload);
  };

  return (
    <Modal title={title} onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={submit}>Save</button>
    </>}>
      <div className="form-group"><label>Company name *</label><input className="input" value={f.company_name} onChange={(e) => set("company_name", e.target.value)} /></div>
      <div className="form-group"><label>Contact name *</label><input className="input" value={f.contact_name} onChange={(e) => set("contact_name", e.target.value)} /></div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Email *</label><input className="input" type="email" value={f.email} onChange={(e) => set("email", e.target.value)} /></div>
        <div className="form-group"><label>Phone *</label><input className="input" value={f.phone} onChange={(e) => set("phone", e.target.value)} /></div>
      </div>
      <div style={{ fontWeight: 600, margin: "8px 0" }}>Billing rates</div>
      <div className="grid grid-3 gap">
        <div className="form-group"><label>Storage /unit/day</label><input className="input" type="number" step="0.01" value={f.billing_rates.storage_per_unit_per_day} onChange={(e) => setRate("storage_per_unit_per_day", e.target.value)} /></div>
        <div className="form-group"><label>Fulfillment /order</label><input className="input" type="number" step="0.01" value={f.billing_rates.fulfillment_per_order} onChange={(e) => setRate("fulfillment_per_order", e.target.value)} /></div>
        <div className="form-group"><label>Receiving /unit</label><input className="input" type="number" step="0.01" value={f.billing_rates.receiving_per_unit} onChange={(e) => setRate("receiving_per_unit", e.target.value)} /></div>
      </div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Low stock default</label><input className="input" type="number" value={f.low_stock_threshold_default} onChange={(e) => set("low_stock_threshold_default", e.target.value)} /></div>
        <div className="form-group"><label>Active</label>
          <select className="select" value={String(f.is_active)} onChange={(e) => set("is_active", e.target.value === "true")}>
            <option value="true">Active</option><option value="false">Inactive</option>
          </select></div>
      </div>
      {!initial.company_name && <div className="form-group"><label>Portal password</label><input className="input" type="password" value={portal_password} onChange={(e) => setPortalPassword(e.target.value)} /></div>}
    </Modal>
  );
}

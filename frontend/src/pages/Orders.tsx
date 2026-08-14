import { useEffect, useState } from "react";
import { getOrders, getSellers, getWarehouses, getProducts, createOrder, updateOrderStatus } from "../api/endpoints";
import type { Order, Seller, Warehouse, Product, OrderStatus } from "../api/types";
import { Spinner } from "../components/ui";
import { Modal } from "../components/Modal";
import { useToast } from "../lib/toast";
import { formatCurrency } from "../lib/status";

const STATUSES: OrderStatus[] = ["pending", "picking", "packed", "labeled", "shipped", "cancelled"];

export default function Orders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [shippingFor, setShippingFor] = useState<Order | null>(null);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [o, w] = await Promise.all([getOrders(), getWarehouses()]);
      setOrders(o); setWarehouses(w);
    } catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const move = async (id: string, status: OrderStatus, shipping?: any) => {
    try {
      await updateOrderStatus(id, status, shipping);
      toast(`Order -> ${status}`, "success");
      load();
    } catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
  };

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Orders</h1><p className="page-sub">Outbound order board</p></div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ Create Order</button>
      </div>
      {loading ? <Spinner /> : (
        <div className="grid" style={{ gridTemplateColumns: `repeat(${STATUSES.length}, 1fr)`, gap: 12 }}>
          {STATUSES.map((st) => (
            <div key={st} className="card" style={{ padding: 12, minHeight: 200 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <span className={`chip ${st === "shipped" ? "chip-success" : st === "pending" ? "chip-warning" : "chip-neutral"}`}>{st}</span>
                <span style={{ color: "#ABACA7" }}>{orders.filter((o) => o.status === st).length}</span>
              </div>
              {orders.filter((o) => o.status === st).map((o) => (
                <div key={o.id} style={{ background: "#F9FAF7", border: "1px solid #E6E7E0", borderRadius: 8, padding: 10, marginBottom: 8 }}>
                  <div style={{ fontWeight: 700 }}>{o.order_ref}</div>
                  <div style={{ color: "#ABACA7", fontSize: 12 }}>{o.customer?.name} · {o.items.length} items</div>
                  {o.shipping?.tracking_number && (
                    <div style={{ color: "#1B475D", fontSize: 12, marginTop: 4 }}>Tracking: {o.shipping.tracking_number} ({o.shipping.carrier}) · {formatCurrency(o.shipping.ship_cost)}</div>
                  )}
                  <select className="select" style={{ marginTop: 8, fontSize: 12 }} value={o.status} onChange={(e) => {
                    const ns = e.target.value as OrderStatus;
                    if ((ns === "labeled" || ns === "shipped") && !o.shipping) setShippingFor(o);
                    else move(o.id, ns);
                  }}>
                    {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
      {showCreate && <CreateOrderDialog warehouses={warehouses} onClose={() => setShowCreate(false)} onSaved={async (d) => {
        try { await createOrder(d); toast("Order created", "success"); setShowCreate(false); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
      {shippingFor && <ShippingDialog order={shippingFor} onClose={() => setShippingFor(null)} onSave={async (shipping) => {
        await move(shippingFor.id, "labeled", shipping);
        setShippingFor(null);
      }} />}
    </div>
  );
}

function ShippingDialog({ order, onClose, onSave }: { order: Order; onClose: () => void; onSave: (s: any) => void }) {
  const [f, setF] = useState<any>({ carrier: "", tracking_number: "", weight_lbs: 0, ship_cost: 0 });
  const set = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  return (
    <Modal title={`Shipping details — ${order.order_ref}`} onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={() => onSave(f)}>Label & Ship</button>
    </>}>
      <p style={{ color: "#ABACA7", margin: "0 0 12px" }}>Provide shipping details to label/ship this order.</p>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Carrier</label><input className="input" value={f.carrier} onChange={(e) => set("carrier", e.target.value)} /></div>
        <div className="form-group"><label>Tracking number</label><input className="input" value={f.tracking_number} onChange={(e) => set("tracking_number", e.target.value)} /></div>
      </div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Weight (lbs)</label><input className="input" type="number" step="0.1" value={f.weight_lbs} onChange={(e) => set("weight_lbs", parseFloat(e.target.value) || 0)} /></div>
        <div className="form-group"><label>Ship cost ($)</label><input className="input" type="number" step="0.01" value={f.ship_cost} onChange={(e) => set("ship_cost", parseFloat(e.target.value) || 0)} /></div>
      </div>
    </Modal>
  );
}

function CreateOrderDialog({ warehouses, onClose, onSaved }: { warehouses: Warehouse[]; onClose: () => void; onSaved: (d: any) => void }) {
  const [sellers, setSellers] = useState<Seller[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [f, setF] = useState<any>({ order_ref: "", seller_id: "", warehouse_id: "", assigned_to: "", customer: { name: "", address: "" }, items: [{ product_id: "", quantity: 1 }] });
  useEffect(() => { getSellers().then(setSellers); getProducts().then(setProducts); }, []);
  const set = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  const setItem = (i: number, k: string, v: any) => setF((s: any) => ({ ...s, items: s.items.map((x: any, idx: number) => idx === i ? { ...x, [k]: v } : x) }));
  return (
    <Modal title="Create Order" onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={() => onSaved(f)}>Create</button>
    </>}>
      <div className="form-group"><label>Order ref</label><input className="input" value={f.order_ref} onChange={(e) => set("order_ref", e.target.value)} /></div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Seller</label>
          <select className="select" value={f.seller_id} onChange={(e) => set("seller_id", e.target.value)}>
            <option value="">Select</option>{sellers.map((s) => <option key={s.id} value={s.id}>{s.company_name}</option>)}
          </select></div>
        <div className="form-group"><label>Warehouse</label>
          <select className="select" value={f.warehouse_id} onChange={(e) => set("warehouse_id", e.target.value)}>
            <option value="">Select</option>{warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
          </select></div>
      </div>
      <div className="form-group"><label>Assigned to (user id, optional)</label><input className="input" value={f.assigned_to} onChange={(e) => set("assigned_to", e.target.value)} /></div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Customer name</label><input className="input" value={f.customer.name} onChange={(e) => set("customer", { ...f.customer, name: e.target.value })} /></div>
        <div className="form-group"><label>Address</label><input className="input" value={f.customer.address} onChange={(e) => set("customer", { ...f.customer, address: e.target.value })} /></div>
      </div>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>Items</div>
      {f.items.map((it: any, i: number) => (
        <div className="flex gap" key={i} style={{ marginBottom: 8 }}>
          <select className="select" value={it.product_id} onChange={(e) => setItem(i, "product_id", e.target.value)}>
            <option value="">Product</option>{products.map((p) => <option key={p.id} value={p.id}>{p.product_name}</option>)}
          </select>
          <input className="input" style={{ width: 90 }} type="number" value={it.quantity} onChange={(e) => setItem(i, "quantity", parseInt(e.target.value) || 1)} />
        </div>
      ))}
      <button className="btn btn-secondary btn-sm" onClick={() => setF((s: any) => ({ ...s, items: [...s.items, { product_id: "", quantity: 1 }] }))}>+ Add item</button>
    </Modal>
  );
}

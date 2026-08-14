import { useEffect, useState } from "react";
import { getInventory, getLowStock, adjustInventory, getWarehouses, getProducts, getSellers } from "../api/endpoints";
import type { Inventory as Inv, Warehouse, Product, Seller } from "../api/types";
import { Table, Spinner } from "../components/ui";
import { Modal } from "../components/Modal";
import { useToast } from "../lib/toast";
import { formatNumber, formatDate } from "../lib/status";

export default function Inventory() {
  const [rows, setRows] = useState<Inv[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [sellers, setSellers] = useState<Seller[]>([]);
  const [warehouseId, setWarehouseId] = useState("");
  const [lowOnly, setLowOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [adjusting, setAdjusting] = useState<Inv | null>(null);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [inv, wh, prods, sell] = await Promise.all([
        lowOnly ? getLowStock(warehouseId || undefined) : getInventory(warehouseId || undefined),
        getWarehouses(), getProducts(), getSellers(),
      ]);
      setRows(inv as any);
      setWarehouses(wh); setProducts(prods); setSellers(sell);
    } catch (e: any) {
      toast(e.response?.data?.detail || "Failed to load inventory", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [warehouseId, lowOnly]);

  const whName = (id: string) => warehouses.find((w) => w.id === id)?.name ?? id.slice(0, 6);
  const prodName = (id: string) => products.find((p) => p.id === id)?.product_name ?? id.slice(0, 8);
  const sellerName = (id: string) => sellers.find((s) => s.id === id)?.company_name ?? id.slice(0, 6);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Inventory</h1>
          <p className="page-sub">Live stock levels per product per warehouse</p>
        </div>
        <div className="flex gap align-center">
          <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <input type="checkbox" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} />
            Low stock only
          </label>
          <select className="select" style={{ width: 180 }} value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)}>
            <option value="">All warehouses</option>
            {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
          </select>
          <button className="btn btn-secondary" onClick={load}>Refresh</button>
        </div>
      </div>

      <div className="card">
        {loading ? <Spinner /> : (
          <Table headers={["Product", "Seller", "Warehouse", "Bin", "Good", "Damaged", "Reserved", "Available", "Updated", ""]}>
            {(rows as any[]).map((r) => {
              const avail = r.quantity_available ?? r.available;
              const isLow = (r.quantity_available ?? r.available ?? 0) <= (r.low_stock_threshold ?? 5);
              return (
                <tr key={r.id ?? r.product_id}>
                  <td style={{ fontWeight: 600 }}>{r.product_name ?? prodName(r.product_id)}</td>
                  <td>{r.seller_id ? sellerName(r.seller_id) : "—"}</td>
                  <td>{r.warehouse_id ? whName(r.warehouse_id) : r.warehouse}</td>
                  <td>{r.bin_location ?? "—"}</td>
                  <td>{r.quantity_good ?? "—"}</td>
                  <td>{r.quantity_damaged ?? "—"}</td>
                  <td>{r.quantity_reserved ?? "—"}</td>
                  <td style={{ fontWeight: 700 }}>{formatNumber(avail)}</td>
                  <td>{r.last_updated ? formatDate(r.last_updated) : "—"}</td>
                  <td>{r.id && <button className="btn btn-sm btn-secondary" onClick={() => setAdjusting(r)}>Adjust</button>}</td>
                </tr>
              );
            })}
          </Table>
        )}
      </div>

      {adjusting && (
        <AdjustDialog
          inv={adjusting}
          onClose={() => setAdjusting(null)}
          onSaved={async (data) => {
            try {
              await adjustInventory(adjusting.id, data);
              toast("Stock adjusted", "success");
              setAdjusting(null);
              load();
            } catch (e: any) {
              toast(e.response?.data?.detail || "Adjust failed", "error");
            }
          }}
        />
      )}
    </div>
  );
}

function AdjustDialog({ inv, onClose, onSaved }: { inv: Inv; onClose: () => void; onSaved: (d: any) => void }) {
  const [good, setGood] = useState(String(inv.quantity_good));
  const [damaged, setDamaged] = useState(String(inv.quantity_damaged));
  const [bin, setBin] = useState(inv.bin_location);
  return (
    <Modal
      title="Adjust Stock"
      onClose={onClose}
      footer={<>
        <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSaved({
          quantity_good: parseInt(good) || 0,
          quantity_damaged: parseInt(damaged) || 0,
          bin_location: bin,
        })}>Save</button>
      </>}
    >
      <div className="form-group"><label>Quantity good</label>
        <input className="input" type="number" value={good} onChange={(e) => setGood(e.target.value)} /></div>
      <div className="form-group"><label>Quantity damaged</label>
        <input className="input" type="number" value={damaged} onChange={(e) => setDamaged(e.target.value)} /></div>
      <div className="form-group"><label>Bin location</label>
        <input className="input" value={bin} onChange={(e) => setBin(e.target.value)} /></div>
    </Modal>
  );
}

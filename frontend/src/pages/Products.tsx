import { useEffect, useState } from "react";
import { getProducts, getSellers, createProduct, updateProduct } from "../api/endpoints";
import type { Product, Seller } from "../api/types";
import { Table, Spinner } from "../components/ui";
import { Modal } from "../components/Modal";
import { useToast } from "../lib/toast";

export default function Products() {
  const [products, setProducts] = useState<Product[]>([]);
  const [sellers, setSellers] = useState<Seller[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [p, s] = await Promise.all([getProducts(), getSellers()]);
      setProducts(p); setSellers(s);
    } catch (e: any) {
      toast(e.response?.data?.detail || "Failed to load products", "error");
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const sellerName = (id: string) => sellers.find((s) => s.id === id)?.company_name ?? id.slice(0, 6);

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Products</h1><p className="page-sub">Product catalog</p></div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ Add Product</button>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <Table headers={["Name", "SKU", "UPC", "Seller", "Category", "Dimensions", "Low Stock", "Active", ""]}>
            {products.map((p) => (
              <tr key={p.id}>
                <td style={{ fontWeight: 600 }}>{p.product_name}</td>
                <td>{p.sku}</td>
                <td>{p.upc_barcode}</td>
                <td>{sellerName(p.seller_id)}</td>
                <td>{p.category || "—"}</td>
                <td>{p.dimensions.weight_lbs}lb · {p.dimensions.length_in}x{p.dimensions.width_in}x{p.dimensions.height_in}in</td>
                <td>{p.low_stock_threshold}</td>
                <td>{p.is_active ? <span className="chip chip-success">Active</span> : <span className="chip chip-neutral">Inactive</span>}</td>
                <td><button className="btn btn-sm btn-secondary" onClick={() => setEditing(p)}>Edit</button></td>
              </tr>
            ))}
          </Table>
        )}
      </div>
      {showAdd && <ProductForm title="Add Product" initial={{} as Product} sellers={sellers} onClose={() => setShowAdd(false)} onSave={async (d) => {
        try { await createProduct(d); toast("Product created", "success"); setShowAdd(false); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
      {editing && <ProductForm title="Edit Product" initial={editing} sellers={sellers} onClose={() => setEditing(null)} onSave={async (d) => {
        try { await updateProduct(editing.id, d); toast("Product updated", "success"); setEditing(null); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
    </div>
  );
}

function ProductForm({ title, initial, sellers, onClose, onSave }: {
  title: string; initial: Product; sellers: Seller[]; onClose: () => void; onSave: (d: any) => void;
}) {
  const [f, setF] = useState<any>({
    seller_id: initial.seller_id ?? "",
    upc_barcode: initial.upc_barcode ?? "",
    sku: initial.sku ?? "",
    product_name: initial.product_name ?? "",
    description: initial.description ?? "",
    dimensions: {
      weight_lbs: initial.dimensions?.weight_lbs ?? 0,
      length_in: initial.dimensions?.length_in ?? 0,
      width_in: initial.dimensions?.width_in ?? 0,
      height_in: initial.dimensions?.height_in ?? 0,
    },
    low_stock_threshold: initial.low_stock_threshold ?? 20,
    category: initial.category ?? "",
    is_active: initial.is_active ?? true,
  });
  const set = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  const setDim = (k: string, v: any) => setF((s: any) => ({ ...s, dimensions: { ...s.dimensions, [k]: parseFloat(v) || 0 } }));

  const submit = () => {
    onSave({
      ...f,
      seller_id: f.seller_id,
      low_stock_threshold: parseInt(f.low_stock_threshold) || 0,
    });
  };

  return (
    <Modal title={title} onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={submit}>Save</button>
    </>}>
      <div className="form-group"><label>Seller *</label>
        <select className="select" value={f.seller_id} onChange={(e) => set("seller_id", e.target.value)}>
          <option value="">Select seller</option>
          {sellers.map((s) => <option key={s.id} value={s.id}>{s.company_name}</option>)}
        </select></div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Product name *</label><input className="input" value={f.product_name} onChange={(e) => set("product_name", e.target.value)} /></div>
        <div className="form-group"><label>SKU *</label><input className="input" value={f.sku} onChange={(e) => set("sku", e.target.value)} /></div>
      </div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>UPC barcode *</label><input className="input" value={f.upc_barcode} onChange={(e) => set("upc_barcode", e.target.value)} /></div>
        <div className="form-group"><label>Category</label><input className="input" value={f.category} onChange={(e) => set("category", e.target.value)} /></div>
      </div>
      <div className="form-group"><label>Description</label><textarea className="textarea" value={f.description} onChange={(e) => set("description", e.target.value)} /></div>
      <div style={{ fontWeight: 600, margin: "8px 0" }}>Dimensions</div>
      <div className="grid grid-4 gap">
        <div className="form-group"><label>Weight (lbs)</label><input className="input" type="number" step="0.01" value={f.dimensions.weight_lbs} onChange={(e) => setDim("weight_lbs", e.target.value)} /></div>
        <div className="form-group"><label>Length (in)</label><input className="input" type="number" step="0.01" value={f.dimensions.length_in} onChange={(e) => setDim("length_in", e.target.value)} /></div>
        <div className="form-group"><label>Width (in)</label><input className="input" type="number" step="0.01" value={f.dimensions.width_in} onChange={(e) => setDim("width_in", e.target.value)} /></div>
        <div className="form-group"><label>Height (in)</label><input className="input" type="number" step="0.01" value={f.dimensions.height_in} onChange={(e) => setDim("height_in", e.target.value)} /></div>
      </div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Low stock threshold</label><input className="input" type="number" value={f.low_stock_threshold} onChange={(e) => set("low_stock_threshold", e.target.value)} /></div>
        <div className="form-group"><label>Active</label>
          <select className="select" value={String(f.is_active)} onChange={(e) => set("is_active", e.target.value === "true")}>
            <option value="true">Active</option><option value="false">Inactive</option>
          </select></div>
      </div>
    </Modal>
  );
}

import { useEffect, useState } from "react";
import {
  sellerGetMe, sellerGetProducts, sellerGetInventory, sellerGetOrders,
  sellerGetShipments, sellerGetReturns, sellerGetInvoices, sellerGetNotifications,
} from "../api/endpoints";
import { Table, Spinner } from "../components/ui";
import { useToast } from "../lib/toast";
import { formatCurrency, formatDate, statusChip } from "../lib/status";

// ---- Seller Overview (dashboard) ----
export function SellerOverview() {
  const [me, setMe] = useState<any>(null);
  const [inventory, setInventory] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  useEffect(() => {
    Promise.all([sellerGetMe(), sellerGetInventory(), sellerGetOrders(), sellerGetInvoices()])
      .then(([m, i, o, inv]) => { setMe(m); setInventory(i); setOrders(o); setInvoices(inv); })
      .catch((e) => toast(e.response?.data?.detail || "Failed", "error"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  const shipped = orders.filter((o) => o.status === "shipped").length;
  const available = inventory.reduce((s, i) => s + (i.quantity_available ?? 0), 0);
  const revenue = invoices.reduce((s, i) => s + (i.total ?? 0), 0);

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Overview</h1><p className="page-sub">Welcome back, {me?.contact_name}</p></div>
      </div>
      <div className="grid grid-4 mb">
        <Stat icon="📦" bg="#8FBFA022" label="Total Orders" value={`${orders.length}`} />
        <Stat icon="🚚" bg="#7FA9B522" label="Shipped" value={`${shipped}`} />
        <Stat icon="🗄️" bg="#F2C14E22" label="Units Available" value={`${available}`} />
        <Stat icon="💵" bg="#B9AEDD22" label="Total Invoiced" value={formatCurrency(revenue)} />
      </div>
      <div className="card card-pad">
        <h3 style={{ margin: "0 0 16px", fontFamily: "Poppins", fontWeight: 600 }}>Your Invoices</h3>
        <Table headers={["Ref", "Period", "Total", "Status"]}>
          {invoices.map((i) => (
            <tr key={i.id}>
              <td style={{ fontWeight: 600 }}>{i.invoice_ref}</td>
              <td>{i.period?.month}/{i.period?.year}</td>
              <td>{formatCurrency(i.total)}</td>
              <td><span className={`chip ${statusChip(i.status)}`}>{i.status}</span></td>
            </tr>
          ))}
        </Table>
      </div>
    </div>
  );
}

function Stat({ icon, bg, label, value }: { icon: string; bg: string; label: string; value: string }) {
  return (
    <div className="card stat-card">
      <div className="stat-icon" style={{ background: bg }}>{icon}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

// ---- Reusable seller data table page ----
function SellerTablePage({ title, subtitle, fetchFn, columns, row }: {
  title: string; subtitle: string;
  fetchFn: () => Promise<any[]>;
  columns: string[];
  row: (d: any) => React.ReactNode;
}) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();
  useEffect(() => {
    fetchFn().then(setData).catch((e) => toast(e.response?.data?.detail || "Failed", "error")).finally(() => setLoading(false));
  }, []);
  return (
    <div>
      <div className="page-header"><div><h1 className="page-title">{title}</h1><p className="page-sub">{subtitle}</p></div></div>
      <div className="card">{loading ? <Spinner /> : <Table headers={columns}>{data.map((d, i) => <tr key={d.id ?? i}>{row(d)}</tr>)}</Table>}</div>
    </div>
  );
}

export function SellerProducts() {
  return <SellerTablePage title="Products" subtitle="Your product catalog" fetchFn={sellerGetProducts}
    columns={["Name", "SKU", "UPC", "Category"]}
    row={(p) => <><td style={{ fontWeight: 600 }}>{p.product_name}</td><td>{p.sku}</td><td>{p.upc_barcode}</td><td>{p.category || "—"}</td></>} />;
}

export function SellerInventory() {
  return <SellerTablePage title="Inventory" subtitle="Your stock levels" fetchFn={sellerGetInventory}
    columns={["Product", "Warehouse", "Good", "Damaged", "Reserved", "Available"]}
    row={(i) => <><td style={{ fontWeight: 600 }}>{i.product_name}</td><td>{i.warehouse}</td><td>{i.quantity_good}</td><td>{i.quantity_damaged}</td><td>{i.quantity_reserved}</td><td style={{ fontWeight: 700 }}>{i.quantity_available}</td></>} />;
}

export function SellerOrders() {
  return <SellerTablePage title="Orders" subtitle="Your customer orders" fetchFn={sellerGetOrders}
    columns={["Order", "Status", "Warehouse", "Customer", "Items"]}
    row={(o) => <><td style={{ fontWeight: 600 }}>{o.order_ref}</td><td><span className={`chip ${statusChip(o.status)}`}>{o.status}</span></td><td>{o.warehouse}</td><td>{o.customer}</td><td>{o.items?.length}</td></>} />;
}

export function SellerShipments() {
  return <SellerTablePage title="Shipments" subtitle="Your inbound shipments" fetchFn={sellerGetShipments}
    columns={["Ref", "Status", "Warehouse", "Carrier", "Received"]}
    row={(s) => <><td style={{ fontWeight: 600 }}>{s.shipment_ref}</td><td><span className={`chip ${statusChip(s.status)}`}>{s.status}</span></td><td>{s.warehouse}</td><td>{s.carrier}</td><td>{formatDate(s.received_at)}</td></>} />;
}

export function SellerReturns() {
  return <SellerTablePage title="Returns" subtitle="Your returns" fetchFn={sellerGetReturns}
    columns={["Ref", "Order", "Status", "Completed"]}
    row={(r) => <><td style={{ fontWeight: 600 }}>{r.return_ref}</td><td>{r.original_order_ref}</td><td><span className={`chip ${statusChip(r.status)}`}>{r.status}</span></td><td>{formatDate(r.completed_at)}</td></>} />;
}

export function SellerInvoices() {
  return <SellerTablePage title="Invoices" subtitle="Your monthly invoices" fetchFn={sellerGetInvoices}
    columns={["Ref", "Period", "Total", "Status"]}
    row={(i) => <><td style={{ fontWeight: 600 }}>{i.invoice_ref}</td><td>{i.period?.month}/{i.period?.year}</td><td>{formatCurrency(i.total)}</td><td><span className={`chip ${statusChip(i.status)}`}>{i.status}</span></td></>} />;
}

export function SellerNotifications() {
  return <SellerTablePage title="Notifications" subtitle="Alerts about your account" fetchFn={sellerGetNotifications}
    columns={["Subject", "Message", "When"]}
    row={(n) => <><td style={{ fontWeight: 600 }}>{n.subject}</td><td>{n.message}</td><td>{formatDate(n.created_at)}</td></>} />;
}

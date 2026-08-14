import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { getDashboard, getOrders } from "../api/endpoints";
import type { Dashboard as DashboardData, Order } from "../api/types";
import { useToast } from "../lib/toast";
import { formatDate } from "../lib/status";
import { Spinner } from "../components/ui";

const PIE_COLORS = ["#1C3D4F", "#F2C14E", "#8FBFA0", "#B9AEDD", "#7FA9B5", "#D9695F"];

function Stat({ icon, bg, label, value, change }: { icon: string; bg: string; label: string; value: string; change?: { dir: "up" | "down" | "flat"; pct: string } }) {
  return (
    <div className="card stat-card">
      <div className="stat-icon" style={{ background: bg }}>{icon}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {change && <span className={`stat-change ${change.dir}`}>{change.dir === "up" ? "▲" : change.dir === "down" ? "▼" : "•"} {change.pct}</span>}
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  useEffect(() => {
    Promise.all([getDashboard(), getOrders()])
      .then(([d, o]) => { setData(d); setOrders(o); })
      .catch((e) => toast(e.response?.data?.detail || "Failed to load dashboard", "error"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;

  const orderBreakdown = Object.entries(
    orders.reduce<Record<string, number>>((acc, o) => { acc[o.status] = (acc[o.status] ?? 0) + 1; return acc; }, {})
  ).map(([name, value]) => ({ name, value }));

  const shipped = orders.filter((o) => o.status === "shipped").length;
  const pending = orders.filter((o) => ["pending", "picking", "packed"].includes(o.status)).length;
  const revenue = orders.filter((o) => o.status === "shipped").reduce((s, o) => s + (o.shipping?.ship_cost ?? 0), 0);
  const totalUnits = data?.inventory?.reduce((s, i) => s + i.units, 0) ?? 0;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-sub">Live overview of both warehouses</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-4 mb">
        <Stat icon="💵" bg="#F2C14E22" label="Revenue (shipped)" value={`$${revenue.toFixed(2)}`} change={{ dir: shipped > pending ? "up" : "flat", pct: `${shipped} shipped` }} />
        <Stat icon="📦" bg="#8FBFA022" label="Orders" value={`${orders.length}`} change={{ dir: pending > 0 ? "up" : "flat", pct: `${pending} pending` }} />
        <Stat icon="🏬" bg="#B9AEDD22" label="Warehouses" value={`${data?.warehouses?.length ?? 0}`} change={{ dir: "flat", pct: "active" }} />
        <Stat icon="🗄️" bg="#7FA9B522" label="Total Units" value={`${totalUnits}`} change={{ dir: "flat", pct: "in stock" }} />
      </div>

      {/* Charts */}
      <div className="grid grid-2 mb">
        <div className="card card-pad">
          <div className="flex between align-center" style={{ marginBottom: 16 }}>
            <h3 style={{ margin: 0, fontFamily: "Poppins", fontWeight: 600, fontSize: 16 }}>Units per Warehouse</h3>
            <span style={{ color: "var(--muted)", fontSize: 13 }}>⋯</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={(data?.inventory ?? []).map((i) => ({ name: `WH ${i.warehouse_id.slice(0, 5)}`, units: i.units }))}>
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#8A93A0" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: "#8A93A0" }} axisLine={false} tickLine={false} />
              <Tooltip />
              <Bar dataKey="units" fill="#1C3D4F" radius={[6, 6, 0, 0]} />
              <Bar dataKey="low_stock" fill="#F2C14E" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card card-pad">
          <div className="flex between align-center" style={{ marginBottom: 16 }}>
            <h3 style={{ margin: 0, fontFamily: "Poppins", fontWeight: 600, fontSize: 16 }}>Order Status</h3>
            <span style={{ color: "var(--muted)", fontSize: 13 }}>⋯</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={orderBreakdown} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                {orderBreakdown.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Legend /><Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Warehouse overview */}
      <div className="grid grid-2 mb">
        {(data?.warehouses ?? []).map((w) => (
          <div className="card card-pad" key={w.warehouse_id}>
            <h3 style={{ margin: "0 0 16px", fontFamily: "Poppins", fontSize: 16, fontWeight: 600 }}>🏭 {w.warehouse_name}</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <MiniStat label="Staff active" value={w.staff_active} />
              <MiniStat label="Pending orders" value={w.pending_orders} />
              <MiniStat label="Shipments today" value={w.shipments_today} />
              <MiniStat label="Alerts" value={w.alerts} danger={w.alerts > 0} />
            </div>
          </div>
        ))}
      </div>

      {/* Top selling / recent orders */}
      <div className="card card-pad mb">
        <div className="flex between align-center" style={{ marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontFamily: "Poppins", fontSize: 16, fontWeight: 600 }}>Recent Orders</h3>
          <span style={{ color: "var(--muted)", fontSize: 13 }}>⋯</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Order</th><th>Customer</th><th>Items</th><th>Status</th><th>When</th></tr></thead>
            <tbody>
              {orders.slice(0, 8).map((o) => (
                <tr key={o.id}>
                  <td style={{ fontWeight: 600 }}>{o.order_ref}</td>
                  <td>{o.customer?.name}</td>
                  <td>{o.items.length}</td>
                  <td><span className="chip chip-warning">{o.status}</span></td>
                  <td>{formatDate(o.created_at as any)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Activity feed */}
      <div className="card card-pad">
        <h3 style={{ margin: "0 0 16px", fontFamily: "Poppins", fontSize: 16, fontWeight: 600 }}>Live Activity</h3>
        <div className="table-wrap">
          <table>
            <thead><tr><th>When</th><th>User</th><th>Action</th></tr></thead>
            <tbody>
              {(data?.activity_feed ?? []).slice(0, 10).map((a) => (
                <tr key={a.id}>
                  <td>{formatDate(a.created_at)}</td>
                  <td>{a.user_name}</td>
                  <td>{a.action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MiniStat({ label, value, danger }: { label: string; value: number; danger?: boolean }) {
  return (
    <div style={{ background: "#F7F8F4", borderRadius: 12, padding: "10px 14px" }}>
      <div style={{ color: "var(--muted)", fontSize: 12 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: danger ? "var(--danger)" : "var(--text)" }}>{value}</div>
    </div>
  );
}

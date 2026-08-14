import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { LayoutDashboard, Boxes, Package, Truck, ShoppingCart, Undo2, Receipt, Bell, LogOut } from "lucide-react";
import { useAuth } from "../lib/auth";
import { sellerGetMe } from "../api/endpoints";

const SELLER_NAV = [
  { to: "/seller", label: "Overview", icon: LayoutDashboard },
  { to: "/seller/products", label: "Products", icon: Package },
  { to: "/seller/inventory", label: "Inventory", icon: Boxes },
  { to: "/seller/orders", label: "Orders", icon: ShoppingCart },
  { to: "/seller/shipments", label: "Shipments", icon: Truck },
  { to: "/seller/returns", label: "Returns", icon: Undo2 },
  { to: "/seller/invoices", label: "Invoices", icon: Receipt },
  { to: "/seller/notifications", label: "Notifications", icon: Bell },
];

export default function SellerLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [company, setCompany] = useState("");

  useEffect(() => {
    sellerGetMe().then((m) => setCompany(m.company_name)).catch(() => {});
  }, []);

  const isActive = (to: string) => location.pathname === to;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="logo">
          <span className="logo-mark" />
          Seller Portal
        </div>
        <div style={{ padding: "4px 24px 12px", color: "#7A95A8", fontSize: 13 }}>{company || user?.full_name}</div>
        {SELLER_NAV.map((n) => {
          const Icon = n.icon;
          return (
            <button key={n.to} className={`nav-link ${isActive(n.to) ? "active" : ""}`} onClick={() => navigate(n.to)}>
              <Icon size={18} /> {n.label}
            </button>
          );
        })}
        <div className="nav-link logout" onClick={logout}><LogOut size={18} /> Logout</div>
      </aside>
      <div style={{ flex: 1, minWidth: 0 }}>
        <header className="topbar">
          <div style={{ fontWeight: 600, fontFamily: "Poppins", fontSize: 16 }}>Seller Portal</div>
          <div className="user-chip">
            <div className="avatar">{(user?.full_name || "?").charAt(0).toUpperCase()}</div>
            <div style={{ lineHeight: 1.1 }}>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{user?.full_name}</div>
              <div style={{ fontSize: 11, color: "var(--muted)" }}>seller</div>
            </div>
          </div>
        </header>
        <main className="main">{children}</main>
      </div>
    </div>
  );
}

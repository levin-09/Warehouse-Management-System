import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, useParams } from "react-router-dom";
import { LayoutDashboard, Boxes, Package, Truck, ShoppingCart, Undo2, AlertTriangle, MapPin, Building2, Users as UsersIcon, Receipt, Bell, History, MessageSquare, LogOut, Store, Mic, Search, Calendar, Sun } from "lucide-react";
import { useAuth } from "./lib/auth";
import { useToast } from "./lib/toast";
import { canAccess, ROLE_HOME } from "./lib/permissions";
import Login from "./pages/Login";
import SellerLayout from "./pages/SellerLayout";
import { SellerOverview, SellerProducts, SellerInventory, SellerOrders, SellerShipments, SellerReturns, SellerInvoices, SellerNotifications } from "./pages/SellerPages";
import Dashboard from "./pages/Dashboard";
import Inventory from "./pages/Inventory";
import Products from "./pages/Products";
import Shipments from "./pages/Shipments";
import Orders from "./pages/Orders";
import Returns from "./pages/Returns";
import Damage from "./pages/Damage";
import Bins from "./pages/Bins";
import Sellers from "./pages/Sellers";
import Warehouses from "./pages/Warehouses";
import Users from "./pages/Users";
import Invoices from "./pages/Invoices";
import Notifications from "./pages/Notifications";
import Audit from "./pages/Audit";
import Chat from "./pages/Chat";
import Voice from "./pages/Voice";

function Protected({ children, seller = false, path }: { children: React.ReactNode; seller?: boolean; path?: string }) {
  const { user } = useAuth();
  if (!user) return <Navigate to={seller ? "/seller-login" : "/login"} replace />;
  const role = user.role;
  // If role is missing (stale localStorage), don't lock the user out — render.
  if (!role) return <>{children}</>;
  // A seller can only use the seller portal.
  if (role === "seller" && !isSellerPath(path)) return <Navigate to="/seller" replace />;
  // A non-seller cannot use the seller portal.
  if (role !== "seller" && isSellerPath(path)) return <Navigate to={ROLE_HOME[role as "admin" | "manager" | "staff"] ?? "/"} replace />;
  // Enforce page access by role.
  if (path && !canAccess(role, path)) return <Navigate to={ROLE_HOME[role as "admin" | "manager" | "staff"] ?? "/"} replace />;
  return <>{children}</>;
}

// Match the seller portal path exactly or a sub-path under /seller/,
// but NOT /sellers (the admin Sellers page) — those are different.
function isSellerPath(path?: string): boolean {
  if (!path) return false;
  return path === "/seller" || path.startsWith("/seller/");
}

const NAV = [
  { group: "Overview", items: [
    { to: "/", label: "Dashboard", icon: LayoutDashboard, roles: ["admin", "manager", "staff"] },
  ]},
  { group: "Operations", items: [
    { to: "/inventory", label: "Inventory", icon: Boxes, roles: ["admin", "manager", "staff"] },
    { to: "/products", label: "Products", icon: Package, roles: ["admin", "manager", "staff"] },
    { to: "/shipments", label: "Shipments", icon: Truck, roles: ["admin", "manager", "staff"] },
    { to: "/orders", label: "Orders", icon: ShoppingCart, roles: ["admin", "manager", "staff"] },
    { to: "/returns", label: "Returns", icon: Undo2, roles: ["admin", "manager"] },
    { to: "/damage", label: "Damage", icon: AlertTriangle, roles: ["admin", "manager", "staff"] },
    { to: "/bins", label: "Bin Locations", icon: MapPin, roles: ["admin", "manager", "staff"] },
  ]},
  { group: "Admin", items: [
    { to: "/sellers", label: "Sellers", icon: Store, roles: ["admin"] },
    { to: "/warehouses", label: "Warehouses", icon: Building2, roles: ["admin", "manager"] },
    { to: "/users", label: "Users", icon: UsersIcon, roles: ["admin"] },
    { to: "/invoices", label: "Invoices", icon: Receipt, roles: ["admin", "manager"] },
    { to: "/notifications", label: "Notifications", icon: Bell, roles: ["admin", "manager", "staff"] },
    { to: "/audit", label: "Audit Logs", icon: History, roles: ["admin", "manager"] },
  ]},
  { group: "AI", items: [
    { to: "/assistant", label: "Assistant", icon: MessageSquare, roles: ["admin", "manager", "staff"] },
    { to: "/voice", label: "Voice Assistant", icon: Mic, roles: ["admin", "manager", "staff"] },
  ]},
];

function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const role = user?.role ?? "";
  const isSeller = role === "seller";
  const path = location.pathname;
  const isActive = (to: string) => to === "/" ? path === "/" : path.startsWith(to);

  const handleSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const q = (e.target as HTMLInputElement).value.trim();
    if (e.key !== "Enter" || !q) return;
    // Simple navigation-based search: jump to the most relevant page.
    const low = q.toLowerCase();
    if (/order/.test(low)) navigate("/orders");
    else if (/inventor|stock/.test(low)) navigate("/inventory");
    else if (/product/.test(low)) navigate("/products");
    else if (/ship/.test(low)) navigate("/shipments");
    else if (/warehouse/.test(low)) navigate("/warehouses");
    else if (/seller|client/.test(low)) navigate("/sellers");
    else if (/invoice|bill/.test(low)) navigate("/invoices");
    else if (/return/.test(low)) navigate("/returns");
    else if (/damage/.test(low)) navigate("/damage");
    else if (/bin|location/.test(low)) navigate("/bins");
    else if (/user|staff/.test(low)) navigate("/users");
    else toast(`No exact match for "${q}" — opened dashboard`, "info"), navigate("/");
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="logo">
          <span className="logo-mark" />
          {isSeller ? "Seller Portal" : "IronNest"}
        </div>
        {NAV.map((g) => {
          const items = g.items.filter((i) => i.roles.includes(role));
          if (!items.length) return null;
          return (
            <div className="nav-group" key={g.group}>
              <div className="nav-group-label">{g.group}</div>
              {items.map((i) => {
                const Icon = i.icon;
                const active = isActive(i.to);
                return (
                  <button key={i.to} className={`nav-link ${active ? "active" : ""}`} onClick={() => navigate(i.to)}>
                    <Icon size={18} /> {i.label}
                  </button>
                );
              })}
            </div>
          );
        })}
        <div className="nav-link logout" onClick={logout}>
          <LogOut size={18} /> Logout
        </div>
      </aside>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <header className="topbar">
          <div className="topbar-left">
            <div className="searchbox">
              <Search size={16} />
              <input placeholder="Find inventory, orders or reports" onKeyDown={handleSearch} />
            </div>
          </div>
          <div className="topbar-right">
            <button className="icon-btn"><Bell size={16} /></button>
            <button className="icon-btn"><Calendar size={16} /></button>
            <button className="icon-btn active"><Sun size={16} /></button>
            <div className="user-chip">
              <div className="avatar">{(user?.full_name || "?").charAt(0).toUpperCase()}</div>
              <div style={{ lineHeight: 1.1 }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{user?.full_name}</div>
                <div style={{ fontSize: 11, color: "var(--muted)", textTransform: "capitalize" }}>{role}</div>
              </div>
            </div>
          </div>
        </header>
        <main className="main">{children}</main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/seller-login" element={<Login isSeller />} />
        <Route path="/" element={<Protected path="/"><Layout><Dashboard /></Layout></Protected>} />
        <Route path="/inventory" element={<Protected path="/inventory"><Layout><Inventory /></Layout></Protected>} />
        <Route path="/products" element={<Protected path="/products"><Layout><Products /></Layout></Protected>} />
        <Route path="/shipments" element={<Protected path="/shipments"><Layout><Shipments /></Layout></Protected>} />
        <Route path="/orders" element={<Protected path="/orders"><Layout><Orders /></Layout></Protected>} />
        <Route path="/returns" element={<Protected path="/returns"><Layout><Returns /></Layout></Protected>} />
        <Route path="/damage" element={<Protected path="/damage"><Layout><Damage /></Layout></Protected>} />
        <Route path="/bins" element={<Protected path="/bins"><Layout><Bins /></Layout></Protected>} />
        <Route path="/sellers" element={<Protected path="/sellers"><Layout><Sellers /></Layout></Protected>} />
        <Route path="/warehouses" element={<Protected path="/warehouses"><Layout><Warehouses /></Layout></Protected>} />
        <Route path="/users" element={<Protected path="/users"><Layout><Users /></Layout></Protected>} />
        <Route path="/invoices" element={<Protected path="/invoices"><Layout><Invoices /></Layout></Protected>} />
        <Route path="/notifications" element={<Protected path="/notifications"><Layout><Notifications /></Layout></Protected>} />
        <Route path="/audit" element={<Protected path="/audit"><Layout><Audit /></Layout></Protected>} />
        <Route path="/assistant" element={<Protected path="/assistant"><Layout><Chat /></Layout></Protected>} />
        <Route path="/voice" element={<Protected path="/voice"><Layout><Voice /></Layout></Protected>} />
        {/* Seller portal */}
        <Route path="/seller" element={<Protected seller path="/seller"><SellerLayout><SellerOverview /></SellerLayout></Protected>} />
        <Route path="/seller/products" element={<Protected seller path="/seller/products"><SellerLayout><SellerProducts /></SellerLayout></Protected>} />
        <Route path="/seller/inventory" element={<Protected seller path="/seller/inventory"><SellerLayout><SellerInventory /></SellerLayout></Protected>} />
        <Route path="/seller/orders" element={<Protected seller path="/seller/orders"><SellerLayout><SellerOrders /></SellerLayout></Protected>} />
        <Route path="/seller/shipments" element={<Protected seller path="/seller/shipments"><SellerLayout><SellerShipments /></SellerLayout></Protected>} />
        <Route path="/seller/returns" element={<Protected seller path="/seller/returns"><SellerLayout><SellerReturns /></SellerLayout></Protected>} />
        <Route path="/seller/invoices" element={<Protected seller path="/seller/invoices"><SellerLayout><SellerInvoices /></SellerLayout></Protected>} />
        <Route path="/seller/notifications" element={<Protected seller path="/seller/notifications"><SellerLayout><SellerNotifications /></SellerLayout></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

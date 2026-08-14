// Centralized role-based access control for the frontend.
// Mirrors the backend RBAC policy in core/utils/rbac.py.

export type Role = "admin" | "manager" | "staff" | "seller";

// Which pages each role can see. Keys match nav item `to` paths.
export const ROLE_PAGES: Record<Role, string[]> = {
  admin: [
    "/", "/inventory", "/products", "/shipments", "/orders", "/returns", "/damage", "/bins",
    "/sellers", "/warehouses", "/users", "/invoices", "/notifications", "/audit", "/assistant", "/voice",
  ],
  // Manager: everything except Users and Sellers management.
  manager: [
    "/", "/inventory", "/products", "/shipments", "/orders", "/returns", "/damage", "/bins",
    "/warehouses", "/invoices", "/notifications", "/audit", "/assistant", "/voice",
  ],
  // Staff: warehouse operations only. No admin/management pages.
  staff: [
    "/", "/inventory", "/products", "/shipments", "/orders", "/damage", "/bins", "/notifications",
    "/assistant", "/voice",
  ],
  // Seller: scoped seller portal (own data only).
  seller: [
    "/seller", "/seller/products", "/seller/inventory", "/seller/orders", "/seller/shipments",
    "/seller/returns", "/seller/invoices", "/seller/notifications",
  ],
};

// A page is allowed for a role if it's in ROLE_PAGES (or is the seller home).
// If the role is missing/unknown (e.g. stale localStorage), do NOT over-restrict —
// allow access so users aren't falsely redirected to the dashboard.
export function canAccess(role: Role | string | undefined, path: string): boolean {
  if (!role) return true;
  const pages = ROLE_PAGES[role as Role] ?? [];
  if (pages.includes(path)) return true;
  // Allow sub-routes under an allowed prefix.
  return pages.some((p) => p !== "/" && path.startsWith(p + "/"));
}

// The landing page after login for each role.
export const ROLE_HOME: Record<Role, string> = {
  admin: "/",
  manager: "/",
  staff: "/",
  seller: "/seller",
};

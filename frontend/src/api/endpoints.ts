import { api } from "./client";
import type {
  AuditLog, AuthUser, BinLocation, DamageRecord, Dashboard, Inventory, Invoice,
  Notification, Order, OrderStatus, Product, Return, Seller, Shipment, StockLevel,
  UserRole, Warehouse,
} from "./types";

// ---- Auth ----
export const login = (email: string, password: string) =>
  api.post<AuthUser>("/v1/auth/login", { email, password }).then((r) => r.data);
export const sellerLogin = (email: string, password: string) =>
  api.post<AuthUser>("/v1/auth/seller/login", { email, password }).then((r) => r.data);
export const changePassword = (old_password: string, new_password: string) =>
  api.post("/v1/users/me/password", { old_password, new_password }).then((r) => r.data);

// ---- Dashboard ----
export const getDashboard = () => api.get<Dashboard>("/v1/dashboard/overview").then((r) => r.data);

// ---- Warehouses ----
export const getWarehouses = () => api.get<Warehouse[]>("/v1/warehouses").then((r) => r.data);
export const createWarehouse = (data: Partial<Warehouse>) => api.post("/v1/warehouses", data).then((r) => r.data);
export const updateWarehouse = (id: string, data: Partial<Warehouse>) => api.patch(`/v1/warehouses/${id}`, data).then((r) => r.data);

// ---- Sellers ----
export const getSellers = () => api.get<Seller[]>("/v1/sellers").then((r) => r.data);
export const createSeller = (data: any) => api.post("/v1/sellers", data).then((r) => r.data);
export const updateSeller = (id: string, data: any) => api.patch(`/v1/sellers/${id}`, data).then((r) => r.data);

// ---- Products ----
export const getProducts = () => api.get<Product[]>("/v1/products").then((r) => r.data);
export const getProductByUpc = (upc: string) => api.get<Product>(`/v1/products/upc/${upc}`).then((r) => r.data);
export const createProduct = (data: any) => api.post("/v1/products", data).then((r) => r.data);
export const updateProduct = (id: string, data: any) => api.patch(`/v1/products/${id}`, data).then((r) => r.data);

// ---- Inventory ----
export const getInventory = (warehouseId?: string) =>
  api.get<Inventory[]>("/v1/inventory", { params: warehouseId ? { warehouse_id: warehouseId } : {} }).then((r) => r.data);
export const getLowStock = (warehouseId?: string) =>
  api.get<StockLevel[]>("/v1/inventory/low-stock", { params: warehouseId ? { warehouse_id: warehouseId } : {} }).then((r) => r.data);
export const adjustInventory = (id: string, data: any) => api.patch(`/v1/inventory/${id}`, data).then((r) => r.data);

// ---- Shipments ----
export const getShipments = (warehouseId?: string) =>
  api.get<Shipment[]>("/v1/shipments", { params: warehouseId ? { warehouse_id: warehouseId } : {} }).then((r) => r.data);
export const createShipmentDraft = (data: any) => api.post("/v1/shipments/draft", data).then((r) => r.data);
export const confirmShipment = (data: any) => api.post("/v1/shipments/confirm", data).then((r) => r.data);

// ---- Orders ----
export const getOrders = (warehouseId?: string) =>
  api.get<Order[]>("/v1/orders", { params: warehouseId ? { warehouse_id: warehouseId } : {} }).then((r) => r.data);
export const createOrder = (data: any) => api.post("/v1/orders", data).then((r) => r.data);
export const updateOrderStatus = (id: string, status: OrderStatus, shipping?: any) =>
  api.patch(`/v1/orders/${id}/status`, { status, shipping }).then((r) => r.data);

// ---- Returns ----
export const getReturns = () => api.get<Return[]>("/v1/returns").then((r) => r.data);
export const processReturn = (data: any) => api.post("/v1/returns", data).then((r) => r.data);

// ---- Damage ----
export const getDamageRecords = () => api.get<DamageRecord[]>("/v1/damage-records").then((r) => r.data);
export const createDamageRecord = (data: any) => api.post("/v1/damage-records", data).then((r) => r.data);

// ---- Bins ----
export const getBinLocations = () => api.get<BinLocation[]>("/v1/bin-locations").then((r) => r.data);
export const createBinLocation = (data: any) => api.post("/v1/bin-locations", data).then((r) => r.data);
export const updateBinLocation = (id: string, data: any) => api.patch(`/v1/bin-locations/${id}`, data).then((r) => r.data);

// ---- Users ----
export const getUsers = () => api.get<{ id: string; full_name: string; email: string; role: UserRole; warehouse_id: string; is_active: boolean; last_login: string | null }[]>("/v1/users").then((r) => r.data);
export const createUser = (data: any) => api.post("/v1/users", data).then((r) => r.data);
export const updateUser = (id: string, data: any) => api.patch(`/v1/users/${id}`, data).then((r) => r.data);
export const deleteUser = (id: string) => api.delete(`/v1/users/${id}`).then((r) => r.data);

// ---- Invoices ----
export const getInvoices = () => api.get<Invoice[]>("/v1/invoices").then((r) => r.data);
export const generateInvoices = (year: number, month: number) =>
  api.post(`/v1/invoices/generate?year=${year}&month=${month}`).then((r) => r.data);

// ---- Notifications ----
export const getNotifications = (unreadOnly = false) =>
  api.get<Notification[]>("/v1/notifications", { params: unreadOnly ? { unread_only: true } : {} }).then((r) => r.data);
export const markNotificationRead = (id: string) => api.patch(`/v1/notifications/${id}/read`).then((r) => r.data);

// ---- Audit ----
export const getAuditLogs = (limit = 50) => api.get<AuditLog[]>("/v1/audit-logs", { params: { limit } }).then((r) => r.data);

// ---- Seller Portal (seller-scoped) ----
export const sellerGetMe = () => api.get("/v1/seller/me").then((r) => r.data);
export const sellerGetProducts = () => api.get("/v1/seller/products").then((r) => r.data);
export const sellerGetInventory = () => api.get("/v1/seller/inventory").then((r) => r.data);
export const sellerGetOrders = () => api.get("/v1/seller/orders").then((r) => r.data);
export const sellerGetShipments = () => api.get("/v1/seller/shipments").then((r) => r.data);
export const sellerGetInvoices = () => api.get("/v1/seller/invoices").then((r) => r.data);
export const sellerGetReturns = () => api.get("/v1/seller/returns").then((r) => r.data);
export const sellerGetNotifications = () => api.get("/v1/seller/notifications").then((r) => r.data);

// ---- Chat ----
export const chat = (user_input: string, session_id = "default") =>
  api.post<{ response: string; session_id: string; tool_calls: { name: string; arguments: Record<string, unknown> }[] }>(
    "/v1/chat", { user_input, session_id }
  ).then((r) => r.data);

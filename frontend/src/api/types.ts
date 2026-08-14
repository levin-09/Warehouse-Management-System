// WMS entity + enum types, mirroring the backend schemas.

export type UserRole = "admin" | "manager" | "staff";
export type ShipmentStatus = "draft" | "received";
export type OrderStatus = "pending" | "picking" | "packed" | "labeled" | "shipped" | "cancelled";
export type DamageGrade = "A" | "B" | "C" | "D";
export type ReturnCondition = "resellable" | "damaged" | "unsellable";
export type ReturnAction = "restocked_to_good" | "placed_in_damaged" | "returned_to_seller" | "disposed";
export type ReturnStatus = "pending" | "completed" | "awaiting_seller" | "disposed";
export type InvoiceStatus = "draft" | "sent";
export type AuditMethod = "manual_entry" | "barcode_scan" | "voice_input" | "ai_agent" | "api_script" | "system_auto";

export interface AuthUser {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  role: string;
  warehouse_id: string;
  full_name: string;
}

export interface Warehouse {
  id: string;
  name: string;
  city: string;
  state: string;
  address: string;
  is_active: boolean;
  carrier_schedules: { carrier: string; pickup_time: string; days: string[] }[];
  operating_hours: { open: string; close: string } | null;
}

export interface Seller {
  id: string;
  company_name: string;
  contact_name: string;
  email: string;
  phone: string;
  billing_rates: { storage_per_unit_per_day: number; fulfillment_per_order: number; receiving_per_unit: number };
  low_stock_threshold_default: number;
  is_active: boolean;
}

export interface Product {
  id: string;
  seller_id: string;
  upc_barcode: string;
  sku: string;
  product_name: string;
  description: string;
  dimensions: { weight_lbs: number; length_in: number; width_in: number; height_in: number };
  low_stock_threshold: number;
  category: string;
  is_active: boolean;
}

export interface Inventory {
  id: string;
  product_id: string;
  warehouse_id: string;
  seller_id: string;
  quantity_good: number;
  quantity_damaged: number;
  quantity_reserved: number;
  quantity_available: number;
  bin_location: string;
  last_updated: string;
  last_updated_by: string | null;
}

export interface StockLevel {
  product_id: string;
  product_name: string;
  upc_barcode: string;
  warehouse_id: string;
  quantity_good: number;
  quantity_damaged: number;
  quantity_reserved: number;
  quantity_available: number;
  bin_location: string;
}

export interface Shipment {
  id: string;
  shipment_ref: string;
  seller_id: string;
  warehouse_id: string;
  carrier: string;
  status: ShipmentStatus;
  received_by: string | null;
  received_at: string | null;
  notes: string;
  items: ShipmentItem[];
}

export interface ShipmentItem {
  product_id: string;
  upc_barcode: string;
  product_name: string;
  quantity_expected: number;
  quantity_received: number;
  quantity_damaged: number;
  damage_grade: DamageGrade | null;
  damage_notes: string;
}

export interface Order {
  id: string;
  order_ref: string;
  seller_id: string;
  warehouse_id: string;
  customer: { name: string; address: string };
  status: OrderStatus;
  assigned_to: string | null;
  items: { product_id: string; upc_barcode: string; product_name: string; quantity: number }[];
  shipping: { carrier: string; tracking_number: string; weight_lbs: number; ship_cost: number; shipped_at: string | null } | null;
  created_at?: string;
}

export interface Return {
  id: string;
  return_ref: string;
  original_order_id: string;
  original_order_ref: string;
  seller_id: string;
  warehouse_id: string;
  items: { product_id: string; product_name: string; quantity: number; condition: ReturnCondition; damage_grade: DamageGrade | null; action_taken: ReturnAction | null }[];
  return_reason: string;
  status: ReturnStatus;
  processed_by: string | null;
  seller_notified: boolean;
  completed_at: string | null;
}

export interface DamageRecord {
  id: string;
  shipment_id: string | null;
  shipment_ref: string;
  product_id: string;
  product_name: string;
  seller_id: string;
  warehouse_id: string;
  quantity_damaged: number;
  damage_grade: DamageGrade;
  damage_notes: string;
  carrier: string;
  carrier_tracking: string;
  assessed_by: string | null;
  action_taken: string;
  seller_notified: boolean;
}

export interface BinLocation {
  id: string;
  warehouse_id: string;
  bin_code: string;
  aisle: string;
  row: string;
  shelf: string;
  bin: string;
  product_id: string | null;
  max_capacity: number;
  current_units: number;
  is_occupied: boolean;
}

export interface Invoice {
  id: string;
  invoice_ref: string;
  seller_id: string;
  seller_name: string;
  period: { month: number; year: number };
  line_items: { description: string; units: number; days: number; rate: number; amount: number }[];
  subtotal: number;
  tax: number;
  total: number;
  status: InvoiceStatus;
  sent_at: string;
}

export interface Notification {
  id: string;
  recipient_type: string;
  recipient_id: string;
  recipient_email: string;
  channel: string;
  notification_type: string;
  subject: string;
  message: string;
  is_read: boolean;
  is_sent: boolean;
  sent_at: string | null;
  created_at?: string;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  user_name: string;
  action: string;
  collection_name: string;
  record_id: string | null;
  warehouse_id: string | null;
  old_value: Record<string, unknown>;
  new_value: Record<string, unknown>;
  method: AuditMethod;
  ip_address: string;
  created_at: string;
}

export interface Dashboard {
  warehouses: {
    warehouse_id: string;
    warehouse_name: string;
    staff_active: number;
    pending_orders: number;
    shipments_today: number;
    alerts: number;
  }[];
  inventory: {
    warehouse_id: string;
    skus: number;
    units: number;
    low_stock: number;
    out_stock: number;
  }[];
  activity_feed: { id: string; user_name: string; action: string; created_at: string }[];
  quick_stats: { label: string; value: string }[];
}

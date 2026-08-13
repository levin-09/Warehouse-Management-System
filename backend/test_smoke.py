#!/usr/bin/env python3
"""Comprehensive smoke test for the Whitfield WMS backend.

Tests every registered endpoint and reports PASS/FAIL with status codes.
"""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000/v1"
results = []


def call(method, path, token=None, body=None):
    url = BASE + path
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw) if raw else None
            except Exception:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def record(name, status, expected, extra=""):
    ok = status in (expected if isinstance(expected, (list, tuple, set)) else [expected])
    mark = "PASS" if ok else "FAIL"
    results.append((mark, name, status))
    print(f"[{mark}] {name} -> {status} (expected {expected}) {extra}")


# ---- Auth (staff admin) ----
print("========== AUTH ==========")
s, r = call("POST", "/auth/login", body={"email": "dan@whitfieldfulfillment.com", "password": "admin123"})
record("admin login", s, 200)
admin = r["access_token"]
s, r = call("POST", "/auth/login", body={"email": "dan@whitfieldfulfillment.com", "password": "wrong"})
record("admin login wrong pw", s, 401)

# ---- Warehouses ----
print("========== WAREHOUSES ==========")
s, r = call("GET", "/warehouses", admin)
record("list warehouses", s, 200)
reno = [w["id"] for w in r if w["name"] == "Reno"][0]
col = [w["id"] for w in r if w["name"] == "Columbus"][0]
s, r = call("GET", f"/warehouses/{reno}", admin)
record("get warehouse", s, 200)
s, r = call("POST", "/warehouses", admin, {"name": "Austin", "city": "Austin", "state": "TX", "address": "1 St"})
record("create warehouse", s, 201)
s, r = call("PATCH", f"/warehouses/{reno}", admin, {"city": "Reno-City"})
record("update warehouse", s, 200)

# ---- Sellers ----
print("========== SELLERS ==========")
s, r = call("POST", "/sellers", admin, {
    "company_name": "ABC Online Store", "contact_name": "Sarah Johnson",
    "email": "sarah@abconline.com", "phone": "555-123-4567", "portal_password": "seller123"})
record("create seller", s, 201)
seller = r["id"]
s, r = call("GET", "/sellers", admin)
record("list sellers", s, 200)
s, r = call("GET", f"/sellers/{seller}", admin)
record("get seller", s, 200)
s, r = call("POST", "/sellers", admin, {"company_name": "ABC Online Store", "contact_name": "Dup", "email": "x@x.com", "phone": "1"})
record("create dup seller", s, 400)

# ---- Seller login ----
print("========== SELLER AUTH ==========")
s, r = call("POST", "/auth/seller/login", body={"email": "sarah@abconline.com", "password": "seller123"})
record("seller login", s, 200)
seller_tok = r["access_token"]
s, r = call("POST", "/auth/seller/login", body={"email": "sarah@abconline.com", "password": "bad"})
record("seller login wrong pw", s, 401)

# ---- Users ----
print("========== USERS ==========")
s, r = call("POST", "/users", admin, {"full_name": "Sam Staff", "email": "sam@whitfield.com", "password": "staff123", "role": "staff", "warehouse_id": reno})
record("create staff user", s, 201)
staff = r["id"]
s, r = call("POST", "/users", admin, {"full_name": "Maria", "email": "maria@whitfield.com", "password": "m123456", "role": "staff", "warehouse_id": reno})
record("create second staff", s, 201)
s, r = call("GET", "/users", admin)
record("list users", s, 200)
s, r = call("PATCH", f"/users/{staff}", admin, {"full_name": "Sam Smith"})
record("update user", s, 200)
s, r = call("POST", "/users", admin, {"full_name": "Dup", "email": "sam@whitfield.com", "password": "x123456", "role": "staff", "warehouse_id": reno})
record("create dup user", s, 400)
s, r = call("DELETE", f"/users/{staff}", admin)
record("delete user", s, 200)

# ---- Products ----
print("========== PRODUCTS ==========")
s, r = call("POST", "/products", admin, {"seller_id": seller, "upc_barcode": "012345678905", "sku": "WGT-A-001", "product_name": "Widget A", "low_stock_threshold": 20})
record("create product", s, 201)
pid = r["id"]
s, r = call("GET", "/products", admin)
record("list products", s, 200)
s, r = call("GET", f"/products/upc/012345678905", admin)
record("get product by upc", s, 200)
s, r = call("GET", f"/products/{pid}", admin)
record("get product by id", s, 200)
s, r = call("PATCH", f"/products/{pid}", admin, {"low_stock_threshold": 15})
record("update product", s, 200)
s, r = call("POST", "/products", admin, {"seller_id": seller, "upc_barcode": "012345678905", "sku": "X", "product_name": "Dup"})
record("create dup product", s, 400)

# ---- Bin locations ----
print("========== BIN LOCATIONS ==========")
s, r = call("POST", "/bin-locations", admin, {"warehouse_id": reno, "bin_code": "A-03-2-B", "aisle": "A", "row": "03", "shelf": "2", "bin": "B", "product_id": pid})
record("create bin", s, 201)
binid = r["id"]
s, r = call("GET", "/bin-locations", admin, None)
record("list bins", s, 200)
s, r = call("GET", f"/bin-locations/product/{pid}?warehouse_id={reno}", admin)
record("find bin for product", s, 200)
s, r = call("PATCH", f"/bin-locations/{binid}", admin, {"max_capacity": 120})
record("update bin", s, 200)

# ---- Inventory (before receive) ----
print("========== INVENTORY ==========")
s, r = call("GET", "/inventory", admin)
record("list inventory", s, 200)

# ---- Shipments (duplicate prevention) ----
print("========== SHIPMENTS ==========")
s, r = call("POST", "/shipments/draft", admin, {"shipment_ref": "1Z999AA10123456784", "seller_id": seller, "warehouse_id": reno, "carrier": "UPS", "items": [{"product_id": pid, "quantity_expected": 48}]})
record("create shipment draft", s, 201)
shipid = r["id"]
s, r = call("POST", "/shipments/draft", admin, {"shipment_ref": "1Z999AA10123456784", "seller_id": seller, "warehouse_id": reno})
record("duplicate draft blocked", s, 400)
s, r = call("GET", "/shipments", admin)
record("list shipments", s, 200)
s, r = call("GET", f"/shipments/{shipid}", admin)
record("get shipment", s, 200)
s, r = call("POST", "/shipments/confirm", admin, {"shipment_ref": "1Z999AA10123456784", "received_by": reno, "items": [{"product_id": pid, "quantity_received": 48, "quantity_damaged": 0}]})
record("confirm shipment receipt", s, 200)
s, r = call("POST", "/shipments/confirm", admin, {"shipment_ref": "1Z999AA10123456784", "received_by": reno, "items": []})
record("re-confirm already received", s, 400)

# ---- Inventory (after receive) ----
s, r = call("GET", f"/inventory/stock/012345678905?warehouse_id={reno}", admin)
record("stock after receive", s, 200)
print("     stock:", r["quantity_available"], "available")

# ---- Orders (concurrent reservation) ----
print("========== ORDERS ==========")
s, r = call("POST", "/orders", admin, {"order_ref": "ORD-5521", "seller_id": seller, "warehouse_id": reno, "customer": {"name": "John", "address": "456 Main"}, "items": [{"product_id": pid, "quantity": 10}]})
record("create order (reserve 10)", s, 201)
oid = r["id"]
s, r = call("POST", "/orders", admin, {"order_ref": "ORD-5522", "seller_id": seller, "warehouse_id": reno, "customer": {"name": "J", "address": "1"}, "items": [{"product_id": pid, "quantity": 100}]})
record("order insufficient stock", s, 409)
s, r = call("GET", "/orders", admin)
record("list orders", s, 200)
s, r = call("GET", f"/orders/{oid}", admin)
record("get order", s, 200)
# status workflow
for st in ["picking", "packed", "labeled"]:
    s, r = call("PATCH", f"/orders/{oid}/status", admin, {"status": st, "shipping": {"carrier": "UPS", "tracking_number": "1Z888", "weight_lbs": 1.2, "ship_cost": 8.40}})
    record(f"order -> {st}", s, 200)
s, r = call("PATCH", f"/orders/{oid}/status", admin, {"status": "shipped"})
record("order -> shipped (consumes stock)", s, 200)
# stock after ship: 48 - 10 = 38 available
s, r = call("GET", f"/inventory/stock/012345678905?warehouse_id={reno}", admin)
record("stock after ship", s, 200)
print("     stock:", r["quantity_available"], "available,", r["quantity_reserved"], "reserved")

# ---- Returns ----
print("========== RETURNS ==========")
s, r = call("POST", "/returns", admin, {"original_order_id": oid, "return_reason": "wrong size", "items": [{"product_id": pid, "product_name": "Widget A", "quantity": 2, "condition": "resellable"}]})
record("process return (restock 2)", s, 201)
s, r = call("GET", "/returns", admin)
record("list returns", s, 200)

# ---- Damage records ----
print("========== DAMAGE RECORDS ==========")
s, r = call("POST", "/damage-records", admin, {"shipment_ref": "1Z999AA10123456784", "product_id": pid, "warehouse_id": reno, "quantity_damaged": 3, "damage_grade": "B", "carrier": "UPS"})
record("create damage record", s, 201)
did = r["id"]
s, r = call("GET", "/damage-records", admin)
record("list damage records", s, 200)
s, r = call("GET", f"/damage-records/{did}", admin)
record("get damage record", s, 200)

# ---- Audit logs ----
print("========== AUDIT LOGS ==========")
s, r = call("GET", "/audit-logs?limit=10", admin)
record("list audit logs", s, 200)
if r:
    rid = r[0].get("record_id")
    coll = r[0].get("collection_name")
    s, r = call("GET", f"/audit-logs/history?record_id={rid}&collection_name={coll}", admin)
    record("audit history", s, 200)
s, r = call("GET", "/audit-logs?record_id=badid", admin)
record("audit invalid record_id", s, 400)

# ---- Invoices ----
print("========== INVOICES ==========")
s, r = call("POST", "/invoices/generate?year=2026&month=8", admin)
record("generate invoices", s, 200)
s, r = call("GET", "/invoices", admin)
record("list invoices", s, 200)
if r:
    invid = r[0]["id"]
    s, r = call("GET", f"/invoices/{invid}", admin)
    record("get invoice", s, 200)

# ---- Dashboard ----
print("========== DASHBOARD ==========")
s, r = call("GET", "/dashboard/overview", admin)
record("dashboard overview", s, 200)

# ---- RBAC checks (staff + seller blocked) ----
print("========== RBAC ==========")
s, r = call("POST", "/auth/login", body={"email": "maria@whitfield.com", "password": "m123456"})
record("staff login", s, 200)
staff_tok = r["access_token"]
s, r = call("GET", "/users", staff_tok)
record("staff blocked from users", s, 403)
s, r = call("GET", "/audit-logs", staff_tok)
record("staff blocked from audit", s, 403)
s, r = call("GET", "/invoices", staff_tok)
record("staff blocked from invoices", s, 403)
s, r = call("GET", "/inventory", staff_tok)
record("staff can read inventory", s, 200)
s, r = call("GET", "/users", seller_tok)
record("seller blocked from users", s, 403)
s, r = call("GET", "/products", seller_tok)
record("seller blocked from products", s, 403)

# ---- Operational endpoints ----
print("========== OPERATIONAL ==========")
import urllib.request as ur
for path in ["/", "/health", "/ready"]:
    try:
        with ur.urlopen("http://localhost:8000" + path) as resp:
            print(f"[PASS] GET {path} -> {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"[FAIL] GET {path} -> {e.code}")

print("\n========== SUMMARY ==========")
passed = sum(1 for m, _, _ in results if m == "PASS")
failed = sum(1 for m, _, _ in results if m == "FAIL")
print(f"TOTAL: {len(results)}  PASS: {passed}  FAIL: {failed}")
for m, name, st in results:
    if m == "FAIL":
        print(f"  FAILED: {name} (status {st})")
sys.exit(1 if failed else 0)

import { useEffect, useState } from "react";
import { getUsers, createUser, updateUser, deleteUser, getWarehouses, changePassword } from "../api/endpoints";
import type { Warehouse } from "../api/types";
import { Table, Spinner } from "../components/ui";
import { Modal } from "../components/Modal";
import { useToast } from "../lib/toast";

interface UserRow { id: string; full_name: string; email: string; role: string; warehouse_id: string; is_active: boolean; last_login: string | null }

export default function Users() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<UserRow | null>(null);
  const [showPw, setShowPw] = useState(false);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [u, w] = await Promise.all([getUsers(), getWarehouses()]);
      setUsers(u); setWarehouses(w);
    } catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const whName = (id: string) => warehouses.find((w) => w.id === id)?.name ?? id.slice(0, 6);

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Users</h1><p className="page-sub">Staff accounts (admin only)</p></div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ Add User</button>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <Table headers={["Name", "Email", "Role", "Warehouse", "Status", "Last login", ""]}>
            {users.map((u) => (
              <tr key={u.id}>
                <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                <td>{u.email}</td>
                <td><span className="chip chip-neutral">{u.role}</span></td>
                <td>{whName(u.warehouse_id)}</td>
                <td>{u.is_active ? <span className="chip chip-success">Active</span> : <span className="chip chip-neutral">Inactive</span>}</td>
                <td>{u.last_login ? new Date(u.last_login).toLocaleDateString() : "—"}</td>
                <td>
                  <div className="flex gap">
                    <button className="btn btn-sm btn-secondary" onClick={() => setEditing(u)}>Edit</button>
                    <button className="btn btn-sm btn-danger" onClick={async () => {
                      if (confirm(`Delete ${u.full_name}?`)) {
                        try { await deleteUser(u.id); toast("User deleted", "success"); load(); }
                        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
                      }
                    }}>Delete</button>
                  </div>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </div>
      {showAdd && <AddUser warehouses={warehouses} onClose={() => setShowAdd(false)} onSaved={async (d) => {
        try { await createUser(d); toast("User created", "success"); setShowAdd(false); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
      {editing && <EditUser warehouses={warehouses} user={editing} onClose={() => setEditing(null)} onSaved={async (d) => {
        try { await updateUser(editing.id, d); toast("User updated", "success"); setEditing(null); load(); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
      <button className="btn btn-secondary" onClick={() => setShowPw(true)} style={{ marginTop: 16 }}>Change my password</button>
      {showPw && <ChangePw onClose={() => setShowPw(false)} onSaved={async (d) => {
        try { await changePassword(d.old_password, d.new_password); toast("Password changed", "success"); setShowPw(false); }
        catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
      }} />}
    </div>
  );
}

function EditUser({ warehouses, user, onClose, onSaved }: { warehouses: Warehouse[]; user: UserRow; onClose: () => void; onSaved: (d: any) => void }) {
  const [f, setF] = useState<any>({ full_name: user.full_name, role: user.role, warehouse_id: user.warehouse_id, is_active: user.is_active });
  const set = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  return (
    <Modal title={`Edit ${user.full_name}`} onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={() => onSaved(f)}>Save</button>
    </>}>
      <div className="form-group"><label>Full name</label><input className="input" value={f.full_name} onChange={(e) => set("full_name", e.target.value)} /></div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Role</label>
          <select className="select" value={f.role} onChange={(e) => set("role", e.target.value)}>
            <option value="admin">admin</option><option value="manager">manager</option><option value="staff">staff</option>
          </select></div>
        <div className="form-group"><label>Warehouse</label>
          <select className="select" value={f.warehouse_id} onChange={(e) => set("warehouse_id", e.target.value)}>
            <option value="">Select</option>{warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
          </select></div>
      </div>
      <div className="form-group"><label>Active</label>
        <select className="select" value={String(f.is_active)} onChange={(e) => set("is_active", e.target.value === "true")}>
          <option value="true">Active</option><option value="false">Inactive</option>
        </select></div>
    </Modal>
  );
}

function ChangePw({ onClose, onSaved }: { onClose: () => void; onSaved: (d: any) => void }) {
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  return (
    <Modal title="Change My Password" onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={() => onSaved({ old_password: oldPw, new_password: newPw })}>Change</button>
    </>}>
      <div className="form-group"><label>Old password</label><input className="input" type="password" value={oldPw} onChange={(e) => setOldPw(e.target.value)} /></div>
      <div className="form-group"><label>New password (min 6)</label><input className="input" type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} /></div>
    </Modal>
  );
}

function AddUser({ warehouses, onClose, onSaved }: { warehouses: Warehouse[]; onClose: () => void; onSaved: (d: any) => void }) {
  const [f, setF] = useState<any>({ full_name: "", email: "", password: "", role: "staff", warehouse_id: "", is_active: true });
  const set = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }));
  return (
    <Modal title="Add User" onClose={onClose} footer={<>
      <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary" onClick={() => onSaved(f)}>Create</button>
    </>}>
      <div className="form-group"><label>Full name *</label><input className="input" value={f.full_name} onChange={(e) => set("full_name", e.target.value)} /></div>
      <div className="form-group"><label>Email *</label><input className="input" type="email" value={f.email} onChange={(e) => set("email", e.target.value)} /></div>
      <div className="form-group"><label>Password * (min 6 chars)</label><input className="input" type="password" value={f.password} onChange={(e) => set("password", e.target.value)} /></div>
      <div className="grid grid-2 gap">
        <div className="form-group"><label>Role *</label>
          <select className="select" value={f.role} onChange={(e) => set("role", e.target.value)}>
            <option value="admin">admin</option><option value="manager">manager</option><option value="staff">staff</option>
          </select></div>
        <div className="form-group"><label>Warehouse *</label>
          <select className="select" value={f.warehouse_id} onChange={(e) => set("warehouse_id", e.target.value)}>
            <option value="">Select</option>{warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
          </select></div>
      </div>
      <div className="form-group"><label>Active</label>
        <select className="select" value={String(f.is_active)} onChange={(e) => set("is_active", e.target.value === "true")}>
          <option value="true">Active</option><option value="false">Inactive</option>
        </select></div>
    </Modal>
  );
}

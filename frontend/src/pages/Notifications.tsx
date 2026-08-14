import { useEffect, useState } from "react";
import { getNotifications, markNotificationRead } from "../api/endpoints";
import type { Notification } from "../api/types";
import { Spinner } from "../components/ui";
import { useToast } from "../lib/toast";
import { formatDate } from "../lib/status";

export default function Notifications() {
  const [notifs, setNotifs] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();
  const load = async () => {
    setLoading(true);
    try { setNotifs(await getNotifications()); }
    catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const markRead = async (n: Notification) => {
    if (n.is_read) return;
    try { await markNotificationRead(n.id); load(); }
    catch { /* ignore */ }
  };

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Notifications</h1><p className="page-sub">Alerts and system messages</p></div>
      </div>
      <div className="card" style={{ padding: 12 }}>
        {loading ? <Spinner /> : (
          <div>
            {(notifs ?? []).map((n) => (
              <div key={n.id} onClick={() => markRead(n)} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: 12, borderBottom: "1px solid #E6E7E0", cursor: n.is_read ? "default" : "pointer",
                background: n.is_read ? "transparent" : "#F9FAF7",
              }}>
                <div>
                  <div style={{ fontWeight: 600 }}>
                    {n.subject}
                    {!n.is_read && <span className="badge-count">new</span>}
                  </div>
                  <div style={{ color: "#ABACA7", fontSize: 13 }}>{n.message}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span className="chip chip-neutral">{n.channel}</span>
                  <span style={{ color: "#ABACA7", fontSize: 12, whiteSpace: "nowrap" }}>{formatDate(n.created_at as any)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { getAuditLogs } from "../api/endpoints";
import type { AuditLog } from "../api/types";
import { Table, Spinner } from "../components/ui";
import { useToast } from "../lib/toast";
import { formatDate } from "../lib/status";

export default function Audit() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const toast = useToast();
  useEffect(() => {
    getAuditLogs(50).then(setLogs).catch((e) => toast(e.response?.data?.detail || "Failed", "error")).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Audit Logs</h1><p className="page-sub">Immutable trail of every action (read-only)</p></div>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <Table headers={["When", "User", "Action", "Collection", "Method", ""]}>
            {logs.map((l) => (
              <>
                <tr key={l.id} style={{ cursor: "pointer" }} onClick={() => setExpanded(expanded === l.id ? null : l.id)}>
                  <td>{formatDate(l.created_at)}</td>
                  <td style={{ fontWeight: 600 }}>{l.user_name}</td>
                  <td>{l.action}</td>
                  <td><span className="chip chip-neutral">{l.collection_name}</span></td>
                  <td>{l.method}</td>
                  <td>{expanded === l.id ? "▲" : "▼"}</td>
                </tr>
                {expanded === l.id && (
                  <tr key={l.id + "-detail"}><td colSpan={6} style={{ background: "#F9FAF7" }}>
                    <div style={{ fontFamily: "monospace", fontSize: 12, whiteSpace: "pre-wrap" }}>
                      <strong>Old:</strong> {JSON.stringify(l.old_value, null, 2)}
                      {"\n\n"}<strong>New:</strong> {JSON.stringify(l.new_value, null, 2)}
                    </div>
                  </td></tr>
                )}
              </>
            ))}
          </Table>
        )}
      </div>
    </div>
  );
}

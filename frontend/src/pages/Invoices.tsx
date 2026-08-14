import { useEffect, useState } from "react";
import { getInvoices, generateInvoices } from "../api/endpoints";
import type { Invoice } from "../api/types";
import { Table, Spinner } from "../components/ui";
import { useToast } from "../lib/toast";
import { formatCurrency, statusChip } from "../lib/status";

export default function Invoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();
  const load = async () => {
    setLoading(true);
    try { setInvoices(await getInvoices()); }
    catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Invoices</h1><p className="page-sub">Monthly seller invoices</p></div>
        <button className="btn btn-primary" onClick={async () => {
          try { await generateInvoices(new Date().getFullYear(), new Date().getMonth() + 1); toast("Invoices generated", "success"); load(); }
          catch (e: any) { toast(e.response?.data?.detail || "Failed", "error"); }
        }}>Generate Invoices</button>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <Table headers={["Ref", "Seller", "Period", "Subtotal", "Tax", "Total", "Status"]}>
            {invoices.map((i) => (
              <tr key={i.id}>
                <td style={{ fontWeight: 600 }}>{i.invoice_ref}</td>
                <td>{i.seller_name}</td>
                <td>{i.period.month}/{i.period.year}</td>
                <td>{formatCurrency(i.subtotal)}</td>
                <td>{formatCurrency(i.tax)}</td>
                <td style={{ fontWeight: 700 }}>{formatCurrency(i.total)}</td>
                <td><span className={`chip ${statusChip(i.status)}`}>{i.status}</span></td>
              </tr>
            ))}
          </Table>
        )}
      </div>
    </div>
  );
}

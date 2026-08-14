import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login, sellerLogin } from "../api/endpoints";
import { useAuth } from "../lib/auth";
import { useToast } from "../lib/toast";

export default function Login({ isSeller = false }: { isSeller?: boolean }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login: setAuth } = useAuth();
  const toast = useToast();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = isSeller ? await sellerLogin(email, password) : await login(email, password);
      setAuth(user);
      toast("Logged in successfully", "success");
      navigate(isSeller ? "/seller" : "/");
    } catch (err: any) {
      toast(err.response?.data?.detail || "Login failed", "error");
    } finally {
      setLoading(false);
    }
  };

  const shellStyle: React.CSSProperties = {
    minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
    background: "linear-gradient(135deg, #1C3D4F, #173445)",
  };
  const cardStyle: React.CSSProperties = {
    background: "#fff", padding: 40, borderRadius: 24, width: 380,
    boxShadow: "0 10px 40px rgba(0,0,0,0.3)",
  };

  return (
    <div style={shellStyle}>
      <form onSubmit={submit} style={cardStyle}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <span style={{ width: 34, height: 34, borderRadius: "50%", display: "inline-block", background: "conic-gradient(#F2C14E 0 50%, #1C3D4F 50% 100%)" }} />
          <h1 style={{ margin: 0, color: "#1C3D4F", fontSize: 22, fontFamily: "Poppins" }}>
            {isSeller ? "Seller Portal" : "IronNest WMS"}
          </h1>
        </div>
        <p style={{ color: "#8A93A0", margin: "0 0 24px" }}>
          {isSeller ? "Sign in to your seller account" : "Warehouse Management System"}
        </p>
        <div className="form-group">
          <label>Email</label>
          <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
        <div style={{ marginTop: 16, textAlign: "center", fontSize: 13 }}>
          {isSeller ? (
            <Link to="/login" style={{ color: "#1B475D" }}>Staff login</Link>
          ) : (
            <Link to="/seller-login" style={{ color: "#1B475D" }}>Seller login</Link>
          )}
        </div>
      </form>
    </div>
  );
}

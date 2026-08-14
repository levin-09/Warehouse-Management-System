import { useState, useRef, useEffect } from "react";
import { chat } from "../api/endpoints";
import { useToast } from "../lib/toast";

interface Msg { role: "user" | "bot"; text: string }

export default function Chat() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const toast = useToast();
  const sessionId = useRef("default");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView(); }, [messages, typing]);

  const send = async () => {
    const text = input.trim();
    if (!text) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setTyping(true);
    try {
      const res = await chat(text, sessionId.current);
      setMessages((m) => [...m, { role: "bot", text: res.response }]);
    } catch (e: any) {
      const detail = e.response?.data?.detail;
      setMessages((m) => [...m, {
        role: "bot",
        text: typeof detail === "string" && detail.includes("GROQ")
          ? "The AI assistant isn't configured yet (no GROQ_API_KEY). Tools work, but the assistant can't answer. Ask a staff/admin to add the key."
          : (detail || "Sorry, something went wrong."),
      }]);
      toast("Chat error", "error");
    } finally {
      setTyping(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div><h1 className="page-title">Assistant</h1><p className="page-sub">Ask the WMS AI about inventory, orders, shipments and more</p></div>
      </div>
      <div className="card chat-box">
        <div className="chat-messages">
          <div className="chat-bubble bot">Hello! I'm the Whitfield WMS assistant. Ask me about stock levels, pending orders, bin locations, shipments, sellers and more.</div>
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble ${m.role}`}>{m.text}</div>
          ))}
          {typing && <div className="chat-bubble bot typing">Checking warehouse data…</div>}
          <div ref={endRef} />
        </div>
        <div className="chat-input-row">
          <input
            className="input"
            placeholder="e.g. How many products are in the inventory?"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
          />
          <button className="btn btn-primary" onClick={send} disabled={typing}>Send</button>
        </div>
      </div>
    </div>
  );
}

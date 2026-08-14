import { useState } from "react";
import { PipecatClient, type PipecatClientOptions } from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";
import { PipecatClientProvider, usePipecatClient, usePipecatClientTransportState, PipecatClientAudio } from "@pipecat-ai/client-react";
import { Mic, Phone, PhoneOff } from "lucide-react";
import { useToast } from "../lib/toast";

// Base URL for the Pipecat signaling server. Vite proxies /api to :7860 so the
// browser stays same-origin (required for getUserMedia). Point VITE_PIPECAT_WEBRTC_URL
// at a deployed voice server if you run it remotely.
function createWmsVoiceClient(): PipecatClient {
  const options: PipecatClientOptions = {
    transport: new SmallWebRTCTransport(),
  };
  return new PipecatClient(options);
}

interface Turn { role: string; text: string }

/**
 * Whitfield WMS Voice Assistant.
 * Talks to the Pipecat bot (voice_ai/server/bot.py) which can answer questions
 * about stock/orders and execute warehouse actions by voice.
 */
export default function Voice() {
  const client = createWmsVoiceClient();
  return (
    <PipecatClientProvider client={client}>
      <PipecatClientAudio />
      <VoiceAssistant />
    </PipecatClientProvider>
  );
}

function VoiceAssistant() {
  const client = usePipecatClient();
  const transportState = usePipecatClientTransportState();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const isLive = transportState === "connected";
  const connecting = transportState === "connecting" || transportState === "initializing";

  const handleStart = async () => {
    if (!client) return;
    setBusy(true);
    try {
      setTurns((t) => [...t, { role: "bot", text: "Connecting to the voice assistant…" }]);
      await client.connect();
      setTurns((t) => [...t, {
        role: "bot",
        text: "Connected. You can talk now. Try: \"How many Widget A do we have?\" or \"Received 24 units of UPC 012345678905\".",
      }]);
    } catch (e: any) {
      toast(e?.message || "Could not connect to the voice bot. Is the Pipecat server running on :7860?", "error");
      setTurns((t) => [...t, {
        role: "bot",
        text: "⚠️ Could not connect. Make sure the voice server is running (python bot.py on :7860) and the backend is up.",
      }]);
    } finally {
      setBusy(false);
    }
  };

  const handleStop = async () => {
    if (!client) return;
    await client.disconnect();
    setTurns((t) => [...t, { role: "bot", text: "Call ended." }]);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Voice Assistant</h1>
          <p className="page-sub">Talk to the WMS — check stock, find items, record receipts by voice</p>
        </div>
        <span className="chip" style={{
          background: isLive ? "var(--mint)" : connecting ? "var(--amber)" : "var(--border)",
        }}>
          {isLive ? "● Live" : connecting ? "Connecting…" : "Offline"}
        </span>
      </div>

      <div className="card" style={{ padding: 24 }}>
        {/* Orb */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "12px 0 20px" }}>
          <div
            style={{
              width: 140, height: 140, borderRadius: "50%",
              background: "radial-gradient(circle at 30% 30%, #1B475D, #0f2e3d)",
              boxShadow: isLive ? "0 0 60px rgba(27,71,93,0.9)" : "0 0 30px rgba(27,71,93,0.4)",
              transform: isLive ? "scale(1.08)" : "scale(1)",
              transition: "transform 0.15s ease, box-shadow 0.2s ease",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}
          >
            <Mic size={48} color="#EAF0F3" />
          </div>
          <div style={{ marginTop: 12, color: "var(--muted)" }}>
            {isLive ? "Listening…" : connecting ? "Connecting…" : "Ready"}
          </div>
        </div>

        {/* Controls */}
        <div style={{ display: "flex", gap: 12, justifyContent: "center", marginBottom: 20 }}>
          {!isLive ? (
            <button className="btn btn-primary" onClick={handleStart} disabled={connecting || busy} style={{ padding: "12px 28px" }}>
              <Phone size={18} /> Start call
            </button>
          ) : (
            <button className="btn btn-danger" onClick={handleStop} style={{ padding: "12px 28px" }}>
              <PhoneOff size={18} /> End call
            </button>
          )}
        </div>

        {/* Transcript */}
        <div style={{ background: "var(--canvas)", borderRadius: 12, padding: 16, minHeight: 220 }}>
          {turns.length === 0 ? (
            <div style={{ textAlign: "center", color: "var(--muted)", paddingTop: 60 }}>
              <Mic size={40} style={{ opacity: 0.3 }} />
              <p>Click "Start call" and allow microphone access to begin.</p>
            </div>
          ) : (
            turns.map((t, i) => (
              <p key={i} style={{ margin: "6px 0", color: t.role === "user" ? "var(--text)" : "#1B475D" }}>
                <strong>{t.role === "user" ? "You" : "Assistant"}:</strong> {t.text}
              </p>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

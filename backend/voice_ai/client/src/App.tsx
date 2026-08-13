import { useState } from "react";
import { VoiceProvider, useVoice } from "@pipecat-ai/voice-sdk-react";
import { createWmsVoiceClient } from "./client";

/**
 * Whitfield WMS voice assistant UI.
 * Talks to the WMS Pipecat bot (server/bot.py) which can answer questions and
 * execute warehouse actions.
 */
export default function App() {
  return (
    <VoiceProvider client={createWmsVoiceClient()}>
      <Assistant />
    </VoiceProvider>
  );
}

function Assistant() {
  const { start, stop, isStarting, isSpeaking } = useVoice();
  const [transcript, setTranscript] = useState<{ role: string; text: string }[]>([]);

  const handleStart = async () => {
    setTranscript((t) => [...t, { role: "bot", text: "Connecting to the WMS assistant…" }]);
    await start();
  };

  return (
    <div className="app">
      <header>
        <h1>Whitfield WMS Voice Assistant</h1>
        <p>Speak to check stock, find items, and record warehouse activity.</p>
      </header>

      <main>
        <div className={`orb ${isSpeaking ? "speaking" : ""}`} aria-hidden />

        <div className="controls">
          <button onClick={handleStart} disabled={isStarting}>
            Start call
          </button>
          <button onClick={stop}>End call</button>
        </div>

        <section className="transcript" aria-live="polite">
          {transcript.map((m, i) => (
            <p key={i} className={m.role}>
              <strong>{m.role}:</strong> {m.text}
            </p>
          ))}
        </section>
      </main>
    </div>
  );
}

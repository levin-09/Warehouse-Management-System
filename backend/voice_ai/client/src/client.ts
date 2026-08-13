import { PipecatClient, SmallWebRTCTransport, type PipecatClientOptions } from "@pipecat-ai/client-js";

// Base URL for the Pipecat signaling server. Vite proxies /api to :7860.
const baseUrl = import.meta.env.VITE_PIPECAT_WEBRTC_URL ?? window.location.origin;

// Realtime voice assistant over WebRTC to the WMS Pipecat bot.
export function createWmsVoiceClient(): PipecatClient {
  const transport = new SmallWebRTCTransport({ apiKey: undefined });
  const options: PipecatClientOptions = { baseUrl };
  return new PipecatClient({ transport, options });
}

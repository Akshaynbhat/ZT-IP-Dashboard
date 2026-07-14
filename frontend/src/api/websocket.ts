import { getToken } from "../auth/keycloak";

class ZTWebSocketManager {
  private socket: WebSocket | null = null;
  private reconnectTimeout: any = null;
  private reconnectAttempts = 0;
  private maxReconnectDelay = 30000;
  private isIntentionalDisconnect = false;

  public connect() {
    this.isIntentionalDisconnect = false;
    const token = getToken();
    if (!token) {
      console.warn("WebSocket cannot connect: No Keycloak token available.");
      return;
    }

    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    // Determine WS protocol based on current web location
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws?token=${encodeURIComponent(token)}`;

    console.log(`Connecting WebSocket to: ${protocol}//${host}/api/v1/ws`);
    
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log("WebSocket secure connection established.");
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event) => {
      try {
        if (event.data === "pong") return;
        const payload = JSON.parse(event.data);
        this.handleMessage(payload);
      } catch (err) {
        console.error("Error parsing WebSocket message payload:", err);
      }
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket connection error:", error);
    };

    this.socket.onclose = (event) => {
      console.warn(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
      this.socket = null;
      if (!this.isIntentionalDisconnect) {
        this.scheduleReconnect();
      }
    };
  }

  public disconnect() {
    this.isIntentionalDisconnect = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    console.log("WebSocket disconnected intentionally.");
  }

  private scheduleReconnect() {
    if (this.reconnectTimeout) return;

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), this.maxReconnectDelay);
    console.log(`Scheduling WebSocket reconnect in ${delay}ms (Attempt #${this.reconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect();
    }, delay);
  }

  private handleMessage(payload: { type: string; user_id: string; data: any }) {
    const { type, user_id, data } = payload;
    console.log(`Real-time update received: type=${type}, user_id=${user_id}`);

    if (type === "score") {
      const event = new CustomEvent("zt-score-update", { detail: data });
      window.dispatchEvent(event);
    } else if (type === "alert") {
      const event = new CustomEvent("zt-alert-update", { detail: data });
      window.dispatchEvent(event);
    }
  }
}

export const wsManager = new ZTWebSocketManager();
export default wsManager;

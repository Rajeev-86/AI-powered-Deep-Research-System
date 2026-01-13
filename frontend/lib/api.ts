/**
 * API Client for Research System Backend
 * Handles REST and WebSocket communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatRequest {
  message: string;
  thread_id?: string;
  deep_research?: boolean;
}

export interface ChatResponse {
  response: string;
  intent: string;
  timestamp: string;
  plan?: any;  // Optional plan data when intent is "plan_review"
}

export interface ResearchRequest {
  query: string;
  enable_cache?: boolean;
  enable_streaming?: boolean;
}

export interface ResearchResponse {
  report: string;
  query: string;
  timestamp: string;
  metrics: {
    total_api_calls: number;
    total_tokens: number;
    total_cost: number;
  };
}

/**
 * Send a chat message to the backend
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Execute deep research (REST endpoint)
 */
export async function executeResearch(request: ResearchRequest): Promise<ResearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/research`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Research API Error: ${response.statusText}`);
  }

  return response.json();
}

/**
 * WebSocket client for streaming chat
 */
export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private threadId: string;

  constructor(threadId: string) {
    this.threadId = threadId;
  }

  connect(
    onMessage: (data: any) => void,
    onError?: (error: Event) => void,
    onClose?: () => void
  ) {
    const wsUrl = API_BASE_URL.replace('http', 'ws');
    this.ws = new WebSocket(`${wsUrl}/ws/chat/${this.threadId}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      if (onClose) onClose();
    };
  }

  send(message: string, deepResearch: boolean = false) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        message,
        deep_research: deepResearch
      }));
    } else {
      throw new Error('WebSocket is not connected');
    }
  }

  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

/**
 * WebSocket client for streaming research
 */
export class ResearchWebSocket {
  private ws: WebSocket | null = null;

  connect(
    onMessage: (data: any) => void,
    onError?: (error: Event) => void,
    onClose?: () => void
  ) {
    const wsUrl = API_BASE_URL.replace('http', 'ws');
    this.ws = new WebSocket(`${wsUrl}/ws/research`);

    this.ws.onopen = () => {
      console.log('Research WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('Research WebSocket error:', error);
      if (onError) onError(error);
    };

    this.ws.onclose = () => {
      console.log('Research WebSocket closed');
      if (onClose) onClose();
    };
  }

  startResearch(query: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ query }));
    } else {
      throw new Error('WebSocket is not connected');
    }
  }

  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

/**
 * Health check endpoint
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/`);
    return response.ok;
  } catch {
    return false;
  }
}

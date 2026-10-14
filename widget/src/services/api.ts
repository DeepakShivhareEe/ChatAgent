/**
 * API client for the AI Website Assistant backend.
 * Handles SSE streaming and direct API calls.
 */

import type { SSEEvent } from '../types';

export class APIClient {
  private baseUrl: string;
  private siteKey?: string;

  constructor(baseUrl: string, siteKey?: string) {
    // Remove trailing slash
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.siteKey = siteKey;
  }

  /**
   * Send a chat message and receive streaming SSE response.
   * Calls the callback for each event received.
   */
  async sendMessage(
    query: string,
    conversationId: string | null,
    onEvent: (event: SSEEvent) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.siteKey ? { 'X-Site-Key': this.siteKey } : {}),
      },
      body: JSON.stringify({
        query,
        conversation_id: conversationId,
      }),
      signal,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      // Keep the last potentially incomplete line in the buffer
      buffer = lines.pop() || '';

      let currentEventType = '';
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEventType = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const event: SSEEvent = JSON.parse(data);
            if (!event.type && currentEventType) {
              event.type = currentEventType as SSEEvent['type'];
            }
            onEvent(event);
          } catch {
            // Ignore non-JSON lines
          }
        }
      }
    }
  }

  /**
   * Search the knowledge base directly.
   */
  async search(query: string, topK: number = 5) {
    const response = await fetch(`${this.baseUrl}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK }),
    });

    if (!response.ok) {
      throw new Error(`Search failed: HTTP ${response.status}`);
    }

    return response.json();
  }

  /**
   * Check backend health.
   */
  async health() {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }
}

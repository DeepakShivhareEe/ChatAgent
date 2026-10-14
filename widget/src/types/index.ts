/**
 * TypeScript types for the AI Website Assistant chat widget.
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
  isStreaming?: boolean;
}

export interface ChatWidgetProps {
  /** Backend API URL (e.g., "http://localhost:8000") */
  apiUrl: string;
  /** Widget title */
  title?: string;
  /** Widget subtitle */
  subtitle?: string;
  /** Initial theme */
  theme?: 'light' | 'dark';
  /** Suggested prompt chips */
  suggestedPrompts?: string[];
  /** Position of the floating button */
  position?: 'bottom-right' | 'bottom-left';
  /** Accent color (CSS color value) */
  accentColor?: string;
}

export interface SSEEvent {
  type: 'meta' | 'content' | 'sources' | 'done' | 'error';
  content?: string;
  conversation_id?: string;
  sources?: string[];
  message?: string;
}

export interface ChatState {
  messages: Message[];
  isOpen: boolean;
  isLoading: boolean;
  isStreaming: boolean;
  conversationId: string | null;
  error: string | null;
}

export type Theme = 'light' | 'dark';

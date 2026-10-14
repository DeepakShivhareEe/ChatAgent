/**
 * Core chat state management hook.
 * Handles messages, SSE streaming, and conversation lifecycle.
 */

import { useState, useCallback, useRef } from 'react';
import type { Message, SSEEvent } from '../types';
import { APIClient } from '../services/api';

function generateId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function useChat(apiUrl: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apiClient = useRef(new APIClient(apiUrl));
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (query: string) => {
      if (!query.trim() || isLoading) return;

      setError(null);
      setIsLoading(true);

      // Add user message
      const userMessage: Message = {
        id: generateId(),
        role: 'user',
        content: query.trim(),
        timestamp: new Date(),
      };

      // Create assistant placeholder
      const assistantMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);

      // Start streaming
      setIsStreaming(true);
      abortControllerRef.current = new AbortController();

      try {
        let sources: string[] = [];

        await apiClient.current.sendMessage(
          query.trim(),
          conversationId,
          (event: SSEEvent) => {
            switch (event.type) {
              case 'meta':
                if (event.conversation_id) {
                  setConversationId(event.conversation_id);
                }
                break;

              case 'content':
                if (event.content) {
                  setMessages((prev) => {
                    const updated = [...prev];
                    const last = updated[updated.length - 1];
                    if (last && last.role === 'assistant') {
                      updated[updated.length - 1] = {
                        ...last,
                        content: last.content + event.content,
                      };
                    }
                    return updated;
                  });
                }
                break;

              case 'sources':
                if (event.sources) {
                  sources = event.sources;
                }
                break;

              case 'done':
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last && last.role === 'assistant') {
                    updated[updated.length - 1] = {
                      ...last,
                      isStreaming: false,
                      sources,
                    };
                  }
                  return updated;
                });
                break;

              case 'error':
                setError(event.message || 'An error occurred.');
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last && last.role === 'assistant') {
                    updated[updated.length - 1] = {
                      ...last,
                      content:
                        event.message ||
                        'Sorry, an error occurred. Please try again.',
                      isStreaming: false,
                    };
                  }
                  return updated;
                });
                break;
            }
          },
          abortControllerRef.current.signal
        );
      } catch (err: any) {
        if (err.name === 'AbortError') {
          // User pressed Stop. Keep any partial text, mark the message as
          // finished so the copy button appears, and drop the placeholder
          // if nothing had been received yet.
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === 'assistant') {
              if (last.content) {
                updated[updated.length - 1] = {
                  ...last,
                  isStreaming: false,
                };
              } else {
                updated.pop();
              }
            }
            return updated;
          });
        } else {
          const errorMsg =
            err.message || 'Failed to connect to the assistant.';
          setError(errorMsg);
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === 'assistant') {
              updated[updated.length - 1] = {
                ...last,
                content: `Sorry, I couldn't process your request. ${errorMsg}`,
                isStreaming: false,
              };
            }
            return updated;
          });
        }
      } finally {
        setIsLoading(false);
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [conversationId, isLoading]
  );

  const clearConversation = useCallback(() => {
    // Abort any ongoing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setMessages([]);
    setConversationId(null);
    setError(null);
    setIsLoading(false);
    setIsStreaming(false);
  }, []);

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    messages,
    isLoading,
    isStreaming,
    conversationId,
    error,
    sendMessage,
    clearConversation,
    stopStreaming,
  };
}

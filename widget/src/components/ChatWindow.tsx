/**
 * ChatWindow — the main chat panel with header, messages, and input.
 */

import { motion } from 'motion/react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { SuggestedPrompts } from './SuggestedPrompts';
import { ThemeToggle } from './ThemeToggle';
import type { Message, Theme } from '../types';

interface ChatWindowProps {
  title: string;
  subtitle?: string;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  theme: Theme;
  suggestedPrompts: string[];
  onSend: (message: string) => void;
  onClear: () => void;
  onClose: () => void;
  onStop: () => void;
  onToggleTheme: () => void;
  position: 'bottom-right' | 'bottom-left';
}

export function ChatWindow({
  title,
  subtitle,
  messages,
  isLoading,
  isStreaming,
  theme,
  suggestedPrompts,
  onSend,
  onClear,
  onClose,
  onStop,
  onToggleTheme,
  position,
}: ChatWindowProps) {
  return (
    <motion.div
      className={`chat-window ${position}`}
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.95 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-info">
          <div className="chat-header-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z" />
              <path d="M16 14H8a4 4 0 0 0-4 4v2h16v-2a4 4 0 0 0-4-4z" />
            </svg>
          </div>
          <div>
            <h3 className="chat-header-title">{title}</h3>
            {subtitle && <p className="chat-header-subtitle">{subtitle}</p>}
          </div>
        </div>

        <div className="chat-header-actions">
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />

          {messages.length > 0 && (
            <motion.button
              className="header-action-btn"
              onClick={onClear}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              title="Clear conversation"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </motion.button>
          )}

          <motion.button
            className="header-action-btn close-btn"
            onClick={onClose}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            title="Close chat"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </motion.button>
        </div>
      </div>

      {/* Messages */}
      <div className="chat-body">
        <MessageList messages={messages} isLoading={isLoading} />

        {/* Suggested prompts (only when no messages) */}
        {messages.length === 0 && suggestedPrompts.length > 0 && (
          <SuggestedPrompts prompts={suggestedPrompts} onSelect={onSend} />
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={onSend}
        isLoading={isLoading}
        isStreaming={isStreaming}
        onStop={onStop}
      />
    </motion.div>
  );
}

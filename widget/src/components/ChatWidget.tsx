/**
 * ChatWidget — the root component that combines the floating button and chat window.
 * This is the main public-facing export of the widget.
 */

import { useState, useCallback } from 'react';
import { AnimatePresence } from 'motion/react';
import { ChatButton } from './ChatButton';
import { ChatWindow } from './ChatWindow';
import { useChat } from '../hooks/useChat';
import { useTheme } from '../hooks/useTheme';
import type { ChatWidgetProps } from '../types';

const DEFAULT_PROMPTS = [
  'What features do you offer?',
  'How does pricing work?',
  'How do I get started?',
  'How can I contact support?',
];

export function ChatWidget({
  apiUrl,
  title = 'AI Assistant',
  subtitle = 'Ask me anything about the website',
  theme: initialTheme,
  suggestedPrompts = DEFAULT_PROMPTS,
  position = 'bottom-right',
  accentColor,
}: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { theme, toggleTheme } = useTheme(initialTheme);
  const {
    messages,
    isLoading,
    isStreaming,
    sendMessage,
    clearConversation,
    stopStreaming,
  } = useChat(apiUrl);

  const handleToggle = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  const handleClose = useCallback(() => {
    setIsOpen(false);
  }, []);

  return (
    <div
      className={`awa-widget ${theme}`}
      style={
        accentColor
          ? ({ '--awa-accent': accentColor, '--awa-accent-hover': accentColor } as React.CSSProperties)
          : undefined
      }
    >
      <AnimatePresence>
        {isOpen && (
          <ChatWindow
            title={title}
            subtitle={subtitle}
            messages={messages}
            isLoading={isLoading}
            isStreaming={isStreaming}
            theme={theme}
            suggestedPrompts={suggestedPrompts}
            onSend={sendMessage}
            onClear={clearConversation}
            onClose={handleClose}
            onStop={stopStreaming}
            onToggleTheme={toggleTheme}
            position={position}
          />
        )}
      </AnimatePresence>

      <ChatButton
        isOpen={isOpen}
        onClick={handleToggle}
        position={position}
        accentColor={accentColor}
      />
    </div>
  );
}

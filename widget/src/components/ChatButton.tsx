/**
 * ChatButton — floating action button to open/close the chat widget.
 */

import { motion, AnimatePresence } from 'motion/react';

interface ChatButtonProps {
  isOpen: boolean;
  onClick: () => void;
  position: 'bottom-right' | 'bottom-left';
  accentColor?: string;
  unreadCount?: number;
}

export function ChatButton({
  isOpen,
  onClick,
  position,
  accentColor,
  unreadCount = 0,
}: ChatButtonProps) {
  return (
    <motion.button
      className={`chat-floating-btn ${position}`}
      onClick={onClick}
      style={accentColor ? { background: accentColor } : undefined}
      whileHover={{ scale: 1.08, boxShadow: '0 8px 30px rgba(0,0,0,0.25)' }}
      whileTap={{ scale: 0.92 }}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
    >
      <AnimatePresence mode="wait">
        {isOpen ? (
          <motion.div
            key="close"
            initial={{ rotate: -90, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            exit={{ rotate: 90, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </motion.div>
        ) : (
          <motion.div
            key="chat"
            initial={{ rotate: 90, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            exit={{ rotate: -90, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Unread badge */}
      {!isOpen && unreadCount > 0 && (
        <motion.span
          className="unread-badge"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 500, damping: 15 }}
        >
          {unreadCount}
        </motion.span>
      )}

      {/* Pulse ring on idle */}
      {!isOpen && (
        <span className="pulse-ring" />
      )}
    </motion.button>
  );
}

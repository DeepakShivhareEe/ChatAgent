/**
 * Typing indicator — animated dots showing the assistant is thinking.
 */

import { motion } from 'motion/react';

export function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="typing-indicator-inner">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="typing-dot"
            animate={{ y: [0, -6, 0] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              delay: i * 0.15,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>
    </div>
  );
}

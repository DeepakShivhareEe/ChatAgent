/**
 * Suggested prompts — clickable chips to help users get started.
 */

import { motion } from 'motion/react';

interface SuggestedPromptsProps {
  prompts: string[];
  onSelect: (prompt: string) => void;
}

export function SuggestedPrompts({ prompts, onSelect }: SuggestedPromptsProps) {
  if (!prompts.length) return null;

  return (
    <div className="suggested-prompts">
      <p className="suggested-prompts-label">Try asking:</p>
      <div className="suggested-prompts-grid">
        {prompts.map((prompt, index) => (
          <motion.button
            key={index}
            className="suggested-prompt-chip"
            onClick={() => onSelect(prompt)}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08, duration: 0.3 }}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="prompt-icon">
              <circle cx="12" cy="12" r="10" />
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            {prompt}
          </motion.button>
        ))}
      </div>
    </div>
  );
}

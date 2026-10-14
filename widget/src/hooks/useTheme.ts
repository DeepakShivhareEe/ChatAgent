/**
 * Theme management hook — dark/light mode with system preference detection.
 */

import { useState, useEffect, useCallback } from 'react';
import type { Theme } from '../types';

export function useTheme(initialTheme?: Theme) {
  const [theme, setTheme] = useState<Theme>(() => {
    if (initialTheme) return initialTheme;
    // Detect system preference
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
    }
    return 'light';
  });

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  }, []);

  // Listen for system theme changes
  useEffect(() => {
    if (initialTheme) return; // Don't override explicit theme

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => {
      setTheme(e.matches ? 'dark' : 'light');
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [initialTheme]);

  return { theme, setTheme, toggleTheme };
}

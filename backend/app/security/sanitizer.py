"""
Input/output sanitizer — strips dangerous HTML, prevents markdown injection.
"""

import re
import html


class Sanitizer:
    """Sanitize user input and LLM output."""

    # Dangerous HTML tags
    DANGEROUS_TAGS = re.compile(
        r"<\s*\/?\s*(script|iframe|object|embed|form|input|button|textarea|select"
        r"|link|meta|style|base|applet)\b[^>]*>",
        re.IGNORECASE,
    )

    # HTML entity patterns
    HTML_TAG = re.compile(r"<[^>]+>")

    # Dangerous markdown patterns (e.g., image/link injections with javascript:)
    DANGEROUS_MARKDOWN = re.compile(
        r"\[([^\]]*)\]\s*\(\s*(javascript|data|vbscript)\s*:",
        re.IGNORECASE,
    )

    # Excessive whitespace / newlines
    EXCESSIVE_NEWLINES = re.compile(r"\n{4,}")
    EXCESSIVE_SPACES = re.compile(r" {10,}")

    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input before processing.

        - Strip dangerous HTML tags
        - Escape remaining HTML entities
        - Remove dangerous markdown links
        - Trim and normalize whitespace
        """
        if not text:
            return ""

        # Strip dangerous HTML tags
        cleaned = self.DANGEROUS_TAGS.sub("", text)

        # Remove all remaining HTML tags from input
        cleaned = self.HTML_TAG.sub("", cleaned)

        # Unescape then re-escape HTML entities
        cleaned = html.unescape(cleaned)
        cleaned = html.escape(cleaned, quote=False)

        # Remove dangerous markdown links
        cleaned = self.DANGEROUS_MARKDOWN.sub("[\\1](removed:", cleaned)

        # Normalize whitespace
        cleaned = self.EXCESSIVE_NEWLINES.sub("\n\n\n", cleaned)
        cleaned = self.EXCESSIVE_SPACES.sub(" ", cleaned)

        return cleaned.strip()

    def sanitize_output(self, text: str) -> str:
        """
        Sanitize LLM output before sending to the client.

        Lighter touch — preserve markdown formatting but remove dangerous elements.
        """
        if not text:
            return ""

        # Strip dangerous HTML tags (but keep safe markdown-related ones)
        cleaned = self.DANGEROUS_TAGS.sub("", text)

        # Remove dangerous markdown links
        cleaned = self.DANGEROUS_MARKDOWN.sub("[\\1](removed:", cleaned)

        return cleaned

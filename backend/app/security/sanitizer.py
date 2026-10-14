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

    # Number of trailing characters held back during streaming so a dangerous
    # HTML tag or markdown link that spans a chunk boundary is always assembled
    # whole before it is sanitized. Also bounds how long an unterminated '<'
    # may delay output.
    STREAM_HOLD_CHARS = 256

    # Longest unterminated markdown link that may be held back. A label longer
    # than this is emitted with the link broken instead of delaying output
    # further (see stream_split).
    MAX_LINK_HOLD_CHARS = 2048

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

    def stream_split(self, buffer: str) -> tuple[str, str]:
        """
        Split an accumulated streaming buffer into text that is safe to emit
        now and a trailing part to keep buffered.

        The trailing STREAM_HOLD_CHARS characters are held back so a dangerous
        tag/link straddling a chunk boundary is sanitized as a whole. In
        addition, the cut point is never placed inside an unterminated
        ``<...`` sequence, nor after an unterminated ``[`` label, because
        ``sanitize_output`` only rewrites a markdown link when it sees the whole
        ``[label](javascript:`` pattern at once — a label longer than the hold
        window would otherwise be emitted in pieces and never sanitized. A
        label longer than MAX_LINK_HOLD_CHARS is emitted with its ``[`` escaped
        instead of held forever, which fails closed: the pieces can no longer
        combine into a clickable link.

        Returns:
            (emit, remainder) — ``emit`` can be sanitized and sent to the
            client; ``remainder`` must stay buffered for the next chunk.
        """
        if len(buffer) <= self.STREAM_HOLD_CHARS:
            return "", buffer

        cut = len(buffer) - self.STREAM_HOLD_CHARS

        # Do not cut inside an unterminated '<...' sequence. Only back up when
        # that '<' is within reach (a bounded amount), so a stray literal '<'
        # cannot stall the stream indefinitely.
        last_lt = buffer.rfind("<", 0, cut)
        if (
            last_lt != -1
            and buffer.rfind(">", 0, cut) < last_lt
            and (cut - last_lt) <= self.STREAM_HOLD_CHARS
        ):
            cut = last_lt

        # Hold back an unterminated markdown link label so the link is
        # assembled before it is sanitized.
        last_open = buffer.rfind("[", 0, cut)
        if last_open != -1 and "]" not in buffer[last_open:cut]:
            if len(buffer) - last_open <= self.MAX_LINK_HOLD_CHARS:
                cut = last_open
            else:
                # The bounded hold is exhausted: emit the text with the opening
                # bracket escaped so the label cannot become a link later.
                return buffer[:last_open] + "\\" + buffer[last_open:cut], buffer[cut:]

        return buffer[:cut], buffer[cut:]

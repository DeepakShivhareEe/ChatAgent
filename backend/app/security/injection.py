"""
Prompt injection detection — identifies and blocks common injection patterns.
"""

import re
from app.models.exceptions import InjectionDetectedError


class InjectionDetector:
    """Detect and block prompt injection attempts."""

    # Patterns that indicate prompt injection attempts
    INJECTION_PATTERNS = [
        # "Ignore previous instructions" variants
        re.compile(
            r"(ignore|disregard|forget|override|bypass|skip)\s+"
            r"(all\s+)?(previous|prior|above|earlier|preceding|original|initial)\s+"
            r"(instructions|prompts?|rules?|directives?|constraints?|guidelines?)",
            re.IGNORECASE,
        ),
        # "You are now" role manipulation
        re.compile(
            r"(you\s+are\s+now|act\s+as|pretend\s+to\s+be|role\s*play\s+as|"
            r"assume\s+the\s+role|behave\s+as|switch\s+to|transform\s+into)",
            re.IGNORECASE,
        ),
        # System prompt extraction
        re.compile(
            r"(reveal|show|display|print|output|repeat|echo|tell)\s+"
            r"(me\s+)?(your|the|system)\s+"
            r"(system\s+)?(prompt|instructions|rules|configuration|settings)",
            re.IGNORECASE,
        ),
        # "New instructions" injection
        re.compile(
            r"(new|updated|revised|replacement)\s+"
            r"(system\s+)?(instructions|prompt|rules|directives)",
            re.IGNORECASE,
        ),
        # Direct system/developer message spoofing
        re.compile(
            r"(\[system\]|\[developer\]|\[admin\]|system\s*:|developer\s*:|admin\s*:)",
            re.IGNORECASE,
        ),
        # "Do anything now" / DAN jailbreak
        re.compile(
            r"(do\s+anything\s+now|DAN\s+mode|jailbreak|unrestricted\s+mode|"
            r"no\s+restrictions|without\s+limitations|unfiltered\s+mode)",
            re.IGNORECASE,
        ),
        # "From now on" directive override
        re.compile(
            r"from\s+now\s+on\s+(you\s+)?(will|must|should|shall|can)\s+"
            r"(ignore|disregard|not\s+follow|bypass)",
            re.IGNORECASE,
        ),
        # Base64/encoding attempts to bypass detection
        re.compile(
            r"(decode|execute|eval|run)\s+(this\s+)?(base64|encoded|encrypted)",
            re.IGNORECASE,
        ),
    ]

    # Maximum input length to prevent resource exhaustion
    MAX_INPUT_LENGTH = 5000

    def detect(self, text: str) -> str:
        """
        Check input for prompt injection patterns.

        Args:
            text: The user input to check.

        Returns:
            The original text if safe.

        Raises:
            InjectionDetectedError: If injection is detected.
        """
        if not text:
            return text

        # Check length
        if len(text) > self.MAX_INPUT_LENGTH:
            raise InjectionDetectedError(
                "Input exceeds maximum allowed length."
            )

        # Check all patterns
        for pattern in self.INJECTION_PATTERNS:
            if pattern.search(text):
                raise InjectionDetectedError(
                    "Your message was flagged by our safety system. "
                    "Please rephrase your question about the website."
                )

        return text

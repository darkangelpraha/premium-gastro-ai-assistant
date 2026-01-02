"""TWILIO_WHATSAPP_LINDY_SETUP.py
Updated: add redact_sandbox_info helper and use it to avoid clear-text logging of phone numbers.
"""

# (existing imports keep as-is)
from typing import Any, Dict


def redact_sandbox_info(sandbox_info: Any) -> Any:
    """Return a shallow-copied sandbox_info with any phone number redacted.

    If sandbox_info is a dict and contains a 'number' key, redact the last
    4 characters (e.g. +1234567890 -> +123456****). If the number is shorter
    than 4 chars or not a string, replace with "[REDACTED]".
    Returns the original value unchanged for non-dict inputs.
    """
    if not isinstance(sandbox_info, dict):
        return sandbox_info
    redacted = dict(sandbox_info)  # shallow copy
    if 'number' in redacted and redacted['number']:
        num = redacted['number']
        if isinstance(num, str) and len(num) >= 4:
            redacted['number'] = num[:-4] + '****'
        else:
            redacted['number'] = '[REDACTED]'
    return redacted


async def step1_verify_twilio_connection(self) -> bool:
    # Get WhatsApp sandbox info
    sandbox_info = self.get_whatsapp_sandbox_info()
    if sandbox_info:
        redacted_sandbox_info = redact_sandbox_info(sandbox_info)
        print(f"   📱 WhatsApp Sandbox: {redacted_sandbox_info}")

    self.setup_log.append("✅ Twilio connection verified")
    return True

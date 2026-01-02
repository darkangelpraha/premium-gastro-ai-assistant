"""Tests for the sandbox info redaction helper.

These are simple unit tests intended to run under pytest. They verify that
phone numbers are masked and short/invalid numbers are replaced with
"[REDACTED]".
"""

from TWILIO_WHATSAPP_LINDY_SETUP import redact_sandbox_info


def test_redact_full_number():
    sandbox = {'number': '+1234567890', 'foo': 'bar'}
    r = redact_sandbox_info(sandbox)
    assert 'number' in r
    assert r['number'].endswith('****')
    assert r['number'] != sandbox['number']


def test_redact_short_number():
    sandbox = {'number': '123', 'foo': 'bar'}
    r = redact_sandbox_info(sandbox)
    assert r['number'] == '[REDACTED]'


# Optionally test non-dict input passthrough

def test_passthrough_non_dict():
    inp = '+123456'
    assert redact_sandbox_info(inp) == inp

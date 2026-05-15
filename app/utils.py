import json
from datetime import datetime
import re
from html import escape as escape_html

TELEGRAM_MESSAGE_TITLE = 'Pulsarr'
TELEGRAM_FULL_LOG_LIMIT = 350
SEVERITY_EMOJIS = {
    'critical': '🔥',
    'high': '🚨',
    'medium': '⚠️',
    'low': 'ℹ️',
}


def compact_json(obj, max_len=8000):
    try:
        s = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    except Exception:
        s = str(obj)
    if len(s) > max_len:
        return s[:max_len] + '...'
    return s


def _safe_get(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
        if cur is None:
            return None
    return cur


def _text_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text if text else None
    if isinstance(value, (int, float, bool)):
        return str(value)
    return None


def _pick_text(*values):
    for value in values:
        text = _text_value(value)
        if text is not None:
            return text
    return None


def _escape_text(value):
    text = _text_value(value)
    if text is None:
        return None
    return escape_html(text)


def _severity_emoji(severity):
    normalized = _pick_text(severity)
    if normalized is None:
        return '🚨'
    return SEVERITY_EMOJIS.get(normalized.lower(), '🚨')


def _format_field(label, value):
    escaped_value = _escape_text(value)
    if escaped_value is None:
        return None
    return f'<b>{escape_html(label)}:</b> {escaped_value}'


def _format_full_log(value):
    text = _pick_text(value)
    if text is None:
        return None
    if len(text) > TELEGRAM_FULL_LOG_LIMIT:
        text = text[:TELEGRAM_FULL_LOG_LIMIT] + '...'
    return f'<b>Log:</b>\n<code>{escape_html(text)}</code>'


# Sensitive keys to mask when logging payloads
_SENSITIVE_KEYS = {"password", "passwd", "secret", "token", "api_key", "apikey", "authorization", "telegram_bot_token", "TELEGRAM_BOT_TOKEN", "bot_token"}


def _mask_value(v: str) -> str:
    if v is None:
        return v
    s = str(v)
    if len(s) <= 8:
        return "****"
    return f"{s[:4]}...{s[-4:]}"


def masked_payload(obj):
    """Return a copy of obj with sensitive values masked for safe logging.

    Works recursively for dicts/lists. Keeps structure but redacts values for keys
    matching _SENSITIVE_KEYS (case-insensitive).
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            key_lower = str(k).lower()
            if any(sk in key_lower for sk in _SENSITIVE_KEYS):
                out[k] = _mask_value(v)
            else:
                out[k] = masked_payload(v)
        return out
    if isinstance(obj, list):
        return [masked_payload(i) for i in obj]
    # primitives
    return obj


def masked_compact_json(obj, max_len=8000):
    try:
        masked = masked_payload(obj)
        s = json.dumps(masked, ensure_ascii=False, separators=(',', ':'))
    except Exception:
        s = str(obj)
    if len(s) > max_len:
        return s[:max_len] + '...'
    return s


def build_telegram_message(payload: dict) -> str:
    """Build a Telegram HTML message from an alert payload."""
    if not isinstance(payload, dict):
        payload = {}

    severity = _pick_text(payload.get('severity'), _safe_get(payload, 'rule', 'level'))
    event_message = _pick_text(
        payload.get('message'),
        payload.get('title'),
        payload.get('alert'),
        _safe_get(payload, 'rule', 'description'),
        'Alert',
    )

    lines = [f"{_severity_emoji(severity)}\n<b>{escape_html(TELEGRAM_MESSAGE_TITLE)}</b>"]

    field_values = [
        ('Event', event_message),
        ('Severity', payload.get('severity')),
        ('Level', _pick_text(payload.get('level'), _safe_get(payload, 'rule', 'level'))),
        ('Source', payload.get('source')),
        ('Orchestrator', payload.get('orchestrator')),
        ('Event type', payload.get('event_type')),
        ('Agent', _pick_text(payload.get('agent'), _safe_get(payload, 'agent', 'name'))),
        ('Agent IP', _pick_text(payload.get('agent_ip'), _safe_get(payload, 'agent', 'ip'), _safe_get(payload, 'agent', 'ip_address'))),
        ('Target user', payload.get('target_user')),
        ('Source IP', _pick_text(payload.get('source_ip'), _safe_get(payload, 'data', 'srcip'), _safe_get(payload, 'data', 'src_ip'), _safe_get(payload, 'source', 'ip'))),
        ('Source port', _pick_text(payload.get('source_port'))),
        ('Rule ID', _pick_text(payload.get('rule_id'), _safe_get(payload, 'rule', 'id'), _safe_get(payload, 'rule', 'rule_id'))),
        ('Decoder', payload.get('decoder')),
        ('Log source', payload.get('log_source')),
        ('Affected endpoint', payload.get('affected_endpoint')),
        ('Workflow', payload.get('workflow')),
    ]

    for label, value in field_values:
        line = _format_field(label, value)
        if line is not None:
            lines.append(line)

    full_log = _format_full_log(payload.get('full_log') or _safe_get(payload, 'data', 'full_log'))
    if full_log is not None:
        lines.append('')
        lines.append(full_log)

    return '\n'.join(lines)


def format_message(payload: dict) -> str:
    return build_telegram_message(payload)


def escape_markdown_v2(text: str) -> str:
    """Escape text for Telegram MarkdownV2 minimal safe subset.

    This function applies backslash escaping to characters that MarkdownV2
    reserves. It is conservative and aims to reduce parse errors.
    """
    if not isinstance(text, str):
        text = str(text)
    # Characters that must be escaped in MarkdownV2
    to_escape = r"_*[]()~`>#+-=|{}.!"
    pattern = re.compile(r'([{}])'.format(re.escape(to_escape)))
    return pattern.sub(r"\\\1", text)

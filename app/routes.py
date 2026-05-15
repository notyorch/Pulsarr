import os
import logging
from html import escape as escape_html
from flask import Blueprint, request, jsonify, current_app
import requests

from .utils import build_telegram_message, masked_compact_json

bp = Blueprint('alerts', __name__)


@bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200


@bp.route('/alert', methods=['POST'])
def alert():
    logger = current_app.logger

    # Basic API key check (X-API-Key header or Bearer token)
    api_key = os.getenv('API_KEY')
    if api_key:
        header = request.headers.get('X-API-Key') or request.headers.get('Authorization')
        if not header:
            logger.warning('Missing API key header')
            return jsonify({'error': 'missing api key'}), 401
        if header.startswith('Bearer '):
            token = header.split(' ', 1)[1]
        else:
            token = header
        if token != api_key:
            logger.warning('Invalid API key')
            return jsonify({'error': 'invalid api key'}), 401

    # Validate JSON payload
    if not request.is_json:
        logger.warning('Request content-type is not application/json')
        return jsonify({'error': 'invalid content type, expected application/json'}), 400

    payload = request.get_json(silent=True)
    if payload is None:
        logger.warning('Malformed JSON payload')
        return jsonify({'error': 'malformed json'}), 400

    # Log a masked version of the payload to avoid leaking secrets
    try:
        # import here to avoid circular import at module import time
        from .utils import masked_compact_json
        logger.info('Received alert payload: %s', masked_compact_json(payload))
    except Exception:
        logger.info('Received alert payload (unavailable)')

    try:
        message_text = build_telegram_message(payload)
    except Exception:
        logger.exception('Failed to format message; falling back to compact payload')
        # fallback to masked compact representation
        message_text = f"<b>Pulsarr</b>\n\n<code>{escape_html(masked_compact_json(payload))}</code>"

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error('Telegram token or chat id not configured')
        return jsonify({'error': 'telegram not configured'}), 500

    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    params = {
        'chat_id': chat_id,
        'text': message_text,
        'disable_web_page_preview': True,
        'parse_mode': 'HTML',
    }

    try:
        r = requests.post(url, json=params, timeout=10)
        r.raise_for_status()
        logger.info('Message forwarded to Telegram chat %s', chat_id)
    except requests.RequestException:
        # Log exception details on server side only; do not return raw exception text to caller
        logger.exception('Failed sending to Telegram')
        return jsonify({'error': 'failed to send to telegram'}), 502

    # parse telegram response safely
    try:
        result = r.json() if r.text else {}
    except Exception:
        result = {'ok': False}

    include_raw = os.getenv('INCLUDE_RAW_JSON', 'false').lower() in ('1', 'true', 'yes')

    response = {'ok': True, 'telegram': result}
    if include_raw:
        response['payload'] = payload

    return jsonify(response), 200

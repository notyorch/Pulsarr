import os
import unittest
from unittest.mock import Mock, patch

from app import create_app
from app.utils import build_telegram_message


class TelegramMessageTests(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict(
            os.environ,
            {
                'TELEGRAM_BOT_TOKEN': 'test-token',
                'TELEGRAM_CHAT_ID': '123456',
                'API_KEY': 'secret-key',
                'INCLUDE_RAW_JSON': 'false',
            },
            clear=False,
        )
        self.env_patch.start()
        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        self.env_patch.stop()

    def test_build_message_minimal_payload(self):
        message = build_telegram_message({'message': 'Alert only'})

        self.assertTrue(message.startswith('🚨\n<b>Pulsarr</b>'))
        self.assertIn('<b>Event:</b> Alert only', message)
        self.assertNotIn('<b>Source:</b>', message)
        self.assertNotIn('<b>Orchestrator:</b>', message)
        self.assertNotIn('<b>Log:</b>', message)

    def test_build_message_enriched_payload(self):
        payload = {
            'message': 'Multiple SSH authentication failures detected',
            'source': 'wazuh',
            'orchestrator': 'shuffle',
            'severity': 'high',
            'level': 9,
            'rule_id': '5716',
            'agent': 'servidor-web-01',
            'agent_ip': '192.168.10.50',
            'target_user': 'root',
            'source_ip': '203.0.113.78',
            'source_port': '54321',
            'decoder': 'sshd',
            'log_source': '/var/log/auth.log',
            'full_log': 'May 15 14:32:18 servidor-web-01 sshd[12345]: Failed password for root from 203.0.113.78 port 54321 ssh2',
            'event_type': 'SSH authentication failure',
            'affected_endpoint': '/ssh',
            'workflow': 'telegram-test',
        }

        message = build_telegram_message(payload)

        self.assertTrue(message.startswith('🚨\n<b>Pulsarr</b>'))
        self.assertIn('<b>Event:</b> Multiple SSH authentication failures detected', message)
        self.assertIn('<b>Severity:</b> high', message)
        self.assertIn('<b>Level:</b> 9', message)
        self.assertIn('<b>Source:</b> wazuh', message)
        self.assertIn('<b>Orchestrator:</b> shuffle', message)
        self.assertIn('<b>Event type:</b> SSH authentication failure', message)
        self.assertIn('<b>Agent:</b> servidor-web-01', message)
        self.assertIn('<b>Agent IP:</b> 192.168.10.50', message)
        self.assertIn('<b>Target user:</b> root', message)
        self.assertIn('<b>Source IP:</b> 203.0.113.78', message)
        self.assertIn('<b>Source port:</b> 54321', message)
        self.assertIn('<b>Rule ID:</b> 5716', message)
        self.assertIn('<b>Decoder:</b> sshd', message)
        self.assertIn('<b>Log source:</b> /var/log/auth.log', message)
        self.assertIn('<b>Affected endpoint:</b> /ssh', message)
        self.assertIn('<b>Workflow:</b> telegram-test', message)
        self.assertIn('<b>Log:</b>', message)
        self.assertIn('Failed password for root from 203.0.113.78 port 54321 ssh2', message)

    def test_full_log_is_truncated(self):
        payload = {
            'message': 'Long log test',
            'full_log': 'a' * 400,
        }

        message = build_telegram_message(payload)

        self.assertIn('<b>Log:</b>', message)
        self.assertIn('a' * 350 + '...', message)
        self.assertNotIn('a' * 351, message)

    @patch('app.routes.requests.post')
    def test_alert_endpoint_sends_html_and_handles_missing_fields(self, mock_post):
        mocked_response = Mock()
        mocked_response.raise_for_status.return_value = None
        mocked_response.text = '{"ok": true}'
        mocked_response.json.return_value = {'ok': True}
        mock_post.return_value = mocked_response

        result = self.client.post(
            '/alert',
            json={'message': 'Only message'},
            headers={'X-API-Key': 'secret-key'},
        )

        self.assertEqual(result.status_code, 200)
        sent_payload = mock_post.call_args.kwargs['json']
        self.assertEqual(sent_payload['parse_mode'], 'HTML')
        self.assertIn('<b>Pulsarr</b>', sent_payload['text'])
        self.assertIn('<b>Event:</b> Only message', sent_payload['text'])


if __name__ == '__main__':
    unittest.main()
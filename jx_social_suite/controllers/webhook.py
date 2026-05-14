# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import logging
import hmac
import hashlib

_logger = logging.getLogger(__name__)


class JxSocialWebhookController(http.Controller):

    @http.route('/jx_social/webhook/<string:provider>', type='http', auth='public',
                methods=['GET', 'POST'], csrf=False)
    def webhook(self, provider, **kwargs):
        """
        Webhook receiver for Facebook/Instagram Graph API events.
        GET  → Hub verification challenge
        POST → Event payload
        """
        # ── GET: Facebook Hub Verification ──
        if request.httprequest.method == 'GET':
            hub_mode      = kwargs.get('hub.mode')
            hub_challenge = kwargs.get('hub.challenge')
            hub_verify    = kwargs.get('hub.verify_token')

            expected = request.env['ir.config_parameter'].sudo().get_param(
                f'jx_social.{provider}_webhook_verify_token'
            )

            if hub_mode == 'subscribe' and hub_verify == expected:
                _logger.info("Webhook verified for provider: %s", provider)
                return request.make_response(hub_challenge)

            _logger.warning("Webhook verification failed for provider: %s", provider)
            return request.make_response('Forbidden', status=403)

        # ── POST: Event Payload ──
        try:
            body = request.httprequest.data
            payload_str = body.decode('utf-8')

            # Verify signature (Facebook sends X-Hub-Signature-256)
            if not self._verify_signature(provider, body, request.httprequest.headers):
                _logger.warning("Invalid webhook signature for %s", provider)
                return request.make_response('Unauthorized', status=401)

            # Store event for async processing
            request.env['jx.social.webhook.event'].sudo().create({
                'provider': provider,
                'event_type': self._extract_event_type(payload_str),
                'payload': payload_str,
                'status': 'pending',
            })

            return request.make_response('ok')

        except Exception as e:
            _logger.exception("Webhook processing error for %s: %s", provider, e)
            return request.make_response('ok')  # Always return 200 to Meta

    def _verify_signature(self, provider, body, headers):
        """Verify X-Hub-Signature-256 from Meta"""
        try:
            app_secret = request.env['ir.config_parameter'].sudo().get_param(
                f'jx_social.{provider}_app_secret'
            )
            if not app_secret:
                return True  # Skip verification if not configured

            signature_header = headers.get('X-Hub-Signature-256', '')
            if not signature_header.startswith('sha256='):
                return False

            expected_sig = hmac.new(
                app_secret.encode(), body, hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(f"sha256={expected_sig}", signature_header)
        except Exception:
            return False

    def _extract_event_type(self, payload_str):
        """Extract event type from payload"""
        try:
            data = json.loads(payload_str)
            return data.get('object', 'unknown')
        except Exception:
            return 'unknown'
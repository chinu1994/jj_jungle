# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import hmac
import hashlib
import logging
import json

_logger = logging.getLogger(__name__)

class JxSocialWebhookController(http.Controller):

    @http.route('/jx_social/webhook/<string:provider>', type='http', auth='public', methods=['POST'], csrf=False)
    def webhook_ingest(self, provider, **kwargs):
        """
        Webhook Ingestion Endpoint as per Section 7.4
        - Validates HMAC signature
        - Stores raw payload in queue table
        """
        try:
            data = request.httprequest.data
            signature = request.httprequest.headers.get('X-Hub-Signature-256') or \
                       request.httprequest.headers.get('X-Signature')

            # Store raw event
            event = request.env['jx.social.webhook.event'].sudo().create({
                'provider': provider,
                'payload': json.loads(data) if data else {},
                'signature': signature,
            })

            # Validate signature (provider-specific secret)
            if not self._validate_signature(provider, data, signature):
                event.write({'status': 'failed', 'error_message': 'Invalid signature'})
                return http.Response("Invalid signature", status=403)

            event.write({'status': 'pending'})
            _logger.info("Webhook received and queued for provider: %s (ID: %s)", provider, event.id)

            return http.Response("OK", status=200)

        except Exception as e:
            _logger.error("Webhook ingestion failed for %s: %s", provider, str(e))
            return http.Response("Error", status=500)

    def _validate_signature(self, provider, data, signature):
        """HMAC-SHA256 validation using provider app secret"""
        if not signature or not data:
            return False

        secret = self._get_provider_secret(provider)
        if not secret:
            return False

        try:
            hmac_obj = hmac.new(secret.encode(), data, hashlib.sha256)
            expected = 'sha256=' + hmac_obj.hexdigest()
            return hmac.compare_digest(expected, signature)
        except:
            return False

    def _get_provider_secret(self, provider):
        """Get secret from system parameters"""
        param = f'jx_social.webhook.secret.{provider}'
        return request.env['ir.config_parameter'].sudo().get_param(param)
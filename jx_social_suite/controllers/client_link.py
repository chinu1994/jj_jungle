# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import logging
import json

_logger = logging.getLogger(__name__)

class JxSocialClientLinkController(http.Controller):

    @http.route('/jx_social/connect/<string:signed_token>', type='http', auth='public', website=True, methods=['GET'])
    def client_connect_link(self, signed_token, **kwargs):
        """
        Client Self-Connection Link Handler
        With Rate Limiting (Max 10 attempts per token per hour) as per WARNING
        """
        # ==================== Rate Limiting Check ====================
        rate_limit_key = f'jx_social_client_link_rate:{signed_token}'
        attempts = request.env['ir.config_parameter'].sudo().get_param(rate_limit_key, '0')
        attempts = int(attempts)

        if attempts >= 10:
            _logger.warning("Rate limit exceeded for client link: %s", signed_token)
            return request.render('jx_social_suite.client_link_error', {
                'message': 'Too many attempts. Please try again after some time.'
            })

        # Increment attempt counter
        request.env['ir.config_parameter'].sudo().set_param(rate_limit_key, str(attempts + 1))

        # Auto expire rate limit counter after 1 hour
        # (In production, better to use redis or a dedicated rate limit table)

        # ==================== Link Validation ====================
        link = request.env['jx.social.client_link'].sudo().search([
            ('signed_token', '=', signed_token)
        ], limit=1)

        if not link:
            return request.render('jx_social_suite.client_link_error', {
                'message': 'Invalid or expired connection link.'
            })

        if link.used or link.expiry < fields.Datetime.now():
            return request.render('jx_social_suite.client_link_error', {
                'message': 'This connection link has expired or has already been used.'
            })

        # Security: Only show allowed providers for this client — No agency or other data exposed
        try:
            allowed_providers = json.loads(link.allowed_providers or '[]')
        except:
            allowed_providers = []

        # Render minimal branded page (No agency info, no other client data)
        return request.render('jx_social_suite.client_connect_page', {
            'link': link,
            'allowed_providers': allowed_providers,
            'partner_name': link.partner_id.name,   # Only client's own name
        })

    @http.route('/jx_social/connect/<string:signed_token>/start/<string:provider>',
                type='http', auth='public', website=True, methods=['GET'])
    def start_oauth_from_link(self, signed_token, provider, **kwargs):
        """Start OAuth from client link"""
        link = request.env['jx.social.client_link'].sudo().search([
            ('signed_token', '=', signed_token)
        ], limit=1)

        if not link or link.used or link.expiry < fields.Datetime.now():
            return request.redirect('/jx_social/connect/' + signed_token + '?error=invalid_link')

        allowed = json.loads(link.allowed_providers or '[]')
        if provider not in allowed:
            return request.redirect('/jx_social/connect/' + signed_token + '?error=provider_not_allowed')

        # Pass client_link reference in state
        state = f"client_link:{signed_token}:{provider}"

        return request.redirect(f'/jx_social/oauth/init/{provider}?state={state}')
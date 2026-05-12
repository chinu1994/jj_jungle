# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class JxSocialOAuthController(http.Controller):

    @http.route('/jx_social/oauth/callback/<string:provider>', type='http', auth='user', methods=['GET'])
    def oauth_callback(self, provider, **kwargs):
        """
        OAuth Callback Handler
        Follows exact flow defined in Sprint 1 Documentation Section 5.1.1
        """
        code = kwargs.get('code')
        state = kwargs.get('state')
        error = kwargs.get('error')

        if error:
            _logger.error("OAuth Error from %s: %s", provider, error)
            return request.redirect('/web#action=jx_social_account_action&error=oauth_failed')

        if not code or not state:
            _logger.warning("Missing code or state in OAuth callback")
            return request.redirect('/web#action=jx_social_account_action&error=invalid_callback')

        # TODO: State validation will be implemented using services/token_service + jx.social.token pending record
        # As per doc: Validate signed JWT/HMAC, expiry, nonce, agency_user_id, client_partner_id

        try:
            # This logic will call Token Service (to be created)
            token_service = request.env['jx.social.token.service']
            result = token_service.process_oauth_callback(provider, code, state)

            if result.get('success'):
                return request.redirect('/web#action=jx_social_account_action&success=account_connected')
            else:
                _logger.error("OAuth processing failed: %s", result.get('error'))
                return request.redirect('/web#action=jx_social_account_action&error=token_processing_failed')

        except Exception as e:
            _logger.exception("Critical error in OAuth callback for provider %s", provider)
            return request.redirect('/web#action=jx_social_account_action&error=system_error')
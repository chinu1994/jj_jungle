# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class JxSocialOAuthController(http.Controller):

    @http.route('/jx_social/oauth/callback/<string:provider>', type='http', auth='user', methods=['GET'])
    def oauth_callback(self, provider, **kwargs):
        code = kwargs.get('code')
        state = kwargs.get('state')
        error = kwargs.get('error')

        if error:
            _logger.error("OAuth Error: %s", error)
            return request.redirect('/web?#action=jx_social_account_action&error=1')

        if not code or not state:
            return request.redirect('/web?#action=jx_social_account_action&error=2')

        try:
            token_service = request.env['jx.social.token.service']
            result = token_service.process_oauth_callback(provider, code, state)

            if result.get('success'):
                return request.redirect('/web?#action=jx_social_account_action&success=connected')
            else:
                return request.redirect('/web?#action=jx_social_account_action&error=3')

        except Exception as e:
            _logger.exception("OAuth Callback Failed")
            return request.redirect('/web?#action=jx_social_account_action&error=4')
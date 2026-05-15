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

        # Action ID dynamically fetch karo
        def get_action_url(extra=''):
            action = request.env.ref(
                'jx_social_suite.jx_social_account_action',
                raise_if_not_found=False
            )
            action_id = action.id if action else ''
            return f'/web#action={action_id}{extra}'

        if error:
            _logger.error("OAuth Error: %s", error)
            return request.redirect(get_action_url('&error=1'))

        if not code or not state:
            return request.redirect(get_action_url('&error=2'))

        try:
            token_service = request.env['jx.social.token.service']
            result = token_service.process_oauth_callback(provider, code, state)

            if result.get('success'):
                return request.redirect(get_action_url('&success=connected'))
            else:
                return request.redirect(get_action_url('&error=3'))

        except Exception as e:
            _logger.exception("OAuth Callback Failed")
            return request.redirect(get_action_url('&error=4'))
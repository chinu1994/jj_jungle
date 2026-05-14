# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class JxSocialClientLinkController(http.Controller):

    @http.route('/jx_social/connect/<string:token>', type='http', auth='public', methods=['GET'])
    def client_connect(self, token, **kwargs):
        """
        Public URL sent to clients to connect their social accounts.
        Validates the signed token and redirects to OAuth flow.
        """
        try:
            link = request.env['jx.social.client_link'].sudo().search([
                ('signed_token', '=', token),
                ('used', '=', False),
            ], limit=1)

            if not link:
                return request.render('jx_social_suite.client_link_invalid', {
                    'error': 'This link is invalid or has already been used.'
                })

            if not link.active:
                return request.render('jx_social_suite.client_link_invalid', {
                    'error': 'This link has expired. Please request a new one.'
                })

            # Store token in session for post-OAuth use
            request.session['jx_client_link_token'] = token

            return request.render('jx_social_suite.client_link_landing', {
                'link': link,
                'partner': link.partner_id,
            })

        except Exception as e:
            _logger.exception("Client link error: %s", e)
            return request.render('jx_social_suite.client_link_invalid', {
                'error': 'Something went wrong. Please contact your agency.'
            })

    @http.route('/jx_social/connect/<string:token>/start/<string:provider>',
                type='http', auth='public', methods=['GET'])
    def client_connect_provider(self, token, provider, **kwargs):
        """Start OAuth for a specific provider from client link."""
        try:
            link = request.env['jx.social.client_link'].sudo().search([
                ('signed_token', '=', token),
                ('used', '=', False),
            ], limit=1)

            if not link or not link.active:
                return request.redirect('/web')

            connector = request.env['jx.social.connector.registry'].sudo().get_connector(provider)
            # Use token as state so callback can identify the link
            oauth_url = connector.get_oauth_auth_url(state=f"link_{token}")
            return request.redirect(oauth_url)

        except Exception as e:
            _logger.exception("Client connect provider error: %s", e)
            return request.redirect('/web')
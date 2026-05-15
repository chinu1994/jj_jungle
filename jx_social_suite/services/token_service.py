# -*- coding: utf-8 -*-
from odoo import models, api, fields
from cryptography.fernet import Fernet
import logging

_logger = logging.getLogger(__name__)


class JxSocialTokenService(models.AbstractModel):
    _name = 'jx.social.token.service'
    _description = 'JX Social Token Service'

    # ==================== Encryption ====================

    def _get_fernet(self):
        secret = self.env['ir.config_parameter'].sudo().get_param('jx_social.token_secret_key')
        if not secret:
            raise Exception("Token encryption key not configured. Set 'jx_social.token_secret_key' in System Parameters.")
        return Fernet(secret.encode())

    def encrypt_token(self, raw_value):
        if not raw_value:
            return False
        return self._get_fernet().encrypt(raw_value.encode()).decode()

    def decrypt_token(self, encrypted_value):
        if not encrypted_value:
            return False
        return self._get_fernet().decrypt(encrypted_value.encode()).decode()

    # ==================== OAuth Callback ====================

    @api.model
    def process_oauth_callback(self, provider, code, state):
        """
        Called from oauth_callback controller.
        state = social account ID (as string)
        """

        if provider == 'facebook':
            return self._process_facebook_callback(code, state)

        account_id = int(state)
        account = self.env['jx.social.account'].browse(account_id)

        if not account.exists():
            raise Exception(f"Social account {account_id} not found")

        # Exchange code for token via connector
        connector = self.env['jx.social.connector.registry'].get_connector(provider)
        token_data = connector.exchange_code_for_token(code, state)

        access_token  = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_at    = token_data.get('expires_at')

        if not access_token:
            raise Exception("No access token returned from provider")

        # Encrypt before saving
        encrypted_access  = self.encrypt_token(access_token)
        encrypted_refresh = self.encrypt_token(refresh_token) if refresh_token else False

        # Create or update token linked to this account
        existing_token = account.token_id
        if existing_token:
            existing_token.write({
                'access_token_encrypted': encrypted_access,
                'refresh_token_encrypted': encrypted_refresh,
                'expires_at': expires_at,
            })
            token = existing_token
        else:
            token = self.env['jx.social.token'].create({
                'provider': provider,
                'access_token_encrypted': encrypted_access,
                'refresh_token_encrypted': encrypted_refresh,
                'expires_at': expires_at,
            })

            account.write({
                'token_id': token.id,
                'last_synced': fields.Datetime.now(),
                'agency_user_id': self.env.user.id,
            })
        _logger.info("Token saved successfully for account %s (%s)", account.id, provider)
        return {'success': True, 'token_id': token.id}

    # ==================== Disconnect ====================

    @api.model
    def disconnect_account(self, account):
        """Revoke token via connector, then delete token record"""
        if not account.token_id:
            return

        try:
            connector = self.env['jx.social.connector.registry'].get_connector(account.provider)
            connector.revoke_token(account.token_id)
        except Exception as e:
            _logger.warning("Token revoke failed (non-fatal): %s", e)

        account.token_id.unlink()

    def health_check_all_tokens(self):
        _logger.info("JX Social: Token health check starting")
        tokens = self.env['jx.social.token'].search([])  # no active filter
        for token in tokens:
            if not token.access_token_encrypted:
                _logger.warning("Token %s has no access token", token.id)
        _logger.info("JX Social: Token health check done. Checked %s tokens", len(tokens))

    @api.model
    def _process_facebook_callback(self, code, state):

        account_id = int(state)

        account = self.env['jx.social.account'].browse(account_id)

        if not account.exists():
            raise Exception("Social account not found")

        connector = self.env['jx.social.connector.registry'].get_connector('facebook')

        token_data = connector.exchange_code_for_token(code, state)

        access_token = token_data.get('access_token')

        if not access_token:
            raise Exception("No access token returned")

        # ==========================================
        # GET FACEBOOK PAGES
        # ==========================================

        pages = connector.get_connected_accounts(access_token)

        if not pages:
            raise Exception("No Facebook pages found")

        # First page
        page = pages[0]

        page_id = page.get('id')
        page_name = page.get('name')
        page_token = page.get('access_token')

        encrypted_access = self.encrypt_token(page_token)

        # ==========================================
        # CREATE / UPDATE TOKEN
        # ==========================================

        existing_token = account.token_id

        if existing_token:

            existing_token.write({
                'access_token_encrypted': encrypted_access,
            })

            token = existing_token

        else:

            token = self.env['jx.social.token'].create({
                'provider': 'facebook',
                'access_token_encrypted': encrypted_access,
            })

        # ==========================================
        # UPDATE EXISTING ACCOUNT
        # ==========================================

        account.write({
            'token_id': token.id,
            'last_synced': fields.Datetime.now(),
            'agency_user_id': self.env.user.id,
        })

        return {
            'success': True,
            'token_id': token.id,
        }
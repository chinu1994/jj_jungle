# -*- coding: utf-8 -*-

from odoo import models, api, fields
from cryptography.fernet import Fernet
import base64
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class JxSocialTokenService(models.AbstractModel):
    _name = 'jx.social.token.service'
    _description = 'JX Social Token Service'

    # ==================== Encryption ====================
    @api.model
    def _get_encryption_key(self):
        key = self.env['ir.config_parameter'].sudo().get_param('jx_social.encryption_key')
        if not key:
            key = Fernet.generate_key().decode()
            self.env['ir.config_parameter'].sudo().set_param('jx_social.encryption_key', key)
            _logger.warning("New encryption key generated. Set via env var in production!")
        return key.encode()

    @api.model
    def _get_fernet(self):
        return Fernet(self._get_encryption_key())

    @api.model
    def encrypt_token(self, raw_token):
        if not raw_token:
            return False
        try:
            fernet = self._get_fernet()
            encrypted = fernet.encrypt(raw_token.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            _logger.error("Token encryption failed")
            return False

    @api.model
    def decrypt_token(self, encrypted_token):
        if not encrypted_token:
            return False
        try:
            fernet = self._get_fernet()
            decoded = base64.urlsafe_b64decode(encrypted_token.encode())
            return fernet.decrypt(decoded).decode()
        except Exception:
            _logger.error("Token decryption failed")
            return False

    # ==================== Token Refresh & Health (5.3) ====================
    @api.model
    def should_refresh_token(self, token):
        """Check if token needs refresh based on buffer"""
        if not token or not token.expires_at:
            return True
        buffer_minutes = 10  # Default buffer, connectors can override
        buffer = timedelta(minutes=buffer_minutes)
        return fields.Datetime.now() > (token.expires_at - buffer)

    @api.model
    def refresh_token(self, token):
        """Refresh token using refresh_token (connector specific logic will be called)"""
        # Will be implemented per connector in Section 6
        return {'success': False, 'error': 'Connector refresh logic pending'}

    @api.model
    def health_check_all_tokens(self):
        """Daily cron job - Token Health Check"""
        accounts = self.env['jx.social.account'].search([('status', '=', 'connected')])
        for account in accounts:
            if account.token_id:
                self._perform_health_check(account)

    @api.model
    def _perform_health_check(self, account):
        """Lightweight profile call to verify token"""
        try:
            connector = self.env['jx.social.connector']._get_connector(account.provider)
            result = connector.test_connection(account)
            if not result.get('success'):
                if result.get('error_type') == 'auth':
                    account.status = 'error'
                    # TODO: Send notification to agency_user_id
        except Exception as e:
            _logger.error("Health check failed for account %s", account.id)

    @api.model
    def disconnect_account(self, account):
        """Proper disconnect as per documentation"""
        if not account.token_id:
            return

        # Revoke token at provider if supported (connector responsibility)
        try:
            connector = self.env['jx.social.connector']._get_connector(account.provider)
            connector.revoke_token(account.token_id)
        except Exception:
            _logger.warning("Token revocation failed or not supported for %s", account.provider)

        # Delete token record
        account.token_id.unlink()

        # Update account status
        account.write({
            'status': 'disconnected',
            'token_id': False,
        })

        # Audit log will be written from calling method
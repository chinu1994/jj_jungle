# -*- coding: utf-8 -*-
from odoo import models, fields, api
from cryptography.fernet import Fernet
import logging

_logger = logging.getLogger(__name__)


class JxSocialToken(models.Model):
    _name = 'jx.social.token'
    _description = 'JX Social OAuth Token'
    _rec_name = 'provider'

    provider = fields.Selection([
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
        ('twitter', 'Twitter / X'),
        ('google_business', 'Google Business'),
    ], string='Provider', required=True)

    access_token_encrypted = fields.Char(
        string='Access Token (Encrypted)',
        groups='base.group_system'
    )
    refresh_token_encrypted = fields.Char(
        string='Refresh Token (Encrypted)',
        groups='base.group_system'
    )
    expires_at = fields.Datetime(string='Expires At')
    is_valid = fields.Boolean(
        string='Is Valid',
        compute='_compute_is_valid',
        store=False
    )
    scopes = fields.Char(string='Scopes')
    raw_response = fields.Text(string='Raw Response')

    social_account_ids = fields.One2many(
        'jx.social.account', 'token_id', string='Accounts'
    )

    # ==================== Encryption ====================

    def _get_fernet(self):
        secret = self.env['ir.config_parameter'].sudo().get_param(
            'jx_social.token_secret_key'
        )
        if not secret:
            raise Exception(
                "Token encryption key not configured. "
                "Set 'jx_social.token_secret_key' in System Parameters."
            )
        return Fernet(secret.encode())

    def _encrypt(self, value):
        if not value:
            return False
        return self._get_fernet().encrypt(value.encode()).decode()

    def _decrypt(self, value):
        if not value:
            return False
        return self._get_fernet().decrypt(value.encode()).decode()

    def get_decrypted_access_token(self):
        self.ensure_one()
        return self._decrypt(self.access_token_encrypted)

    def get_decrypted_refresh_token(self):
        self.ensure_one()
        return self._decrypt(self.refresh_token_encrypted)

    def set_tokens(self, access_token, refresh_token=None):
        self.ensure_one()
        vals = {'access_token_encrypted': self._encrypt(access_token)}
        if refresh_token:
            vals['refresh_token_encrypted'] = self._encrypt(refresh_token)
        self.write(vals)

    # ==================== Computed ====================

    @api.depends('expires_at', 'access_token_encrypted')
    def _compute_is_valid(self):
        now = fields.Datetime.now()
        for record in self:
            if not record.access_token_encrypted:
                record.is_valid = False
            elif record.expires_at and record.expires_at < now:
                record.is_valid = False
            else:
                record.is_valid = True  # No expiry = long-lived token = valid
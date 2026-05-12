# -*- coding: utf-8 -*-

from odoo import models, fields, api

class JxSocialToken(models.Model):
    _name = 'jx.social.token'
    _description = 'JX Social Token'

    account_id = fields.Many2one(
        'jx.social.account',
        string='Social Account',
        required=True,
        ondelete='cascade'
    )

    provider = fields.Selection(related='account_id.provider', store=True)

    access_token = fields.Char(string='Access Token (Encrypted)', required=True)
    refresh_token = fields.Char(string='Refresh Token (Encrypted)')

    expires_at = fields.Datetime()
    scopes = fields.Char()

    is_valid = fields.Boolean(compute='_compute_is_valid')

    @api.depends('expires_at')
    def _compute_is_valid(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_valid = bool(record.expires_at and record.expires_at > now)

    # ==================== Secure Token Access ====================
    def get_decrypted_access_token(self):
        self.ensure_one()
        token_service = self.env['jx.social.token.service']
        return token_service.decrypt_token(self.access_token)

    def get_decrypted_refresh_token(self):
        self.ensure_one()
        if not self.refresh_token:
            return False
        token_service = self.env['jx.social.token.service']
        return token_service.decrypt_token(self.refresh_token)
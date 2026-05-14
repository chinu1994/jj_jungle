# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class JxSocialAccount(models.Model):
    _name = 'jx.social.account'
    _description = 'JX Social Account'
    _rec_name = 'account_name'
    _order = 'partner_id, provider'

    # ==================== Main Fields ====================
    partner_id = fields.Many2one(
        'res.partner', string='Client', required=True, ondelete='cascade',
        domain="[('is_company', '=', True)]"
    )
    provider = fields.Selection(
        selection=[
            ('facebook', 'Facebook'),
            ('instagram', 'Instagram'),
            ('linkedin', 'LinkedIn'),
            ('tiktok', 'TikTok'),
            ('twitter', 'Twitter / X'),
            ('google_business', 'Google Business'),
        ],
        string='Provider', required=True
    )
    account_name = fields.Char(string='Account Name')
    account_external_id = fields.Char(string='External ID')
    account_type = fields.Selection(
        selection=[('page', 'Page'), ('profile', 'Profile'),
                   ('company', 'Company'), ('business_profile', 'Business Profile')],
        string='Account Type'
    )
    status = fields.Selection(
        selection=[('connected', 'Connected'), ('disconnected', 'Disconnected'),
                   ('error', 'Error'), ('pending', 'Pending')],
        string='Status', default='pending', compute='_compute_status', store=True
    )
    token_id = fields.Many2one('jx.social.token', string='Token', ondelete='set null')
    last_synced = fields.Datetime(string='Last Synced')
    scopes = fields.Char(string='Scopes')
    agency_user_id = fields.Many2one('res.users', string='Connected By')

    # Relational
    post_ids = fields.Many2many('jx.social.post', string='Posts')
    schedule_ids = fields.One2many('jx.social.schedule', 'social_account_id', string='Scheduled Posts')
    analytics_ids = fields.One2many('jx.social.analytics', 'analytic_account_id', string='Analytics')

    # ==================== Computed ====================
    @api.depends('token_id')
    def _compute_status(self):
        for record in self:
            if record.token_id and record.token_id.is_valid:
                record.status = 'connected'
            elif record.token_id:
                record.status = 'error'
            else:
                record.status = 'disconnected'

    # ==================== Actions (Important) ====================
    def action_connect_account(self):
        """Connect Account Button"""
        self.ensure_one()
        try:
            connector = self.env['jx.social.connector.registry'].get_connector(self.provider)
            oauth_url = connector.get_oauth_auth_url(state=str(self.id))

            return {
                'type': 'ir.actions.act_url',
                'url': oauth_url,
                'target': 'self',
            }
        except Exception as e:
            raise UserError(_("Connection failed: %s") % str(e))

    def action_disconnect_account(self):
        """Disconnect Account Button"""
        self.ensure_one()
        try:
            if self.token_id:
                self.env['jx.social.token.service'].disconnect_account(self)

            self.write({'status': 'disconnected', 'token_id': False})

            self.env['jx.social.audit'].create({
                'action_type': 'disconnect',
                'user_id': self.env.user.id,
                'partner_id': self.partner_id.id,
                'social_account_id': self.id,
                'result': 'success',
            })
            return True
        except Exception as e:
            raise UserError(_("Disconnect failed: %s") % str(e))
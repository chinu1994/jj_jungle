# -*- coding: utf-8 -*-

from odoo import models, fields, api

class JxSocialAccount(models.Model):
    _name = 'jx.social.account'
    _description = 'JX Social Account'
    _rec_name = 'account_name'
    _order = 'partner_id, provider'

    # ==================== Main Fields ====================
    partner_id = fields.Many2one(
        'res.partner',
        string='Client',
        required=True,
        ondelete='cascade',
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
        string='Provider',
        required=True,
        help="Social Media Platform"
    )

    account_name = fields.Char(
        string='Account Name',
        help="Display name of the connected account (from provider)"
    )

    account_external_id = fields.Char(
        string='External ID',
        help="Provider's stable ID for the page/profile"
    )

    account_type = fields.Selection(
        selection=[
            ('page', 'Page'),
            ('profile', 'Profile'),
            ('company', 'Company'),
            ('business_profile', 'Business Profile'),
        ],
        string='Account Type'
    )

    status = fields.Selection(
        selection=[
            ('connected', 'Connected'),
            ('disconnected', 'Disconnected'),
            ('error', 'Error'),
            ('pending', 'Pending'),
        ],
        string='Status',
        default='pending',
        compute='_compute_status',
        store=True
    )

    token_id = fields.Many2one(
        'jx.social.token',
        string='Token',
        ondelete='set null',
        help="Linked OAuth token (1:1)"
    )

    last_synced = fields.Datetime(
        string='Last Synced',
        help="Last successful analytics synchronization"
    )

    scopes = fields.Char(
        string='Scopes',
        help="Comma-separated OAuth scopes granted"
    )

    agency_user_id = fields.Many2one(
        'res.users',
        string='Connected By',
        help="Agency user who connected this account"
    )

    # ==================== Relational Fields ====================
    post_ids = fields.Many2many(
        'jx.social.post',
        string='Posts',
        relation='jx_social_post_account_rel'
    )

    schedule_ids = fields.One2many(
        'jx.social.schedule',
        'social_account_id',
        string='Scheduled Posts'
    )

    analytics_ids = fields.One2many(
        'jx.social.analytics',
        'analytic_account_id',
        string='Analytics History'
    )

    # ==================== Computed Fields ====================
    @api.depends('token_id')
    def _compute_status(self):
        for record in self:
            if record.token_id and record.token_id.is_valid:
                record.status = 'connected'
            elif record.token_id:
                record.status = 'error'
            else:
                record.status = 'disconnected'
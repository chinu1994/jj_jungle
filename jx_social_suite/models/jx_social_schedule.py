# -*- coding: utf-8 -*-

from odoo import models, fields, api

class JxSocialSchedule(models.Model):
    _name = 'jx.social.schedule'
    _description = 'JX Social Schedule'
    _rec_name = 'post_id'
    _order = 'scheduled_at desc, create_date desc'

    # ==================== Main Fields ====================
    post_id = fields.Many2one(
        'jx.social.post',
        string='Post',
        required=True,
        ondelete='cascade',
        index=True
    )

    social_account_id = fields.Many2one(
        'jx.social.account',
        string='Social Account',
        required=True,
        ondelete='restrict',
        index=True,
        help="Target account for this schedule"
    )

    scheduled_at = fields.Datetime(
        string='Scheduled At',
        help="When to publish. NULL = publish immediately"
    )

    published_at = fields.Datetime(
        string='Published At',
        readonly=True,
        help="When provider confirmed publication"
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('queued', 'Queued'),
            ('publishing', 'Publishing'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
            ('retried', 'Retried'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        default='draft',
        required=True,
        index=True,
        help="Job state machine"
    )

    external_post_id = fields.Char(
        string='External Post ID',
        help="Provider's ID for the published post"
    )

    retry_count = fields.Integer(
        string='Retry Count',
        default=0
    )

    max_retries = fields.Integer(
        string='Max Retries',
        default=3
    )

    error_message = fields.Text(
        string='Error Message',
        help="Last error from provider API"
    )

    provider_response = fields.Text(
        string='Provider Response',
        help="Raw provider API response (JSON) for debugging"
    )

    # ==================== Relational / Helper Fields ====================
    partner_id = fields.Many2one(
        related='post_id.partner_id',
        string='Client',
        store=True,
        readonly=True
    )

    provider = fields.Selection(
        related='social_account_id.provider',
        string='Provider',
        store=True,
        readonly=True
    )

    # ==================== Constraints ====================
    _sql_constraints = [
        ('unique_post_account',
         'unique(post_id, social_account_id)',
         'Only one schedule per (Post, Account) pair is allowed!')
    ]

    # ==================== State Helpers (Optional but recommended) ====================
    def action_queue(self):
        """Move to queued state"""
        self.write({
            'state': 'queued',
            'retry_count': 0
        })

    def action_mark_publishing(self):
        """Mark as currently publishing"""
        self.write({'state': 'publishing'})

    def action_mark_sent(self, external_post_id=None):
        """Mark as successfully sent"""
        vals = {
            'state': 'sent',
            'published_at': fields.Datetime.now(),
        }
        if external_post_id:
            vals['external_post_id'] = external_post_id
        self.write(vals)

    def action_fail(self, error_message=None, response=None):
        """Mark as failed"""
        self.write({
            'state': 'failed',
            'error_message': error_message,
            'provider_response': response,
        })
# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import logging

_logger = logging.getLogger(__name__)

class JxSocialAudit(models.Model):
    _name = 'jx.social.audit'
    _description = 'JX Social Audit Log'
    _order = 'timestamp desc, id desc'
    _rec_name = 'timestamp'

    # ==================== Main Fields ====================
    action_type = fields.Selection(
        selection=[
            ('connect', 'Connect Account'),
            ('disconnect', 'Disconnect Account'),
            ('publish', 'Publish Post'),
            ('schedule', 'Schedule Post'),
            ('reschedule', 'Reschedule Post'),
            ('boost', 'Boost Post'),
            ('template_save', 'Save Template'),
            ('link_generate', 'Generate Client Link'),
            ('link_used', 'Client Link Used'),
            ('token_refresh', 'Token Refresh'),
            ('token_revoke', 'Token Revoke'),
            ('permission_denied', 'Permission Denied'),
        ],
        string='Action Type',
        required=True
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        readonly=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Client',
        help="Client this action relates to"
    )

    social_account_id = fields.Many2one(
        'jx.social.account',
        string='Social Account'
    )

    post_id = fields.Many2one(
        'jx.social.post',
        string='Post'
    )

    details = fields.Text(
        string='Details',
        help="JSON string with contextual data"
    )

    ip_address = fields.Char(
        string='IP Address',
        readonly=True
    )

    timestamp = fields.Datetime(
        string='Timestamp',
        default=fields.Datetime.now,
        readonly=True
    )

    result = fields.Selection(
        selection=[
            ('success', 'Success'),
            ('failure', 'Failure'),
            ('partial', 'Partial'),
        ],
        string='Result',
        default='success'
    )

    # ==================== Immutable Audit Log ====================
    @api.model_create_multi
    def create(self, vals_list):
        """Create audit records using sudo to bypass normal ACL"""
        for vals in vals_list:
            # Ensure timestamp is set
            if not vals.get('timestamp'):
                vals['timestamp'] = fields.Datetime.now()

            # Convert dict to JSON string if details is a dictionary
            if isinstance(vals.get('details'), dict):
                try:
                    vals['details'] = json.dumps(vals['details'], default=str)
                except:
                    vals['details'] = str(vals['details'])

        # Use sudo() ONLY here as per documentation note
        return super(JxSocialAudit, self.sudo()).create(vals_list)

    # Block all write and unlink operations
    def write(self, vals):
        _logger.warning("Attempted to modify immutable audit record (ID: %s). Operation blocked.", self.ids)
        return False

    def unlink(self):
        _logger.warning("Attempted to delete audit record (ID: %s). Operation blocked.", self.ids)
        return False
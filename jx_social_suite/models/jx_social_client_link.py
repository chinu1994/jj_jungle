# -*- coding: utf-8 -*-

from odoo import models, fields, api
import hashlib
import hmac
import json
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)



class JxSocialClientLink(models.Model):
    _name = 'jx.social.client_link'
    _description = 'JX Social Client Connection Link'
    _rec_name = 'signed_token'

    signed_token = fields.Char(
        string='Signed Token',
        required=True,
        index=True,
        readonly=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Client',
        required=True,
        ondelete='cascade',
        domain="[('is_company', '=', True)]"
    )

    agency_user_id = fields.Many2one(
        'res.users',
        string='Agency User',
        required=True,
        default=lambda self: self.env.user
    )

    allowed_providers = fields.Char(
        string='Allowed Providers',
        help="JSON list of allowed providers e.g. ['facebook','instagram']"
    )

    expiry = fields.Datetime(
        string='Expiry',
        required=True
    )

    used = fields.Boolean(
        string='Used',
        default=False
    )

    connected_providers = fields.Char(
        string='Connected Providers',
        help="JSON list of successfully connected providers"
    )

    # ==================== Helper Fields ====================
    active = fields.Boolean(
        compute='_compute_active',
        store=False
    )

    @api.depends('expiry', 'used')
    def _compute_active(self):
        now = fields.Datetime.now()
        for record in self:
            record.active = not record.used and (record.expiry > now)

    # ==================== Create Method ====================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('signed_token'):
                token_data = {
                    'partner_id': vals['partner_id'],
                    'agency_user_id': vals.get('agency_user_id') or self.env.user.id,
                    'timestamp': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                secret = self.env['ir.config_parameter'].sudo().get_param('database.secret')
                message = json.dumps(token_data, sort_keys=True).encode()
                vals['signed_token'] = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

            if not vals.get('expiry'):
                vals['expiry'] = fields.Datetime.now() + timedelta(hours=72)

        return super().create(vals_list)

    def _cleanup_expired_links(self):
        _logger.info("JX Social: Client link cleanup done (stub)")
        return True
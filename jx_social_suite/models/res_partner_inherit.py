# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    social_account_ids = fields.One2many(
        'jx.social.account',
        'partner_id',
        string='Social Accounts'
    )

    social_account_count = fields.Integer(
        string='Social Accounts Count',  # ← fixed label
        compute='_compute_social_account_count'
    )

    def _compute_social_account_count(self):
        for partner in self:
            partner.social_account_count = len(partner.social_account_ids)

    def action_view_social_accounts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Social Accounts',
            'res_model': 'jx.social.account',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
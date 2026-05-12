# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ==================== Social Account Integration ====================
    social_account_count = fields.Integer(
        string='Connected Social Accounts',
        compute='_compute_social_account_count',
        store=True
    )

    social_account_ids = fields.One2many(
        'jx.social.account',
        'partner_id',
        string='Social Accounts'
    )

    @api.depends('social_account_ids')
    def _compute_social_account_count(self):
        for partner in self:
            partner.social_account_count = len(partner.social_account_ids)

    # ==================== Archive Handling ====================
    def write(self, vals):
        """When client is archived, disconnect all social accounts"""
        res = super().write(vals)

        if vals.get('active') is False:
            # Archive = Disconnect accounts but do NOT delete them
            accounts = self.env['jx.social.account'].search([
                ('partner_id', 'in', self.ids),
                ('status', '!=', 'disconnected')
            ])
            if accounts:
                accounts.write({'status': 'disconnected'})
                # Optional: Log in audit
                for acc in accounts:
                    self.env['jx.social.audit'].create({
                        'action_type': 'disconnect',
                        'user_id': self.env.user.id,
                        'partner_id': acc.partner_id.id,
                        'social_account_id': acc.id,
                        'result': 'success',
                        'details': 'Client archived - account disconnected automatically'
                    })
        return res
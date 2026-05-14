# -*- coding: utf-8 -*-

from odoo import models, fields

class JxSocialAnalytics(models.Model):
    _name = 'jx.social.analytics'
    _description = 'JX Social Analytics'

    analytic_account_id = fields.Many2one(
        'jx.social.account',
        string='Social Account',
        ondelete='cascade'
    )

    post_id = fields.Many2one(
        'jx.social.post',
        string='Post'
    )

    date = fields.Date(string='Date')

    impressions = fields.Integer(string='Impressions')
    clicks = fields.Integer(string='Clicks')
    likes = fields.Integer(string='Likes')
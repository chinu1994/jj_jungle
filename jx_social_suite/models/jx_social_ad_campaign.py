# -*- coding: utf-8 -*-
from odoo import models, fields


class JxSocialAdCampaign(models.Model):
    _name = 'jx.social.ad.campaign'
    _description = 'JX Social Ad Campaign'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string='Campaign Name', required=True)

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
        ],
        string='Provider',
        required=True
    )

    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('paused', 'Paused'),
            ('completed', 'Completed'),
        ],
        string='Status',
        default='draft'
    )

    budget = fields.Float(string='Budget')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    external_campaign_id = fields.Char(string='External Campaign ID')
    notes = fields.Text(string='Notes')
# -*- coding: utf-8 -*-
from odoo import models, fields, api


class JxSocialTemplate(models.Model):
    _name = 'jx.social.template'
    _description = 'JX Social Post Template'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)

    post_type = fields.Selection(
        selection=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('video', 'Video'),
            ('carousel', 'Carousel'),
            ('link', 'Link'),
        ],
        string='Post Type',
        required=True,
        default='text'
    )

    content_text = fields.Text(string='Content Template')
    hashtags = fields.Char(string='Default Hashtags')
    link_url = fields.Char(string='Default Link URL')

    partner_id = fields.Many2one(
        'res.partner',
        string='Client (Optional)',
        domain="[('is_company', '=', True)]",
        help="Leave empty for global template"
    )

    active = fields.Boolean(default=True)

    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True
    )
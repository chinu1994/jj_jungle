# -*- coding: utf-8 -*-

from odoo import models, fields, api

class JxSocialPost(models.Model):
    _name = 'jx.social.post'
    _description = 'JX Social Post'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(
        string='Post Reference',
        default='/',
        readonly=True,
        copy=False
    )

    # ==================== Main Fields ====================
    partner_id = fields.Many2one(
        'res.partner',
        string='Client',
        required=True,
        ondelete='cascade',
        domain="[('is_company', '=', True)]",
        help="Client this post belongs to"
    )

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
        default='text',
        help="Drives composer validation logic"
    )

    content_text = fields.Text(
        string='Content',
        help="The post caption/body (sanitised before publish)"
    )

    media_ids = fields.Many2many(
        'ir.attachment',
        string='Media',
        help="Uploaded media files"
    )

    link_url = fields.Char(
        string='Link URL',
        help="Link to attach to post (used for UTM tracking)"
    )

    hashtags = fields.Char(
        string='Hashtags',
        help="Space-separated hashtags"
    )

    target_account_ids = fields.Many2many(
        'jx.social.account',
        string='Target Accounts',
        domain="[('partner_id', '=', partner_id), ('status', '=', 'connected')]",
        help="Accounts to publish this post to"
    )

    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('publishing', 'Publishing'),
            ('published', 'Published'),
            ('failed', 'Failed'),
            ('partial', 'Partially Published'),
        ],
        string='Status',
        default='draft',
        compute='_compute_status',
        store=True,
        help="Computed from schedule_ids states"
    )

    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True
    )

    template_id = fields.Many2one(
        'jx.social.template',
        string='From Template',
        help="Source template if created from template"
    )

    repurposed_from_id = fields.Many2one(
        'jx.social.post',
        string='Repurposed From',
        help="Original post if this is repurposed content",
        ondelete='set null'
    )

    # ==================== Relational Fields ====================
    schedule_ids = fields.One2many(
        'jx.social.schedule',
        'post_id',
        string='Schedules'
    )

    # ==================== Computed Methods ====================
    @api.depends('schedule_ids.state')
    def _compute_status(self):
        for post in self:
            if not post.schedule_ids:
                post.status = 'draft'
                continue

            states = post.schedule_ids.mapped('state')
            if all(s == 'published' for s in states):
                post.status = 'published'
            elif any(s == 'failed' for s in states) and any(s == 'published' for s in states):
                post.status = 'partial'
            elif any(s in ('failed', 'error') for s in states):
                post.status = 'failed'
            elif any(s == 'publishing' for s in states):
                post.status = 'publishing'
            elif any(s == 'scheduled' for s in states):
                post.status = 'scheduled'
            else:
                post.status = 'draft'

    # ==================== Create Override ====================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('jx.social.post') or '/'
        return super().create(vals_list)
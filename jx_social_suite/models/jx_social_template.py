from odoo import models, fields

class JxSocialTemplate(models.Model):
    _name = 'jx.social.template'
    _description = 'JX Social Template'

    name = fields.Char()
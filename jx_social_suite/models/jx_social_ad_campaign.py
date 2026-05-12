from odoo import models, fields

class JxSocialAdCampaign(models.Model):
    _name = 'jx.social.ad.campaign'
    _description = 'JX Social Ad Campaign'

    name = fields.Char()
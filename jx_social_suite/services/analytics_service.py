from odoo import models, api

class JxSocialAnalyticsService(models.AbstractModel):
    _name = 'jx.social.analytics.service'
    _description = 'Analytics Service (Stub)'

    @api.model
    def sync_all_analytics(self):
        return True
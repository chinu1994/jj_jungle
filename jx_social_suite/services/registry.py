# -*- coding: utf-8 -*-

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class JxSocialConnectorRegistry(models.AbstractModel):
    _name = 'jx.social.connector.registry'
    _description = 'JX Social Connector Registry'

    # ==================== Registry ====================
    CONNECTOR_REGISTRY = {
        'facebook': 'jx.social.connector.facebook',
        'instagram': 'jx.social.connector.instagram',
        'linkedin': 'jx.social.connector.linkedin',
        'tiktok': 'jx.social.connector.tiktok',
        'twitter': 'jx.social.connector.twitter',
        'google_business': 'jx.social.connector.google_business',
    }

    @api.model
    def get_connector(self, provider):
        if not provider:
            raise ValueError("Provider is missing!")

        model_name = self.CONNECTOR_REGISTRY.get(provider)

        if not model_name:
            raise ValueError(f'No connector found for provider: {provider}')

        return self.env[model_name]
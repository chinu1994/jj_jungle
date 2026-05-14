# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ==================== Instagram / Meta ====================
    jx_social_instagram_app_id = fields.Char(
        string='Instagram App ID',
        config_parameter='jx_social.instagram_app_id'
    )
    jx_social_instagram_app_secret = fields.Char(
        string='Instagram App Secret',
        config_parameter='jx_social.instagram_app_secret'
    )

    # ==================== Cloudinary ====================
    jx_social_cloudinary_cloud_name = fields.Char(
        string='Cloudinary Cloud Name',
        config_parameter='jx_social.cloudinary_cloud_name'
    )
    jx_social_cloudinary_api_key = fields.Char(
        string='Cloudinary API Key',
        config_parameter='jx_social.cloudinary_api_key'
    )
    jx_social_cloudinary_api_secret = fields.Char(
        string='Cloudinary API Secret',
        config_parameter='jx_social.cloudinary_api_secret'
    )
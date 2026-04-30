# -*- coding: utf-8 -*-
# Part of JJ Jungle. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class JJSocialStreamType(models.Model):
    """ Technical model that allows social module implementations ('social_facebook', 'social_twitter', ...)
    to introduce their own social stream types (eg: 'Page Posts' for Facebook, 'Keyword' for Twitter, ...) """

    _name = 'jj.social.stream.type'
    _description = 'JJ Social Stream Post'

    name = fields.Char("Name", readonly=True, required=True, translate=True)
    stream_type = fields.Char("Stream type name (technical)", readonly=True, required=True)
    media_id = fields.Many2one('jj.social.media', string="Social Media", readonly=True, required=True)

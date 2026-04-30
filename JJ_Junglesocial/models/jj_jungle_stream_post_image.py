# -*- coding: utf-8 -*-
# Part of JJ Jungle. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class JJSocialStreamAttachment(models.Model):
    """ A jj.social.stream.post.image represents an image that was shared with a jj.social.stream.post.
    It only contains the URL of the image on the related jj.social.media. """

    _name = 'jj.social.stream.post.image'
    _description = 'JJ Social Stream Post Image Attachment'

    image_url = fields.Char("Image URL", readonly=True, required=True)
    stream_post_id = fields.Many2one('jj.social.stream.post', string="Stream Post", ondelete="cascade")

# -*- coding: utf-8 -*-
from cryptography.fernet import Fernet
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """
    Auto-generate Fernet encryption key on first install.
    Only sets the key if it does not already exist.
    """
    from odoo.api import Environment
    import odoo

    with Environment.manage():
        env = Environment(cr, odoo.SUPERUSER_ID, {})
        params = env['ir.config_parameter']

        existing = params.get_param('jx_social.token_secret_key')
        if not existing:
            key = Fernet.generate_key().decode()
            params.set_param('jx_social.token_secret_key', key)
            _logger.info("JX Social Suite: Fernet encryption key auto-generated and saved.")
        else:
            _logger.info("JX Social Suite: Encryption key already exists — skipping.")

        # Create sequence for jx.social.post if not exists
        seq = env['ir.sequence'].search([('code', '=', 'jx.social.post')], limit=1)
        if not seq:
            env['ir.sequence'].create({
                'name': 'JX Social Post Reference',
                'code': 'jx.social.post',
                'prefix': 'POST/',
                'padding': 5,
                'number_increment': 1,
            })
            _logger.info("JX Social Suite: Post sequence created.")
# -*- coding: utf-8 -*-
from cryptography.fernet import Fernet
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    from odoo.api import Environment
    import odoo

    env = Environment(cr, odoo.SUPERUSER_ID, {})
    params = env['ir.config_parameter']

    existing = params.get_param('jx_social.token_secret_key')
    if not existing:
        key = Fernet.generate_key().decode()
        params.set_param('jx_social.token_secret_key', key)
        _logger.info("JX Social Suite: Fernet encryption key auto-generated.")
    else:
        _logger.info("JX Social Suite: Encryption key already exists — skipping.")

    # Sequence wala block hata diya - XML handle karega
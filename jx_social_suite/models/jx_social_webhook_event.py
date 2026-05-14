# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json
import logging

_logger = logging.getLogger(__name__)


class JxSocialWebhookEvent(models.Model):
    _name = 'jx.social.webhook.event'
    _description = 'JX Social Webhook Event'
    _order = 'received_at desc'
    _rec_name = 'event_type'

    provider = fields.Selection(
        selection=[
            ('facebook', 'Facebook'),
            ('instagram', 'Instagram'),
        ],
        string='Provider',
        required=True
    )

    event_type = fields.Char(string='Event Type', required=True)

    payload = fields.Text(
        string='Payload (JSON)',
        help="Raw webhook payload"
    )

    status = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('processed', 'Processed'),
            ('failed', 'Failed'),
            ('ignored', 'Ignored'),
        ],
        string='Status',
        default='pending',
        index=True
    )

    received_at = fields.Datetime(
        string='Received At',
        default=fields.Datetime.now,
        readonly=True
    )

    processed_at = fields.Datetime(string='Processed At', readonly=True)
    error_message = fields.Text(string='Error Message')

    def mark_processed(self):
        self.write({'status': 'processed', 'processed_at': fields.Datetime.now()})

    def mark_failed(self, error):
        self.write({'status': 'failed', 'error_message': str(error)[:500]})
# -*- coding: utf-8 -*-

from odoo import models


class JxSocialConnectorBase(models.AbstractModel):
    _name = 'jx.social.connector'
    _description = 'JX Social Provider Connector Abstract Interface'

    # ==================== Provider Capability Matrix ====================

    # Provider identifier (facebook, instagram, etc.)
    provider_name = None

    # Supported post types
    supported_post_types = []   # ['text', 'image', 'video', 'carousel', 'link']

    # Feature flags
    supports_organic = True
    supports_analytics = False
    supports_ads = False

    # Limits
    max_media_size_mb = 10

    # API Info (optional)
    api_version = None
    api_notes = ""

    # ==================== Interface Methods ====================

    def get_oauth_auth_url(self, state):
        """Return OAuth authorization URL"""
        raise NotImplementedError("Must implement get_oauth_auth_url()")

    def exchange_code_for_token(self, code, state):
        """Exchange OAuth code for access token"""
        raise NotImplementedError("Must implement exchange_code_for_token()")

    def refresh_token(self, token_record):
        """Refresh expired token"""
        raise NotImplementedError("Must implement refresh_token()")

    def revoke_token(self, token_record):
        """Revoke token from provider"""
        raise NotImplementedError("Must implement revoke_token()")

    def get_connected_accounts(self, token_record):
        """Fetch pages/accounts linked to token"""
        raise NotImplementedError("Must implement get_connected_accounts()")

    def publish_post(self, schedule_record):
        """
        Publish post to provider

        Must return:
        {
            'external_post_id': str,
            'published_at': datetime,
            'raw_response': dict
        }
        """
        raise NotImplementedError("Sprint 1 stub")

    def fetch_post_analytics(self, schedule_record, date_from, date_to):
        """
        Fetch analytics data for a post

        Must return:
        {
            'impressions': int,
            'reach': int,
            'engagement': int,
            'raw_data': dict
        }
        """
        raise NotImplementedError("Sprint 1 stub")

    # ==================== Validation ====================

    def validate_post(self, post_record):
        """
        Validate post before publishing

        Returns:
            list of errors (empty list = valid)
        """
        errors = []

        # Example basic validation (optional)
        if not post_record:
            errors.append("Post record is missing.")

        return errors
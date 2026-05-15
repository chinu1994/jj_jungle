# -*- coding: utf-8 -*-

from odoo import models, fields
from .connector_base import JxSocialConnectorBase

import requests
import base64
import hashlib
import time
import logging
from PIL import Image
import io

_logger = logging.getLogger(__name__)


class FacebookConnector(JxSocialConnectorBase):
    _name = 'jx.social.connector.facebook'

    provider_name = 'facebook'
    supported_post_types = ['text', 'image', 'link']
    supports_organic = True
    supports_analytics = True
    max_media_size_mb = 25

    # =========================================================
    # OAuth URL
    # =========================================================

    def get_oauth_auth_url(self, state: str) -> str:
        params = self.env['ir.config_parameter'].sudo()

        app_id = params.get_param('jx_social.facebook_app_id')
        base_url = params.get_param('web.base.url')

        redirect_uri = f"{base_url}/jx_social/oauth/callback/facebook"

        return (
            "https://www.facebook.com/v17.0/dialog/oauth"
            f"?client_id={app_id}"
            f"&redirect_uri={redirect_uri}"
            "&scope=pages_manage_posts,pages_read_engagement,pages_show_list,business_management"
            f"&state={state}"
        )

    # =========================================================
    # Exchange OAuth Code
    # =========================================================

    def exchange_code_for_token(self, code: str, state: str) -> dict:

        params = self.env['ir.config_parameter'].sudo()

        app_id = params.get_param('jx_social.facebook_app_id')
        app_secret = params.get_param('jx_social.facebook_app_secret')
        base_url = params.get_param('web.base.url')

        redirect_uri = f"{base_url}/jx_social/oauth/callback/facebook"

        # ==================== Short Token ====================

        short_resp = requests.get(
            "https://graph.facebook.com/v17.0/oauth/access_token",
            params={
                'client_id': app_id,
                'client_secret': app_secret,
                'redirect_uri': redirect_uri,
                'code': code
            },
            timeout=20
        ).json()

        _logger.error("Facebook short token response: %s", short_resp)

        short_token = short_resp.get('access_token')

        if not short_token:
            raise Exception(f"Failed to get short token: {short_resp}")

        # ==================== Long Token ====================

        long_resp = requests.get(
            "https://graph.facebook.com/v17.0/oauth/access_token",
            params={
                'grant_type': 'fb_exchange_token',
                'client_id': app_id,
                'client_secret': app_secret,
                'fb_exchange_token': short_token
            },
            timeout=20
        ).json()

        _logger.error("Facebook long token response: %s", long_resp)

        long_token = long_resp.get('access_token', short_token)

        return {
            'access_token': long_token,
            'refresh_token': None,
            'expires_at': False,
            'raw_response': long_resp
        }

    # =========================================================
    # Publish Post
    # =========================================================

    def publish_post(self, schedule_record):

        post = schedule_record.post_id
        account = schedule_record.social_account_id
        token = account.token_id

        if not token:
            raise Exception("No token found")

        access_token = token.get_decrypted_access_token()

        try:

            # ==================== IMAGE POST ====================

            if post.post_type == 'image':

                attachment = post.media_ids[0] if post.media_ids else None

                if not attachment:
                    raise Exception("No image attached")

                image_bytes = self._process_image(attachment)

                post_id = self._publish_photo(
                    page_id=account.account_external_id,
                    image_bytes=image_bytes,
                    caption=post.content_text or '',
                    access_token=access_token
                )

            # ==================== TEXT POST ====================

            else:

                post_id = self._publish_text_post(
                    page_id=account.account_external_id,
                    message=post.content_text or '',
                    access_token=access_token
                )

            return {
                'external_post_id': post_id,
                'published_at': fields.Datetime.now(),
                'raw_response': {}
            }

        except Exception as e:
            _logger.exception("Facebook Publish Failed: %s", str(e))
            raise

    # =========================================================
    # Text Post
    # =========================================================

    def _publish_text_post(self, page_id, message, access_token):

        url = f"https://graph.facebook.com/v17.0/{page_id}/feed"

        resp = requests.post(
            url,
            data={
                'message': message,
                'access_token': access_token
            },
            timeout=30
        ).json()

        _logger.error("Facebook text post response: %s", resp)

        if 'id' not in resp:
            raise Exception(f"Facebook text post failed: {resp}")

        return resp['id']

    # =========================================================
    # Image Post
    # =========================================================

    def _publish_photo(self, page_id, image_bytes, caption, access_token):

        url = f"https://graph.facebook.com/v17.0/{page_id}/photos"

        resp = requests.post(
            url,
            data={
                'caption': caption,
                'access_token': access_token
            },
            files={
                'source': ('post.jpg', image_bytes, 'image/jpeg')
            },
            timeout=60
        ).json()

        _logger.error("Facebook image post response: %s", resp)

        if 'post_id' not in resp and 'id' not in resp:
            raise Exception(f"Facebook image post failed: {resp}")

        return resp.get('post_id') or resp.get('id')

    # =========================================================
    # Process Image
    # =========================================================

    def _process_image(self, attachment):

        if not attachment.datas:
            raise Exception(f"Attachment '{attachment.name}' has no data")

        raw = base64.b64decode(attachment.datas)

        if len(raw) < 100:
            raise Exception("Invalid image data")

        img = Image.open(io.BytesIO(raw))
        img.verify()

        img = Image.open(io.BytesIO(raw))

        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = bg

        elif img.mode != 'RGB':
            img = img.convert('RGB')

        w, h = img.size

        if w < 320 or h < 320:
            scale = 320 / min(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=90)

        return buf.getvalue()

    # =========================================================
    # Get Connected Pages
    # =========================================================

    def get_connected_accounts(self, access_token):

        url = "https://graph.facebook.com/v17.0/me/accounts"

        resp = requests.get(
            url,
            params={
                'fields': 'id,name,access_token',
                'access_token': access_token
            },
            timeout=30
        ).json()

        _logger.error("Facebook pages response: %s", resp)

        if 'data' not in resp:
            raise Exception(f"Unable to fetch pages: {resp}")

        return resp['data']

    # =========================================================
    # Revoke Token
    # =========================================================

    def revoke_token(self, token_record):
        return True

    def refresh_token(self, token_record):
        raise NotImplementedError("Sprint 2")

    def fetch_post_analytics(self, schedule_record, date_from, date_to):
        raise NotImplementedError("Sprint 2")
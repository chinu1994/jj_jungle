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

class InstagramConnector(JxSocialConnectorBase):
    _name = 'jx.social.connector.instagram'

    provider_name = 'instagram'
    supported_post_types = ['image', 'video', 'carousel']
    supports_organic = True
    supports_analytics = True
    max_media_size_mb = 8

    def get_oauth_auth_url(self, state: str) -> str:
        params = self.env['ir.config_parameter'].sudo()
        app_id = params.get_param('jx_social.instagram_app_id')
        base_url = params.get_param('web.base.url')
        redirect_uri = f"{base_url}/jx_social/oauth/callback/instagram"

        return (
            "https://www.facebook.com/v17.0/dialog/oauth"
            f"?client_id={app_id}"
            f"&redirect_uri={redirect_uri}"
            "&scope=pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish,business_management"
            f"&state={state}"
        )

    def exchange_code_for_token(self, code: str, state: str) -> dict:
        params = self.env['ir.config_parameter'].sudo()
        app_id = params.get_param('jx_social.instagram_app_id')
        app_secret = params.get_param('jx_social.instagram_app_secret')
        base_url = params.get_param('web.base.url')
        redirect_uri = f"{base_url}/jx_social/oauth/callback/instagram"

        # Short-lived → Long-lived Token
        short_resp = requests.get("https://graph.facebook.com/v17.0/oauth/access_token", params={
            'client_id': app_id, 'client_secret': app_secret,
            'redirect_uri': redirect_uri, 'code': code
        }, timeout=20).json()

        _logger.error("Instagram short token response: %s", short_resp)  # Add this

        short_token = short_resp.get('access_token')
        if not short_token:
            raise Exception(f"Failed to get short token: {short_resp}")  # Show actual error

        long_resp = requests.get("https://graph.facebook.com/v17.0/oauth/access_token", params={
            'grant_type': 'fb_exchange_token',
            'client_id': app_id,
            'client_secret': app_secret,
            'fb_exchange_token': short_token
        }, timeout=20).json()

        long_token = long_resp.get('access_token', short_token)

        return {
            'access_token': long_token,
            'refresh_token': None,
            'expires_at': False,
            'raw_response': long_resp
        }

    def publish_post(self, schedule_record):
        post = schedule_record.post_id
        account = schedule_record.social_account_id
        token = account.token_id

        if not token:
            raise Exception("No token found")

        access_token = token.get_decrypted_access_token()

        try:
            attachment = post.media_ids[0] if post.media_ids else None
            if not attachment:
                raise Exception("No media attached")

            jpeg_bytes = self._process_image(attachment)
            image_url = self._upload_to_cloudinary(jpeg_bytes)

            creation_id = self._create_container(account.account_external_id, image_url, post.content_text or "", access_token)
            self._wait_for_container(creation_id, access_token)
            post_id = self._publish_container(account.account_external_id, creation_id, access_token)

            return {
                'external_post_id': post_id,
                'published_at': fields.Datetime.now(),
                'raw_response': {}
            }

        except Exception as e:
            _logger.error("Instagram Publish Failed: %s", str(e))
            raise

    # Helper Methods (Cleaned)
    def _process_image(self, attachment):
        _logger.error("DEBUG attachment: name=%s, mimetype=%s, datas type=%s, datas preview=%s",
                      attachment.name,
                      attachment.mimetype,
                      type(attachment.datas),
                      str(attachment.datas)[:100] if attachment.datas else 'EMPTY'
                      )

        if not attachment.datas:
            raise Exception(f"Attachment '{attachment.name}' has no data (datas is empty/False)")

        raw = base64.b64decode(attachment.datas)

        if len(raw) < 100:
            raise Exception(f"Decoded data too small ({len(raw)} bytes) - likely not a real image")

        # Re-open after verify
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

    def _upload_to_cloudinary(self, jpeg_bytes):
        params = self.env['ir.config_parameter'].sudo()
        cloud_name = params.get_param('jx_social.cloudinary_cloud_name')
        api_key = params.get_param('jx_social.cloudinary_api_key')
        api_secret = params.get_param('jx_social.cloudinary_api_secret')

        if not all([cloud_name, api_key, api_secret]):
            raise Exception("Cloudinary not configured")

        timestamp = str(int(time.time()))
        signature = hashlib.sha1(f"timestamp={timestamp}{api_secret}".encode()).hexdigest()

        resp = requests.post(
            f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
            data={'api_key': api_key, 'timestamp': timestamp, 'signature': signature},
            files={'file': ('post.jpg', jpeg_bytes, 'image/jpeg')},
            timeout=30
        ).json()

        if 'secure_url' not in resp:
            raise Exception("Cloudinary upload failed")
        return resp['secure_url']

    def _create_container(self, ig_id, image_url, caption, access_token):
        url = f"https://graph.facebook.com/v17.0/{ig_id}/media"
        resp = requests.post(url, params={
            'image_url': image_url,
            'caption': caption,
            'media_type': 'IMAGE',
            'access_token': access_token
        }, timeout=30).json()
        if 'id' not in resp:
            raise Exception(f"Container failed: {resp}")
        return resp['id']

    def _wait_for_container(self, creation_id, access_token, max_attempts=15):
        url = f"https://graph.facebook.com/v17.0/{creation_id}"
        for _ in range(max_attempts):
            time.sleep(4)
            resp = requests.get(url, params={'fields': 'status_code', 'access_token': access_token}, timeout=15).json()
            if resp.get('status_code') == 'FINISHED':
                return
            if resp.get('status_code') == 'ERROR':
                raise Exception("Container error")
        raise Exception("Timeout")

    def _publish_container(self, ig_id, creation_id, access_token):
        url = f"https://graph.facebook.com/v17.0/{ig_id}/media_publish"
        resp = requests.post(url, params={
            'creation_id': creation_id,
            'access_token': access_token
        }, timeout=30).json()
        if 'id' not in resp:
            raise Exception(f"Publish failed: {resp}")
        return resp['id']

    # Stubs
    def refresh_token(self, token_record): raise NotImplementedError("Sprint 2")
    def revoke_token(self, token_record): return True
    def get_connected_accounts(self, token_record): raise NotImplementedError("Sprint 2")
    def fetch_post_analytics(self, schedule_record, date_from, date_to): raise NotImplementedError("Sprint 2")
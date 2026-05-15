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
    supported_post_types = ['image', 'video', 'carousel', 'text', 'link']
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
            attachments = post.media_ids

            # ==================== CAPTION BUILD ====================
            caption_parts = []
            if post.content_text:
                caption_parts.append(post.content_text.strip())
            if post.link_url:
                caption_parts.append(post.link_url.strip())
            if post.hashtags:
                tags = []
                for tag in post.hashtags.strip().split():
                    tags.append(tag if tag.startswith('#') else f'#{tag}')
                caption_parts.append(' '.join(tags))
            final_caption = '\n\n'.join(caption_parts)

            # ==================== CAROUSEL POST ====================
            if post.post_type == 'carousel':
                if len(attachments) < 2:
                    raise Exception("Carousel requires at least 2 media items")

                media_ids = []
                for attachment in attachments:
                    mimetype = attachment.mimetype or ''
                    if mimetype.startswith('video/'):
                        media_id = self._upload_video_unpublished(
                            page_id=account.account_external_id,
                            attachment=attachment,
                            access_token=access_token
                        )
                    else:
                        image_bytes = self._process_image(attachment)
                        media_id = self._upload_photo_unpublished(
                            page_id=account.account_external_id,
                            image_bytes=image_bytes,
                            access_token=access_token
                        )
                    media_ids.append(media_id)

                post_id = self._publish_carousel(
                    page_id=account.account_external_id,
                    media_ids=media_ids,
                    caption=final_caption,
                    access_token=access_token
                )

            # ==================== VIDEO POST ====================
            elif attachments and (attachments[0].mimetype or '').startswith('video/'):
                post_id = self._publish_video(
                    page_id=account.account_external_id,
                    attachment=attachments[0],
                    caption=final_caption,
                    access_token=access_token
                )

            # ==================== IMAGE POST ====================
            elif attachments:
                image_bytes = self._process_image(attachments[0])
                post_id = self._publish_photo(
                    page_id=account.account_external_id,
                    image_bytes=image_bytes,
                    caption=final_caption,
                    access_token=access_token
                )

            # ==================== TEXT / LINK POST ====================
            else:
                post_id = self._publish_text_post(
                    page_id=account.account_external_id,
                    message=final_caption,
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

        _logger.info("Facebook text post response: %s", resp)

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

        _logger.info("Facebook image post response: %s", resp)

        if 'post_id' not in resp and 'id' not in resp:
            raise Exception(f"Facebook image post failed: {resp}")

        return resp.get('post_id') or resp.get('id')

    # =========================================================
    # Video Post (Published)
    # =========================================================

    def _publish_video(self, page_id, attachment, caption, access_token):
        url = f"https://graph.facebook.com/v17.0/{page_id}/videos"

        video_bytes = base64.b64decode(attachment.datas)

        resp = requests.post(
            url,
            data={
                'description': caption,
                'access_token': access_token
            },
            files={
                'source': (attachment.name, video_bytes, attachment.mimetype)
            },
            timeout=120
        ).json()

        _logger.info("Facebook video post response: %s", resp)

        if 'id' not in resp:
            raise Exception(f"Facebook video post failed: {resp}")

        return resp['id']

    # =========================================================
    # Carousel - Upload Image Unpublished
    # =========================================================

    def _upload_photo_unpublished(self, page_id, image_bytes, access_token):
        url = f"https://graph.facebook.com/v17.0/{page_id}/photos"

        resp = requests.post(
            url,
            data={
                'published': 'false',
                'access_token': access_token
            },
            files={
                'source': ('post.jpg', image_bytes, 'image/jpeg')
            },
            timeout=60
        ).json()

        _logger.info("Facebook unpublished photo response: %s", resp)

        if 'id' not in resp:
            raise Exception(f"Facebook unpublished photo upload failed: {resp}")

        return resp['id']

    # =========================================================
    # Carousel - Upload Video Unpublished (Cloudinary via URL)
    # =========================================================

    def _upload_video_unpublished(self, page_id, attachment, access_token):
        # Pehle Cloudinary pe upload karo public URL ke liye
        video_url = self._upload_video_to_cloudinary(attachment)

        url = f"https://graph.facebook.com/v17.0/{page_id}/videos"

        resp = requests.post(
            url,
            data={
                'file_url': video_url,
                'published': 'false',
                'access_token': access_token
            },
            timeout=120
        ).json()

        _logger.info("Facebook unpublished video response: %s", resp)

        if 'id' not in resp:
            raise Exception(f"Facebook unpublished video upload failed: {resp}")

        return resp['id']

    # =========================================================
    # Carousel - Final Publish
    # =========================================================

    def _publish_carousel(self, page_id, media_ids, caption, access_token):
        url = f"https://graph.facebook.com/v17.0/{page_id}/feed"

        data = {
            'message': caption,
            'access_token': access_token
        }

        for i, media_id in enumerate(media_ids):
            data[f'attached_media[{i}]'] = f'{{"media_fbid":"{media_id}"}}'

        resp = requests.post(url, data=data, timeout=60).json()

        _logger.info("Facebook carousel post response: %s", resp)

        if 'id' not in resp:
            raise Exception(f"Facebook carousel post failed: {resp}")

        return resp['id']

    # =========================================================
    # Cloudinary - Image Upload
    # =========================================================

    def _upload_image_to_cloudinary(self, jpeg_bytes):
        params = self.env['ir.config_parameter'].sudo()
        cloud_name = params.get_param('jx_social.cloudinary_cloud_name')
        api_key = params.get_param('jx_social.cloudinary_api_key')
        api_secret = params.get_param('jx_social.cloudinary_api_secret')

        if not all([cloud_name, api_key, api_secret]):
            raise Exception("Cloudinary not configured")

        timestamp = str(int(time.time()))
        signature = hashlib.sha1(
            f"timestamp={timestamp}{api_secret}".encode()
        ).hexdigest()

        resp = requests.post(
            f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
            data={'api_key': api_key, 'timestamp': timestamp, 'signature': signature},
            files={'file': ('post.jpg', jpeg_bytes, 'image/jpeg')},
            timeout=30
        ).json()

        _logger.info("Cloudinary image upload response: %s", resp)

        if 'secure_url' not in resp:
            raise Exception(f"Cloudinary image upload failed: {resp}")

        return resp['secure_url']

    # =========================================================
    # Cloudinary - Video Upload
    # =========================================================

    def _upload_video_to_cloudinary(self, attachment):
        params = self.env['ir.config_parameter'].sudo()
        cloud_name = params.get_param('jx_social.cloudinary_cloud_name')
        api_key = params.get_param('jx_social.cloudinary_api_key')
        api_secret = params.get_param('jx_social.cloudinary_api_secret')

        if not all([cloud_name, api_key, api_secret]):
            raise Exception("Cloudinary not configured")

        video_bytes = base64.b64decode(attachment.datas)
        timestamp = str(int(time.time()))
        signature = hashlib.sha1(
            f"timestamp={timestamp}{api_secret}".encode()
        ).hexdigest()

        resp = requests.post(
            f"https://api.cloudinary.com/v1_1/{cloud_name}/video/upload",
            data={'api_key': api_key, 'timestamp': timestamp, 'signature': signature},
            files={'file': (attachment.name, video_bytes, attachment.mimetype)},
            timeout=120
        ).json()

        _logger.info("Cloudinary video upload response: %s", resp)

        if 'secure_url' not in resp:
            raise Exception(f"Cloudinary video upload failed: {resp}")

        return resp['secure_url']

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
    # Stubs
    # =========================================================

    def revoke_token(self, token_record):
        return True

    def refresh_token(self, token_record):
        raise NotImplementedError("Sprint 2")

    def fetch_post_analytics(self, schedule_record, date_from, date_to):
        raise NotImplementedError("Sprint 2")
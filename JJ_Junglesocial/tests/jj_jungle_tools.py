# -*- coding: utf-8 -*-
# Part of JJ Jungle. See LICENSE file for full copyright and licensing details.

from contextlib import contextmanager
from unittest.mock import patch

try:
    from odoo.addons.social_facebook.models.jj_social_account import JJSocialAccountFacebook
    from odoo.addons.social_facebook.models.jj_social_live_post import JJSocialLivePostFacebook
    from odoo.addons.social_facebook.models.jj_social_stream import JJSocialStreamFacebook
    is_facebook_module_installed = True
except ImportError:
    is_facebook_module_installed = False

try:
    from odoo.addons.social_instagram.models.jj_social_account import JJSocialAccountInstagram
    from odoo.addons.social_instagram.models.jj_social_live_post import JJSocialLivePostInstagram
    from odoo.addons.social_instagram.models.jj_social_post import JJSocialPostInstagram
    from odoo.addons.social_instagram.models.jj_social_stream import JJSocialStreamInstagram
    is_instagram_module_installed = True
except ImportError:
    is_instagram_module_installed = False

try:
    from odoo.addons.social_linkedin.models.jj_social_account import JJSocialAccountLinkedin
    from odoo.addons.social_linkedin.models.jj_social_live_post import JJSocialLivePostLinkedin
    from odoo.addons.social_linkedin.models.jj_social_stream import JJSocialStreamLinkedIn
    is_linkedin_module_installed = True
except ImportError:
    is_linkedin_module_installed = False

try:
    from odoo.addons.social_twitter.models.jj_social_account import JJSocialAccountTwitter
    from odoo.addons.social_twitter.models.jj_social_live_post import JJSocialLivePostTwitter
    from odoo.addons.social_twitter.models.jj_social_stream import JJSocialStreamTwitter
    is_twitter_module_installed = True
except ImportError:
    is_twitter_module_installed = False

try:
    from odoo.addons.social_youtube.models.jj_social_account import JJSocialAccountYoutube
    from odoo.addons.social_youtube.models.jj_social_live_post import JJSocialLivePostYoutube
    from odoo.addons.social_youtube.models.jj_social_stream import JJSocialStreamYoutube
    is_youtube_module_installed = True
except ImportError:
    is_youtube_module_installed = False

@contextmanager
def mock_void_external_calls():
    """ Often, when testing social modules, we want to void all outgoing external calls methods.
    This method creates a handy context manager that will void all external calls at once. """
    with mock_void_external_calls_facebook(), \
         mock_void_external_calls_instagram(), \
         mock_void_external_calls_twitter(), \
         mock_void_external_calls_linkedin(), \
         mock_void_external_calls_youtube():
        yield

@contextmanager
def mock_void_external_calls_facebook():
    if is_facebook_module_installed:
        with patch.object(JJSocialAccountFacebook, '_compute_statistics', lambda x: None), \
             patch.object(JJSocialAccountFacebook, '_create_default_stream_facebook', lambda *args, **kwargs: None), \
             patch.object(JJSocialLivePostFacebook, '_post_facebook', lambda x: None), \
             patch.object(JJSocialStreamFacebook, '_fetch_stream_data', lambda x: None):
            yield
    else:
        yield

@contextmanager
def mock_void_external_calls_instagram():
    if is_instagram_module_installed:
        with patch.object(JJSocialAccountInstagram, '_compute_statistics', lambda x: None), \
             patch.object(JJSocialAccountInstagram, '_create_default_stream_instagram', lambda *args, **kwargs: None), \
             patch.object(JJSocialLivePostInstagram, '_post_instagram', lambda x: None), \
             patch.object(JJSocialPostInstagram, '_check_post_access', lambda x: False), \
             patch.object(JJSocialStreamInstagram, '_fetch_stream_data', lambda x: None):
            yield
    else:
        yield

@contextmanager
def mock_void_external_calls_linkedin():
    if is_linkedin_module_installed:
        with patch.object(JJSocialAccountLinkedin, '_compute_statistics', lambda x: None), \
             patch.object(JJSocialAccountLinkedin, '_create_default_stream_linkedin', lambda *args, **kwargs: None), \
             patch.object(JJSocialLivePostLinkedin, '_post_linkedin', lambda x: None), \
             patch.object(JJSocialStreamLinkedIn, '_fetch_stream_data', lambda x: None):
            yield
    else:
        yield

@contextmanager
def mock_void_external_calls_twitter():
    if is_twitter_module_installed:
        with patch.object(JJSocialAccountTwitter, '_compute_statistics', lambda x: None), \
             patch.object(JJSocialAccountTwitter, '_create_default_stream_twitter', lambda *args, **kwargs: None), \
             patch.object(JJSocialLivePostTwitter, '_post_twitter', lambda x: None), \
             patch.object(JJSocialStreamTwitter, '_fetch_stream_data', lambda x: None):
            yield
    else:
        yield

@contextmanager
def mock_void_external_calls_youtube():
    if is_youtube_module_installed:
        with patch.object(JJSocialAccountYoutube, '_create_default_stream_youtube', lambda *args, **kwargs: None), \
             patch.object(JJSocialLivePostYoutube, '_post_youtube', lambda x: None), \
             patch.object(JJSocialStreamYoutube, '_fetch_stream_data', lambda x: None):
            yield
    else:
        yield

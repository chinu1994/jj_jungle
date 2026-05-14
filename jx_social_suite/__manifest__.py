# -*- coding: utf-8 -*-
{
    'name': 'JX Social Suite',
    'version': '16.0.1.0.0',
    'category': 'Marketing',
    'summary': 'Social Media Management & Scheduling for Agencies',
    'description': """
        JX Social Suite - Complete Social Media Management System
        for JXungles Platform. Supports Instagram publishing,
        OAuth account connection, post scheduling, and analytics.
    """,
    'author': 'JXungles Platform',
    'website': '',
    'license': 'LGPL-3',

    'depends': [ 'base', 'mail', 'web',  'contacts', 'project', 'crm'],
    'data': [
        # Security (always first)
        'security/jx_social_groups.xml',
        'security/ir.model.access.csv',

        # Data
        'data/jx_social_cron.xml',

        # Views
        'views/jx_social_account_views.xml',
        'views/jx_social_post_views.xml',
        'views/jx_social_schedule_views.xml',
        'views/jx_social_settings_views.xml',
        'views/jx_social_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'jx_social_suite/static/src/**/*',
        ],
    },

    'post_init_hook': 'post_init_hook',

    'external_dependencies': {
        'python': ['cryptography', 'Pillow', 'requests'],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}
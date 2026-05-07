{
    'name': 'JX Social Suite',
    'version': '16.0.1.0.0',
    'category': 'Marketing',
    'summary': 'Social Media Management & Scheduling for Agencies',
    'description': """
        JX Social Suite - Complete Social Media Management System
        for JXungles Platform.
    """,
    'author': 'JJungles Platform',
    'depends': ['base', 'mail', 'web', 'contacts', 'project', 'crm'],
    'data': [
        'security/jx_social_groups.xml',
        'security/ir.model.access.csv',
        'data/jx_social_cron.xml',
        'views/jx_social_menu.xml',
        'views/jx_social_account_views.xml',
        'views/jx_social_post_views.xml',
        'views/jx_social_calendar_views.xml',
        'views/jx_social_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'jx_social_suite/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
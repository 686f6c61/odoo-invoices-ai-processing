{
    "name": "AI Processing",
    "version": "19.0.1.0.1",
    "category": "Accounting/Accounting",
    "summary": "Secure document AI for reviewable supplier-bill drafts",
    "description": """
Receive invoice attachments, classify and extract them with configurable AI
services, and stage the result for explicit accounting review.
""",
    "author": "00B",
    "license": "LGPL-3",
    "depends": ["account", "mail"],
    "external_dependencies": {
        "python": [
            "requests",
            "pypdf",
            "pypdfium2",
            "cryptography",
        ],
    },
    "data": [
        "security/ai_processing_security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/profile_views.xml",
        "views/model_views.xml",
        "views/inbox_views.xml",
        "views/account_move_views.xml",
        "views/menu_views.xml",
    ],
    "application": False,
    "installable": True,
}

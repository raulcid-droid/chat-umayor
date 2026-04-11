{
    'name': 'Mi Módulo',
    'version': '16.0.1.0.0',
    'summary': 'Descripción corta del módulo',
    'description': """
        Descripción larga del módulo.
    """,
    'author': 'Tu Nombre',
    'website': 'https://tuwebsite.com',
    'category': 'Uncategorized',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/mi_modelo_views.xml',
        'data/datos_iniciales.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

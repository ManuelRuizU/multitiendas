from django.db import migrations

CATEGORIAS = [
    {'nombre': 'Pizzas',       'emoji': '🍕', 'tipo_negocio': 'COMIDA', 'orden': 1},
    {'nombre': 'Sushi',        'emoji': '🍣', 'tipo_negocio': 'COMIDA', 'orden': 2},
    {'nombre': 'Hamburguesas', 'emoji': '🍔', 'tipo_negocio': 'COMIDA', 'orden': 3},
    {'nombre': 'Cafeterías',   'emoji': '☕', 'tipo_negocio': 'COMIDA', 'orden': 4},
    {'nombre': 'Pastelerías',  'emoji': '🧁', 'tipo_negocio': 'COMIDA', 'orden': 5},
    {'nombre': 'Minimarket',   'emoji': '🛒', 'tipo_negocio': 'RETAIL', 'orden': 6},
    {'nombre': 'Farmacias',    'emoji': '💊', 'tipo_negocio': 'RETAIL', 'orden': 7},
    {'nombre': 'Pollos',       'emoji': '🍗', 'tipo_negocio': 'COMIDA', 'orden': 8},
]


def add_categories(apps, schema_editor):
    CategoriaTienda = apps.get_model('plataforma_config', 'CategoriaTienda')
    for cat in CATEGORIAS:
        CategoriaTienda.objects.get_or_create(nombre=cat['nombre'], defaults=cat)


def remove_categories(apps, schema_editor):
    CategoriaTienda = apps.get_model('plataforma_config', 'CategoriaTienda')
    CategoriaTienda.objects.filter(nombre__in=[c['nombre'] for c in CATEGORIAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('plataforma_config', '0002_categoriatienda'),
    ]

    operations = [
        migrations.RunPython(add_categories, remove_categories),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plataforma_config', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriaTienda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True, verbose_name='Nombre')),
                ('emoji',  models.CharField(max_length=20, verbose_name='Emoji')),
                ('tipo_negocio', models.CharField(
                    choices=[
                        ('COMIDA',    'Comida y Bebidas'),
                        ('RETAIL',    'Tienda / Retail'),
                        ('SERVICIOS', 'Servicios'),
                        ('OTRO',      'Otro'),
                    ],
                    default='COMIDA',
                    max_length=20,
                    verbose_name='Tipo de negocio',
                )),
                ('orden',  models.PositiveIntegerField(default=0, verbose_name='Orden')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
            ],
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
                'ordering': ['orden', 'nombre'],
            },
        ),
    ]

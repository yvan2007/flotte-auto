# Generated data migration — types de document initiaux

from django.db import migrations


def creer_types_document(apps, schema_editor):
    TypeDocument = apps.get_model('flotte', 'TypeDocument')
    for ordre, libelle in enumerate([
        'Carte grise',
        'Assurance',
        'Contrôle technique (CT)',
        'Vignette',
        'Certificat de conformité (COC)',
        'Permis de circulation',
        'Carte verte',
    ], start=1):
        TypeDocument.objects.get_or_create(libelle=libelle, defaults={'ordre': ordre})


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('flotte', '0005_normes_flotte_conducteur_type_doc_ct_assurance_audit'),
    ]

    operations = [
        migrations.RunPython(creer_types_document, noop),
    ]

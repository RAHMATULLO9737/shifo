from django.db import migrations


def add_default_catalogs(apps, schema_editor):
    Specialty = apps.get_model('appointments', 'Specialty')
    Service = apps.get_model('appointments', 'Service')
    for name in ['Terapevt', 'Pediatr', 'Kardiolog', 'Nevrolog', 'Stomatolog', 'Dermatolog', 'Oftalmolog', 'Ginekolog', 'LOR']:
        Specialty.objects.get_or_create(name=name)
    for name, duration in [('Umumiy ko‘rik', 30), ('EKG', 15), ('UZI', 30), ('Laboratoriya tahlili', 20)]:
        Service.objects.get_or_create(name=name, defaults={'duration_minutes': duration, 'price': 0})


def remove_default_catalogs(apps, schema_editor):
    # Keep catalog entries when rolling back; administrators may already have edited them.
    pass


class Migration(migrations.Migration):
    dependencies = [('appointments', '0001_initial')]
    operations = [migrations.RunPython(add_default_catalogs, remove_default_catalogs)]

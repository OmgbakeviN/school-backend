from django.db import migrations

def seed_types(apps, schema_editor):
    AT = apps.get_model("assessments", "AssessmentType")
    AT.objects.get_or_create(code="CA1", defaults={"name":"Continuous Assessment 1", "weight":50, "is_active":True})
    AT.objects.get_or_create(code="CA2", defaults={"name":"Continuous Assessment 2", "weight":50, "is_active":True})

def unseed(apps, schema_editor):
    AT = apps.get_model("assessments", "AssessmentType")
    AT.objects.filter(code__in=["CA1","CA2"]).delete()

class Migration(migrations.Migration):

    dependencies = [
        ("assessments", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_types, reverse_code=unseed),
    ]

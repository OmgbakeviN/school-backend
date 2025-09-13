from django.db import migrations

def seed_levels_streams(apps, schema_editor):
    Level = apps.get_model("core", "Level")
    Stream = apps.get_model("core", "Stream")

    levels = [
        ("F1", "Form 1"),
        ("F2", "Form 2"),
        ("F3", "Form 3"),
        ("F4", "Form 4"),
        ("F5", "Form 5"),
        ("L6", "Lower Sixth"),
        ("U6", "Upper Sixth"),
    ]
    for code, name in levels:
        Level.objects.get_or_create(code=code, defaults={"name": name})

    for s in ["Science", "Arts"]:
        Stream.objects.get_or_create(name=s)

def unseed_levels_streams(apps, schema_editor):
    Level = apps.get_model("core", "Level")
    Stream = apps.get_model("core", "Stream")
    Level.objects.filter(code__in=["F1","F2","F3","F4","F5","L6","U6"]).delete()
    Stream.objects.filter(name__in=["Science","Arts"]).delete()

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_levels_streams, reverse_code=unseed_levels_streams),
    ]

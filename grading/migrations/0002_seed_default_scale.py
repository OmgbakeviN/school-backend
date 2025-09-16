from django.db import migrations

def seed(apps, schema_editor):
    AcademicYear = apps.get_model("core", "AcademicYear")
    GradeScale = apps.get_model("grading", "GradeScale")
    GradeBand = apps.get_model("grading", "GradeBand")

    year, _ = AcademicYear.objects.get_or_create(name="2025/2026")
    scale, _ = GradeScale.objects.get_or_create(name="Default A-F", year=year)

    bands = [
        ("A", 80, 100, 4.0),
        ("B", 70, 79, 3.0),
        ("C", 60, 69, 2.0),
        ("D", 50, 59, 1.0),
        ("E", 40, 49, 0.5),
        ("F", 0, 39, 0.0),
    ]
    for letter, lo, hi, gpa in bands:
        GradeBand.objects.get_or_create(
            scale=scale, letter=letter,
            defaults={"min_mark": lo, "max_mark": hi, "gpa": gpa}
        )

def unseed(apps, schema_editor):
    GradeScale = apps.get_model("grading", "GradeScale")
    GradeScale.objects.filter(name="Default A-F").delete()

class Migration(migrations.Migration):

    dependencies = [
        ("grading", "0001_initial"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]

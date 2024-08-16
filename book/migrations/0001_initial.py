# Generated by Django 4.2 on 2024-08-03 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Book",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=63)),
                ("author", models.CharField(max_length=63)),
                (
                    "cover",
                    models.CharField(
                        choices=[("Hard", "hard"), ("Soft", "soft")], max_length=4
                    ),
                ),
                ("inventory", models.PositiveIntegerField()),
                ("daily_fee", models.DecimalField(decimal_places=2, max_digits=5)),
            ],
        ),
    ]

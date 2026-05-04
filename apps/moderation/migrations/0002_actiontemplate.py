"""Sprint 5: ActionTemplate model for moderator one-click reasons."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("moderation", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActionTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("slug", models.SlugField(unique=True)),
                ("label", models.CharField(max_length=100)),
                ("action", models.CharField(
                    choices=[("approve", "Approve"), ("remove", "Remove")],
                    max_length=10,
                )),
                ("default_reason", models.TextField()),
                ("notify_template_id", models.CharField(
                    blank=True, help_text="Email template ID for notification.",
                    max_length=80,
                )),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Action template",
                "verbose_name_plural": "Action templates",
                "ordering": ["sort_order", "label"],
            },
        ),
    ]

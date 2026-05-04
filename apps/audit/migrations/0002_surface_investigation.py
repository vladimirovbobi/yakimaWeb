"""Add Surface.INVESTIGATION choice + widen `surface` column to 16 chars."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accesslog",
            name="surface",
            field=models.CharField(
                choices=[
                    ("admin", "Django admin"),
                    ("mod", "Moderator console"),
                    ("operator", "Operator dashboard"),
                    ("investigation", "Investigation"),
                ],
                db_index=True,
                max_length=16,
            ),
        ),
    ]

"""Add Brokerage model — autocomplete source for RealtorProfile.brokerage."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_vendor_wizard_state"),
    ]

    operations = [
        migrations.CreateModel(
            name="Brokerage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(db_index=True, max_length=200)),
                ("slug", models.SlugField(max_length=200, unique=True)),
                ("city", models.CharField(blank=True, max_length=80)),
                ("state", models.CharField(default="WA", max_length=2)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("website", models.URLField(blank=True)),
                ("license_number", models.CharField(blank=True, max_length=32)),
            ],
            options={
                "verbose_name": "Brokerage",
                "verbose_name_plural": "Brokerages",
                "ordering": ["name"],
            },
        ),
        migrations.AddIndex(
            model_name="brokerage",
            index=models.Index(fields=["state", "city", "name"],
                               name="accounts_br_state_32d5e8_idx"),
        ),
    ]

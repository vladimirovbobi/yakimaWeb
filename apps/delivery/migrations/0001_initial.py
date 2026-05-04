"""Initial migration for the delivery app — Sprint 6 schema.

Tables here are also accessed by the FastAPI delivery service via SQLAlchemy
(see ``delivery/db.py``). Django remains the source of truth for the schema.
"""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("marketplace", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeliveryPackage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(default="Delivery", max_length=240)),
                ("note", models.TextField(blank=True)),
                ("status", models.CharField(
                    choices=[("open", "Open"), ("finalized", "Finalized"), ("revoked", "Revoked")],
                    db_index=True, default="open", max_length=16,
                )),
                ("finalized_at", models.DateTimeField(blank=True, null=True)),
                ("buyer", models.ForeignKey(
                    on_delete=models.PROTECT,
                    related_name="delivery_packages_received",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("lead", models.ForeignKey(
                    on_delete=models.PROTECT,
                    related_name="delivery_packages",
                    to="marketplace.lead",
                )),
                ("vendor", models.ForeignKey(
                    on_delete=models.PROTECT,
                    related_name="delivery_packages_sent",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "db_table": "delivery_packages",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="deliverypackage",
            index=models.Index(fields=["lead", "status"], name="dp_lead_st_idx"),
        ),
        migrations.AddIndex(
            model_name="deliverypackage",
            index=models.Index(fields=["vendor", "-created_at"], name="dp_vendor_idx"),
        ),
        migrations.AddIndex(
            model_name="deliverypackage",
            index=models.Index(fields=["buyer", "-created_at"], name="dp_buyer_idx"),
        ),
        migrations.CreateModel(
            name="DeliveryFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("filename", models.CharField(max_length=240)),
                ("content_type", models.CharField(max_length=80)),
                ("size_bytes", models.PositiveBigIntegerField()),
                ("sha256", models.CharField(blank=True, max_length=64)),
                ("storage_path", models.CharField(max_length=512)),
                ("scan_status", models.CharField(
                    choices=[
                        ("pending", "Pending"),
                        ("clean", "Clean"),
                        ("infected", "Infected"),
                        ("skipped", "Skipped (no scanner configured)"),
                    ],
                    db_index=True, default="pending", max_length=16,
                )),
                ("package", models.ForeignKey(
                    on_delete=models.CASCADE,
                    related_name="files",
                    to="delivery.deliverypackage",
                )),
            ],
            options={
                "db_table": "delivery_files",
                "ordering": ["package", "filename"],
            },
        ),
        migrations.AddIndex(
            model_name="deliveryfile",
            index=models.Index(fields=["package"], name="df_pkg_idx"),
        ),
        migrations.CreateModel(
            name="DeliveryAccessLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("action", models.CharField(max_length=24)),
                ("ip_addr", models.CharField(blank=True, max_length=64)),
                ("user_agent", models.CharField(blank=True, max_length=240)),
                ("file", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.SET_NULL,
                    related_name="access_log",
                    to="delivery.deliveryfile",
                )),
                ("package", models.ForeignKey(
                    on_delete=models.CASCADE,
                    related_name="access_log",
                    to="delivery.deliverypackage",
                )),
                ("user", models.ForeignKey(
                    on_delete=models.PROTECT,
                    related_name="delivery_accesses",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "db_table": "delivery_access_log",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="deliveryaccesslog",
            index=models.Index(fields=["package", "-created_at"], name="dal_pkg_t_idx"),
        ),
        migrations.AddIndex(
            model_name="deliveryaccesslog",
            index=models.Index(fields=["user", "-created_at"], name="dal_user_t_idx"),
        ),
    ]

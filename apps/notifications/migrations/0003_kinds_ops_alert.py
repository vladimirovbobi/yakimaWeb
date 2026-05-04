"""Add OPS_ALERT + VENDOR_SUBMITTED to NotificationKind choices."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0002_rename_notif_user_created_idx_notificatio_user_id_05b4bc_idx_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("lead_received", "New lead received"),
                    ("lead_message", "New message on lead"),
                    ("lead_won", "Lead marked won"),
                    ("review_received", "New review"),
                    ("comment_reply", "Reply to your comment"),
                    ("forum_reply", "Reply on your thread"),
                    ("mod_decision", "Moderation decision"),
                    ("vendor_approved", "Vendor approved"),
                    ("vendor_submitted", "Vendor submitted for review"),
                    ("license_expiring_soon", "License expiring soon"),
                    ("ops_alert", "Operator alert"),
                ],
                db_index=True,
                max_length=32,
            ),
        ),
    ]

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('kind', models.CharField(
                    choices=[
                        ('lead_received', 'New lead received'),
                        ('lead_message', 'New message on lead'),
                        ('lead_won', 'Lead marked won'),
                        ('review_received', 'New review'),
                        ('comment_reply', 'Reply to your comment'),
                        ('forum_reply', 'Reply on your thread'),
                        ('mod_decision', 'Moderation decision'),
                        ('vendor_approved', 'Vendor approved'),
                        ('license_expiring_soon', 'License expiring soon'),
                    ],
                    db_index=True, max_length=32,
                )),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField(blank=True, max_length=2000)),
                ('link', models.CharField(blank=True, max_length=512)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('read_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('emailed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['user', '-created_at'], name='notif_user_created_idx'),
                    models.Index(fields=['user', 'read_at'], name='notif_user_read_idx'),
                ],
            },
        ),
    ]

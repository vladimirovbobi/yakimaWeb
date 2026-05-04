# Generated for Sprint 4 — LeadMessage gets ModeratableMixin + attachment.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0002_alter_service_hero_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='leadmessage',
            name='moderation_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('approved', 'Approved'),
                    ('removed', 'Removed'),
                    ('shadow', 'Shadow-banned'),
                ],
                db_index=True, default='pending', max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='leadmessage',
            name='moderation_score',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leadmessage',
            name='moderated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='leadmessage',
            name='attachment_url',
            field=models.URLField(blank=True),
        ),
        migrations.AddIndex(
            model_name='leadmessage',
            index=models.Index(fields=['lead', 'created_at'], name='mp_leadmsg_lead_idx'),
        ),
        migrations.AddIndex(
            model_name='leadmessage',
            index=models.Index(fields=['moderation_status'], name='mp_leadmsg_modstat_idx'),
        ),
    ]

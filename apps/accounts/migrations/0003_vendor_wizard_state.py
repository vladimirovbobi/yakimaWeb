# Generated for Sprint 4 — vendor onboarding wizard state.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_realtorprofile_headshot_alter_user_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendorprofile',
            name='about',
            field=models.TextField(blank=True, max_length=2000),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='contact_phone',
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='wizard_state',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='vendorprofile',
            name='submitted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

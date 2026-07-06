# Generated migration - Rename bluetooth_device_id to device_name

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projdjango', '0006_incidentreport'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='bluetooth_device_id',
            new_name='device_name',
        ),
    ]

# Generated by Django 5.2 on 2025-06-06 08:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sacco', '0004_saccoadminrequest_contact_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sacco',
            name='admin_requests',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sacco_admin_requests', to='sacco.saccoadminrequest'),
        ),
    ]

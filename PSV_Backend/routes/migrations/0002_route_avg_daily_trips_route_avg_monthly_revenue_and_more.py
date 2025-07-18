# Generated by Django 5.2 on 2025-06-28 09:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='avg_daily_trips',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='route',
            name='avg_monthly_revenue',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='route',
            name='fuel_cost_per_km',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6),
        ),
        migrations.AddField(
            model_name='route',
            name='maintenance_cost_per_month',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
        migrations.AddField(
            model_name='route',
            name='peak_hours_multiplier',
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=3),
        ),
        migrations.AddField(
            model_name='route',
            name='seasonal_variance',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=3),
        ),
    ]

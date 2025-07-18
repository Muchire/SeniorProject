# Generated by Django 5.2 on 2025-06-28 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sacco', '0007_sacco_avg_daily_trips_per_vehicle_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sacco',
            name='avg_daily_trips_per_vehicle',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='sacco',
            name='avg_vehicle_monthly_earnings',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='sacco',
            name='commission_rate',
            field=models.DecimalField(blank=True, decimal_places=2, default=10.0, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='sacco',
            name='daily_target',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='sacco',
            name='weekly_bonus_amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='sacco',
            name='weekly_bonus_threshold',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='saccofinancialmetrics',
            name='avg_revenue_per_vehicle',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='saccofinancialmetrics',
            name='insurance_costs',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='saccofinancialmetrics',
            name='licensing_costs',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='saccofinancialmetrics',
            name='maintenance_costs',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='saccofinancialmetrics',
            name='net_profit_margin',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='saccofinancialmetrics',
            name='operational_costs',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='saccofinancialmetrics',
            name='owner_average_profit',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='saccofinancialmetrics',
            name='revenue_growth_rate',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='saccofinancialmetrics',
            name='total_monthly_revenue',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=15, null=True),
        ),
    ]

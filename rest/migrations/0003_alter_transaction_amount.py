# Generated by Django 4.2.4 on 2023-10-09 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0002_alter_transaction_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
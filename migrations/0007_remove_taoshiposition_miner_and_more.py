# Generated by Django 4.1.7 on 2024-04-22 16:56

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("src", "0006_taoshiposition_miner_public_key"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="taoshiposition",
            name="miner",
        ),
        migrations.RemoveField(
            model_name="taoshiposition",
            name="miner_name",
        ),
    ]

# Generated by Django 5.2 on 2025-04-22 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_user_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content_type', models.CharField(max_length=20)),
                ('content_link', models.TextField(blank=True, null=True)),
                ('order_index', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'lessons',
                'ordering': ['order_index'],
                'managed': False,
            },
        ),
    ]

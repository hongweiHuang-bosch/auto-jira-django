from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0005_issueprocessresult_manual_review_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='IssueLearningMemory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_index', models.PositiveIntegerField(db_index=True)),
                ('issue_key', models.CharField(max_length=64)),
                ('review_status', models.CharField(blank=True, default='', max_length=20)),
                ('incorrect_conclusion', models.TextField(blank=True, default='')),
                ('correct_conclusion', models.TextField(blank=True, default='')),
                ('error_reason', models.TextField(blank=True, default='')),
                ('signal_summary', models.TextField(blank=True, default='')),
                ('memory_file_path', models.CharField(blank=True, default='', max_length=500)),
                ('memory_content_hash', models.CharField(blank=True, default='', max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at', '-id'],
                'unique_together': {('role_index', 'issue_key')},
            },
        ),
    ]

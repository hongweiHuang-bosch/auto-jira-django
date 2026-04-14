
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='AnalysisTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Jira分析任务', max_length=200)),
                ('status', models.CharField(choices=[('PENDING', 'PENDING'), ('RUNNING', 'RUNNING'), ('SUCCESS', 'SUCCESS'), ('FAILED', 'FAILED')], default='PENDING', max_length=20)),
                ('progress', models.PositiveIntegerField(default=0)),
                ('message', models.TextField(blank=True, default='')),
                ('total_groups', models.PositiveIntegerField(default=0)),
                ('finished_groups', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='IssueAnalysisResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issue_key', models.CharField(max_length=64)),
                ('summary', models.CharField(blank=True, default='', max_length=500)),
                ('model', models.CharField(blank=True, default='', max_length=100)),
                ('result_status', models.CharField(choices=[('SUCCESS', 'SUCCESS'), ('FAILED', 'FAILED'), ('MANUAL', 'MANUAL')], default='SUCCESS', max_length=20)),
                ('reply_text', models.TextField(blank=True, default='')),
                ('can_trace_image', models.CharField(blank=True, default='', max_length=500)),
                ('can_trace_image_url', models.CharField(blank=True, default='', max_length=500)),
                ('raw_signals', models.TextField(blank=True, default='')),
                ('has_commented_to_jira', models.BooleanField(default=False)),
                ('commented_at', models.DateTimeField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='analyzer.analysistask')),
            ],
            options={'ordering': ['-created_at'], 'unique_together': {('task', 'issue_key')}},
        ),
    ]

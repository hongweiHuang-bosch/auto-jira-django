from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0009_issueprocessresult_upper_comment_nullable'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoCycleState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_running', models.BooleanField(default=False)),
                ('interval_minutes', models.PositiveIntegerField(default=30)),
                ('stage', models.CharField(choices=[('STOPPED', 'STOPPED'), ('IDLE', 'IDLE'), ('FILTERING', 'FILTERING'), ('PROCESSING', 'PROCESSING'), ('NOTIFYING', 'NOTIFYING'), ('ERROR', 'ERROR')], default='STOPPED', max_length=20)),
                ('stop_requested', models.BooleanField(default=False)),
                ('last_started_at', models.DateTimeField(blank=True, null=True)),
                ('last_finished_at', models.DateTimeField(blank=True, null=True)),
                ('next_run_at', models.DateTimeField(blank=True, null=True)),
                ('last_error', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
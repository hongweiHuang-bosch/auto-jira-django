from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0003_filteredissuesnapshot_filtertask_issueprocesstask_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='issueprocessresult',
            name='manual_override_after_review',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='issueprocessresult',
            name='review_model',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='issueprocessresult',
            name='review_reason',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='issueprocessresult',
            name='review_status',
            field=models.CharField(
                choices=[('PENDING', 'PENDING'), ('PASS', 'PASS'), ('FAIL', 'FAIL')],
                default='PENDING',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='issueprocessresult',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='IssueReviewSample',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_index', models.PositiveIntegerField(db_index=True)),
                ('issue_key', models.CharField(max_length=64)),
                ('incorrect_conclusion', models.TextField()),
                ('correct_conclusion', models.TextField()),
                ('error_reason', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at', '-id'],
            },
        ),
    ]

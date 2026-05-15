from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0004_issueprocessresult_review_fields_and_reviewsample'),
    ]

    operations = [
        migrations.AddField(
            model_name='issueprocessresult',
            name='manual_error_reason',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='issueprocessresult',
            name='manual_correct_result',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='issueprocessresult',
            name='manual_review_saved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

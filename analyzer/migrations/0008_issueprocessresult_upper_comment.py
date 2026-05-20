from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0007_issuevalidationrun_issuevalidationcheck'),
    ]

    operations = [
        migrations.AddField(
            model_name='issueprocessresult',
            name='upper_comment',
            field=models.TextField(blank=True, default=''),
        ),
    ]

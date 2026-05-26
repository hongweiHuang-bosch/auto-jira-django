from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0010_autocyclestate'),
    ]

    operations = [
        migrations.AddField(
            model_name='issueprocesstask',
            name='feishu_notified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
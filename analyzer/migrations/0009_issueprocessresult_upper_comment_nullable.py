from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0008_issueprocessresult_upper_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issueprocessresult',
            name='upper_comment',
            field=models.TextField(blank=True, null=True, default=''),
        ),
    ]
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('analyzer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysistask',
            name='jql',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='analysistask',
            name='role_index',
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AddField(
            model_name='analysistask',
            name='role_label',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("picker", "0006_sync_semantic_role_tags"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="is_active",
        ),
    ]

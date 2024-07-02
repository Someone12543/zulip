# Generated by Django 5.0.5 on 2024-05-02 22:36

import django.db.models.deletion
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps


def create_presence_sequence_for_old_realms(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    Realm = apps.get_model("zerver", "Realm")
    PresenceSequence = apps.get_model("zerver", "PresenceSequence")

    max_id = Realm.objects.aggregate(models.Max("id"))["id__max"]
    if max_id is None:
        # Nothing to do if there are no rows yet.
        return

    BATCH_SIZE = 2000
    lower_bound = 0

    # Add a slop factor to make it likely we run past the end in case
    # of new rows created while we run. Races with realm creation are
    # pretty unlikely, and should throw an exception, so we should
    # catch them.
    max_id += BATCH_SIZE / 2

    while lower_bound < max_id:
        realm_ids = Realm.objects.filter(
            id__gt=lower_bound,
            id__lte=lower_bound + BATCH_SIZE,
            # Filter to realm whose PresenceSequence does not exist, to avoid
            # running into IntegrityError by trying to create duplicate PresenceSequence.
            presencesequence=None,
        ).values_list("id", flat=True)

        PresenceSequence.objects.bulk_create(
            PresenceSequence(realm_id=realm_id, last_update_id=0) for realm_id in realm_ids
        )

        lower_bound += BATCH_SIZE


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("zerver", "0526_user_presence_backfill_last_update_id_to_0"),
    ]

    operations = [
        migrations.CreateModel(
            name="PresenceSequence",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("last_update_id", models.PositiveBigIntegerField()),
                (
                    "realm",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to="zerver.realm"
                    ),
                ),
            ],
        ),
        migrations.RunPython(
            create_presence_sequence_for_old_realms,
            reverse_code=migrations.RunPython.noop,
            elidable=True,
        ),
    ]

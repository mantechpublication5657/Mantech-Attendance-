# Repairs databases where the (now-fixed) accounts.0002 migration already
# ran in its earlier, incomplete form: it dropped the FK constraints from
# Django's auto-created accounts_user_groups/accounts_user_user_permissions
# "through" tables (needed to unblock changing accounts_user.id to uuid),
# but never converted those tables' own user_id columns to match - leaving
# them stuck as bigint against the now-uuid accounts_user.id. This caused
# "operator does not exist: bigint = uuid" whenever Django touched a user's
# groups/permissions (e.g. saving a user in Django admin).
#
# Safe/idempotent on any database: only converts a column if it's still
# bigint (a database where 0002's fixed version already handled this
# correctly finds nothing to do here). Both tables are always empty at this
# point (no user has ever been assigned a group/permission through this
# app), so a fresh gen_random_uuid() per (nonexistent) row is fine.

from django.db import migrations


def fix_columns(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    for table in ('accounts_user_groups', 'accounts_user_user_permissions'):
        schema_editor.execute(f"""
            DO $$
            DECLARE
                col_type text;
            BEGIN
                SELECT data_type INTO col_type
                FROM information_schema.columns
                WHERE table_name = '{table}' AND column_name = 'user_id';

                IF col_type = 'bigint' THEN
                    ALTER TABLE {table} ALTER COLUMN user_id TYPE uuid USING gen_random_uuid();
                END IF;
            END $$;
        """)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_delete_otp'),
    ]

    operations = [
        migrations.RunPython(fix_columns, noop),
    ]

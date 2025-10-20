# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Proyecto(models.Model):
    codigo = models.CharField(db_column='Codigo', primary_key=True, max_length=20, db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.
    mina = models.CharField(db_column='Mina', max_length=50, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Proyecto'


class Registros(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)  # Field name made lowercase.
    id_sondaje_proyecto = models.ForeignKey('Sondajes', models.DO_NOTHING, db_column='Id_Sondaje_Proyecto', blank=True, null=True)  # Field name made lowercase.
    from_field = models.CharField(db_column='From', max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)  # Field name made lowercase. Field renamed because it was a Python reserved word.
    to = models.CharField(db_column='To', max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)  # Field name made lowercase.
    file_name = models.CharField(db_column='File_Name', max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)  # Field name made lowercase.
    file_name_2 = models.CharField(db_column='File_Name_2', max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Registros'


class Sondajes(models.Model):
    id_sondaje_proyecto = models.IntegerField(db_column='Id_Sondaje_Proyecto', primary_key=True)  # Field name made lowercase.
    hole_id = models.CharField(db_column='Hole_Id', max_length=255, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)  # Field name made lowercase.
    codigo = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='Codigo', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Sondajes'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150, db_collation='Modern_Spanish_CI_AS')

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS')
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS')

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128, db_collation='Modern_Spanish_CI_AS')
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150, db_collation='Modern_Spanish_CI_AS')
    first_name = models.CharField(max_length=150, db_collation='Modern_Spanish_CI_AS')
    last_name = models.CharField(max_length=150, db_collation='Modern_Spanish_CI_AS')
    email = models.CharField(max_length=254, db_collation='Modern_Spanish_CI_AS')
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(db_collation='Modern_Spanish_CI_AS', blank=True, null=True)
    object_repr = models.CharField(max_length=200, db_collation='Modern_Spanish_CI_AS')
    action_flag = models.SmallIntegerField()
    change_message = models.TextField(db_collation='Modern_Spanish_CI_AS')
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS')
    model = models.CharField(max_length=100, db_collation='Modern_Spanish_CI_AS')

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS')
    name = models.CharField(max_length=255, db_collation='Modern_Spanish_CI_AS')
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40, db_collation='Modern_Spanish_CI_AS')
    session_data = models.TextField(db_collation='Modern_Spanish_CI_AS')
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class RecortesLainasregistros(models.Model):
    id_laina = models.AutoField(db_column='Id_Laina', primary_key=True)  # Field name made lowercase.
    file_name_l = models.CharField(db_column='File_Name_L', max_length=250, db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.
    file_name_l2 = models.CharField(db_column='File_Name_L2', max_length=250, db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.
    id_sondaje_proyecto = models.ForeignKey('RecortesSondajes', models.DO_NOTHING, db_column='Id_Sondaje_Proyecto', blank=True, null=True)  # Field name made lowercase.
    fecha_hora = models.DateTimeField(db_column='Fecha_Hora')  # Field name made lowercase.
    usuario = models.CharField(max_length=254, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recortes_lainasregistros'


class RecortesProyecto(models.Model):
    codigo = models.CharField(db_column='Codigo', primary_key=True, max_length=250, db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.
    nombre = models.TextField(db_column='Nombre', db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.
    operacion = models.CharField(db_column='Operacion', max_length=250, db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.
    mina = models.CharField(db_column='Mina', max_length=250, db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.
    jefe = models.CharField(db_column='Jefe', max_length=250, db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'recortes_proyecto'


class RecortesRegistros(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)  # Field name made lowercase.
    from_field = models.FloatField(db_column='From')  # Field name made lowercase. Field renamed because it was a Python reserved word.
    to = models.FloatField(db_column='To')  # Field name made lowercase.
    file_name = models.CharField(db_column='File_Name', max_length=250, db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.
    file_name_2 = models.CharField(db_column='File_Name_2', max_length=250, db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.
    file_clean = models.CharField(db_column='File_Clean', max_length=250, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)  # Field name made lowercase.
    file_clean_2 = models.CharField(db_column='File_Clean_2', max_length=250, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)  # Field name made lowercase.
    id_sondaje_proyecto = models.ForeignKey('RecortesSondajes', models.DO_NOTHING, db_column='Id_Sondaje_Proyecto', blank=True, null=True)  # Field name made lowercase.
    procesado = models.BooleanField(db_column='Procesado')  # Field name made lowercase.
    fecha_hora = models.DateTimeField(db_column='Fecha_Hora')  # Field name made lowercase.
    usuario = models.CharField(max_length=254, db_collation='Modern_Spanish_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recortes_registros'


class RecortesSondajes(models.Model):
    id_sondaje_proyecto = models.AutoField(db_column='Id_Sondaje_Proyecto', primary_key=True)  # Field name made lowercase.
    hole_id = models.CharField(db_column='Hole_Id', max_length=210, db_collation='Modern_Spanish_CI_AS')  # Field name made lowercase.
    codigo = models.ForeignKey(RecortesProyecto, models.DO_NOTHING, db_column='Codigo', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'recortes_sondajes'


class Sysdiagrams(models.Model):
    name = models.CharField(max_length=128, db_collation='Modern_Spanish_CI_AS')
    principal_id = models.IntegerField()
    diagram_id = models.AutoField(primary_key=True)
    version = models.IntegerField(blank=True, null=True)
    definition = models.BinaryField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sysdiagrams'
        unique_together = (('principal_id', 'name'),)

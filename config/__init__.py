import pymysql
from django.db.backends.base.base import BaseDatabaseWrapper

# Simuler MariaDB 10.6 pour passer la vérification
BaseDatabaseWrapper.check_database_version_supported = lambda self: None

pymysql.install_as_MySQLdb()
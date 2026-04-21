import psycopg2
from psycopg2 import sql

class DatabaseConnection:
    _instance = None

    #CREDENCIALES DE POSTGRESQL LOCAL
    _host = "127.0.0.1"
    _port = "5432"
    _database = "ferrosoft_bd" 
    _user = "postgres"
    _password = "admin123"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            try:
                cls._instance.connection = psycopg2.connect(
                    host=cls._host,
                    port=cls._port,
                    database=cls._database,
                    user=cls._user,
                    password=cls._password
                )
                cls._instance.connection.autocommit = True
                print("Conexión a PostgreSQL establecida con éxito.")
            except Exception as e:
                print(f"Error al conectar a la base de datos: {e}")
                cls._instance = None
        return cls._instance

    def fetch_all(self, query, params=None):
        """Retorna múltiples registros (Ej: listar productos)"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error en fetch_all: {e}")
            return []

    def fetch_one(self, query, params=None):
        """Retorna un solo registro (Ej: buscar un usuario para el login)"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        except Exception as e:
            print(f"Error en fetch_one: {e}")
            return None

    def execute_query(self, query, params=None):
        """Ejecuta un INSERT, UPDATE o DELETE"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return True
        except Exception as e:
            print(f"Error en execute_query: {e}")
            return False
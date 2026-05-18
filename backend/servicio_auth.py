from backend.bd_conexion import DatabaseConnection

class AuthService:
    def __init__(self):
        self.db = DatabaseConnection()

    def login(self, username, pin):
        """
        Valida el usuario y PIN. 
        Retorna el objeto empleado si es exitoso, None si falla.
        """
        query = """
            SELECT id_empleado, nombre_completo, usuario, rol, estatus 
            FROM empleados 
            WHERE usuario = %s AND pin = %s AND estatus = TRUE
        """
        result = self.db.fetch_one(query, (username, pin))
        
        if result:
            
            return {
                "id": result[0],
                "nombre": result[1],
                "usuario": result[2],
                "rol": result[3]
            }
        return None
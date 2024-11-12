# database.py
import pyodbc
import logging
from datetime import datetime, date, time
from config import SQL_SERVER, DATABASE, USERNAME, PASSWORD

def get_db_connection():
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'
        logging.info(f"Intentando conectar a la base de datos: {SQL_SERVER}/{DATABASE}")
        connection = pyodbc.connect(conn_str)
        logging.info("Conexión exitosa a la base de datos")
        return connection
    except pyodbc.Error as e:
        logging.error(f"Error al conectar a la base de datos: {e}")
        return None

       
def get_ventas_data():
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return {}
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                Folio,
                ISNULL(Estado, '') as Estado,
                ISNULL(CveCte, '') as CveCte,
                ISNULL(Cliente, '') as Cliente,
                ISNULL(Fecha, '') as Fecha,
                ISNULL(Hora, '') as Hora,
                ISNULL(Total, 0) as Total,
                ISNULL(Restante, 0) as Restante,
                ISNULL(FechaPago, '') as FechaPago,
                ISNULL(Paga, 0) as Paga,
                ISNULL(Cambio, '') as Cambio,
                ISNULL(Ticket, '') as Ticket,
                ISNULL(Condiciones, '') as Condiciones,
                ISNULL(FechaProg, '') as FechaProg,
                ISNULL(Corte, 0) as Corte,
                ISNULL(Vendedor, '') as Vendedor,
                ISNULL(ComoPago, '') as ComoPago,
                ISNULL(DiasCred, 0) as DiasCred,
                ISNULL(IntCred, '') as IntCred,
                ISNULL(Articulos, '') as Articulos,
                ISNULL(BarCuenta, '') as BarCuenta,
                ISNULL(BarMesero, '') as BarMesero,
                ISNULL(NotasAdicionales, '') as NotasAdicionales,
                ISNULL(IdBarCuenta, '') as IdBarCuenta,
                ISNULL(Bitacora, '') as Bitacora,
                ISNULL(Anticipo, 0) as Anticipo,
                ISNULL(FolioPago, '') as FolioPago,
                ISNULL(SaldoCliente, 0) as SaldoCliente,
                ISNULL(Caja, 0) as Caja
            FROM Ventas
            WHERE Estado != 'PAGADA'
            AND Estado != 'CANCELADA'
            AND Estado IS NOT NULL
            AND Restante > 0
        """
        
        logging.info(f"Ejecutando consulta SQL para Ventas: {query}")
        cursor.execute(query)
        results = cursor.fetchall()
        
        logging.info(f"Registros de Ventas encontrados: {len(results)}")
        
        def format_date(date_value):
            if date_value:
                if isinstance(date_value, (datetime, date)):
                    return date_value.strftime('%Y-%m-%d')
                try:
                    return datetime.strptime(str(date_value), '%Y-%m-%d').strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    logging.warning(f"Valor de fecha no válido: {date_value}")
                    return ""
            return ""

        def format_time(time_value):
            if time_value:
                if isinstance(time_value, time):
                    return time_value.strftime('%H:%M:%S')
                try:
                    if isinstance(time_value, str):
                        return time_value
                    return datetime.strptime(str(time_value), '%H:%M:%S').strftime('%H:%M:%S')
                except (ValueError, TypeError):
                    logging.warning(f"Valor de hora no válido: {time_value}")
                    return ""
            return ""
        
        ventas_data = {
            str(row.Folio): {
                "estado": row.Estado.strip() if row.Estado else "",
                "cveCte": row.CveCte.strip() if row.CveCte else "",
                "cliente": row.Cliente.strip() if row.Cliente else "",
                "fecha": format_date(row.Fecha),
                "hora": format_time(row.Hora),
                "total": float(row.Total) if row.Total else 0.0,
                "restante": float(row.Restante) if row.Restante else 0.0,
                "fechaPago": format_date(row.FechaPago),
                "paga": float(row.Paga) if row.Paga else 0.0,
                "cambio": row.Cambio.strip() if row.Cambio else "",
                "ticket": row.Ticket.strip() if row.Ticket else "",
                "condiciones": row.Condiciones.strip() if row.Condiciones else "",
                "fechaProg": format_date(row.FechaProg),
                "corte": int(row.Corte) if row.Corte else 0,
                "vendedor": row.Vendedor.strip() if row.Vendedor else "",
                "comoPago": row.ComoPago.strip() if row.ComoPago else "",
                "diasCorte": int(row.DiasCred) if row.DiasCred else 0,
                "intCred": row.IntCred.strip() if row.IntCred else "",
                "articulos": row.Articulos.strip() if row.Articulos else "",
                "barCuenta": row.BarCuenta.strip() if row.BarCuenta else "",
                "barMesero": row.BarMesero.strip() if row.BarMesero else "",
                "notasAdicionales": row.NotasAdicionales.strip() if row.NotasAdicionales else "",
                "idBarCuenta": row.IdBarCuenta.strip() if row.IdBarCuenta else "",
                "bitacora": row.Bitacora.strip() if row.Bitacora else "",
                "anticipo": float(row.Anticipo) if row.Anticipo else 0.0,
                "folioPago": row.FolioPago.strip() if row.FolioPago else "",
                "saldoCliente": float(row.SaldoCliente) if row.SaldoCliente else 0.0,
                "caja": int(row.Caja) if row.Caja else 0
            } for row in results
        }
        
        logging.info(f"Datos de Ventas procesados exitosamente. Total de registros: {len(ventas_data)}")
        return ventas_data
        
    except pyodbc.Error as e:
        logging.error(f"Error al obtener datos de Ventas: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error inesperado al procesar datos de Ventas: {e}")
        return {}
    finally:
        logging.info("Cerrando conexión a la base de datos")
        conn.close()
#States     

def update_client_states(client_id: str, states: dict = None) -> bool:
    """
    Actualiza o crea un registro en la tabla ClientsStates para un cliente específico.
    Si states es None, crea un registro con valores predeterminados False.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si el cliente ya existe
        check_query = """
            SELECT client_id
            FROM dbo.ClientsStates 
            WHERE client_id = ?
        """
        cursor.execute(check_query, (client_id,))
        exists = cursor.fetchone() is not None
        
        if states is None:
            states = {
                "day1": False,
                "day2": False,
                "day3": False,
                "dueday": False,
                "promisePage": False
            }
        
        if exists:
            # Actualizar registro existente
            update_query = """
                UPDATE dbo.ClientsStates 
                SET day1 = ?, 
                    day2 = ?, 
                    day3 = ?, 
                    dueday = ?, 
                    promisePage = ?
                WHERE client_id = ?
            """
            cursor.execute(update_query, 
                         (states["day1"], states["day2"], states["day3"], 
                          states["dueday"], states["promisePage"], client_id))
        else:
            # Insertar nuevo registro
            insert_query = """
                INSERT INTO dbo.ClientsStates 
                (client_id, day1, day2, day3, dueday, promisePage)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, 
                         (client_id, states["day1"], states["day2"], states["day3"], 
                          states["dueday"], states["promisePage"]))
        
        conn.commit()
        logging.info(f"Estados del cliente {client_id} actualizados exitosamente")
        return True
        
    except pyodbc.Error as e:
        logging.error(f"Error al actualizar estados del cliente {client_id}: {e}")
        return False
    finally:
        conn.close()

def delete_client_states(client_id: str) -> bool:
    """
    Elimina el registro de un cliente de la tabla ClientsStates.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        delete_query = """
            DELETE FROM dbo.ClientsStates 
            WHERE client_id = ?
        """
        cursor.execute(delete_query, (client_id,))
        conn.commit()
        logging.info(f"Estados del cliente {client_id} eliminados exitosamente")
        return True
        
    except pyodbc.Error as e:
        logging.error(f"Error al eliminar estados del cliente {client_id}: {e}")
        return False
    finally:
        conn.close()

def get_client_states() -> dict:
    """
    Obtiene todos los registros de la tabla ClientsStates.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return {}
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT client_id, day1, day2, day3, dueday, promisePage
            FROM dbo.ClientsStates
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        return {
            str(row.client_id): {
                "day1": bool(row.day1),
                "day2": bool(row.day2),
                "day3": bool(row.day3),
                "dueday": bool(row.dueday),
                "promisePage": bool(row.promisePage)
            } for row in results
        }
        
    except pyodbc.Error as e:
        logging.error(f"Error al obtener estados de los clientes: {e}")
        return {}
    finally:
        conn.close()

# database.py
def get_client_notes(client_id: str = None) -> dict:
    """
    Obtiene las notas de un cliente específico o de todos los clientes.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return {}
    
    try:
        cursor = conn.cursor()
        if client_id:
            query = """
                SELECT client_id, note_text, created_at
                FROM dbo.Notes
                WHERE client_id = ?
                ORDER BY created_at DESC
            """
            cursor.execute(query, (client_id,))
        else:
            query = """
                SELECT client_id, note_text, created_at
                FROM dbo.Notes
                ORDER BY client_id, created_at DESC
            """
            cursor.execute(query)
            
        results = cursor.fetchall()
        
        # Agrupar notas por cliente
        notes_data = {}
        for row in results:
            client_key = str(row.client_id)
            if client_key not in notes_data:
                notes_data[client_key] = []
            
            notes_data[client_key].append({
                "text": row.note_text,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
        
        if client_id:
            return notes_data.get(str(client_id), [])
        return notes_data
        
    except pyodbc.Error as e:
        logging.error(f"Error al obtener notas de clientes: {e}")
        return {} if client_id is None else []
    finally:
        conn.close()

def get_client_data(self, clave_id):
        """Obtiene los datos específicos de un cliente"""
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            query = """
                SELECT client_id, day1, day2, day3, dueday, promisePage
                FROM dbo.ClientsStates
                WHERE client_id = ?
            """
            cursor.execute(query, (clave_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "ID Cliente": row.client_id,
                    "Día 1": "Sí" if row.day1 else "No",
                    "Día 2": "Sí" if row.day2 else "No",
                    "Día 3": "Sí" if row.day3 else "No",
                    "Día Vencimiento": "Sí" if row.dueday else "No",
                    "Promesa de Pago": "Activa" if row.promisePage else "Inactiva"
                }
            return None
            
        except pyodbc.Error as e:
            logging.error(f"Error al obtener datos del cliente {clave_id}: {e}")
            return None
        finally:
            conn.close()
            

#wsp
def update_client_states_wsp(client_id: str, states: dict = None) -> bool:
    """
    Actualiza o crea un registro en la tabla ClientsStates para un cliente específico.
    Si states es None, crea un registro con valores predeterminados False.
    
    Parameters:
    client_id (str): ID del cliente a actualizar.
    states (dict): Diccionario con los nuevos estados del cliente.
    
    Returns:
    bool: True si la actualización fue exitosa, False en caso contrario.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si el cliente ya existe
        check_query = """
            SELECT client_id
            FROM dbo.ClientsStates 
            WHERE client_id = ?
        """
        cursor.execute(check_query, (client_id,))
        exists = cursor.fetchone() is not None
        
        if states is None:
            states = {
                "day1": False,
                "day2": False,
                "day3": False,
                "dueday": False,
                "promisePage": False
            }
        
        if exists:
            # Actualizar registro existente
            update_query = """
                UPDATE dbo.ClientsStates 
                SET day1 = ?, 
                    day2 = ?, 
                    day3 = ?, 
                    dueday = ?, 
                    promisePage = ?
                WHERE client_id = ?
            """
            cursor.execute(update_query, 
                         (states["day1"], states["day2"], states["day3"], 
                          states["dueday"], states["promisePage"], client_id))
        else:
            # Insertar nuevo registro
            insert_query = """
                INSERT INTO dbo.ClientsStates 
                (client_id, day1, day2, day3, dueday, promisePage)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, 
                         (client_id, states["day1"], states["day2"], states["day3"], 
                          states["dueday"], states["promisePage"]))
        
        conn.commit()
        logging.info(f"Estados del cliente {client_id} actualizados exitosamente")
        return True
        
    except pyodbc.Error as e:
        logging.error(f"Error al actualizar estados del cliente {client_id}: {e}")
        return False
    finally:
        conn.close()
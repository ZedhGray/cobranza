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

def get_clients_data():
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo establecer conexión con la base de datos")
        return {}
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                Clave,
                ISNULL(Estado, '') as Estado,
                ISNULL(Fecha, '') as Fecha,
                ISNULL(Nombre, '') as Nombre,
                ISNULL(Direccion, '') as Direccion,
                ISNULL(Telefono1, '') as Telefono1,
                ISNULL(Telefono2, '') as Telefono2,
                ISNULL(Descripcion, '') as Descripcion,
                ISNULL(Email, '') as Email,
                ISNULL(Referencia, '') as Referencia,
                ISNULL(Obs, '') as Obs,
                ISNULL(Credito, 0) as Credito,
                ISNULL(MontoCredito, 0) as MontoCredito,
                ISNULL(DiasCredito, 0) as DiasCredito,
                ISNULL(InteresCredito, '') as InteresCredito,
                ISNULL(Saldo, 0) as Saldo,
                ISNULL(NL, 0) as NL,
                ISNULL(NC, '') as NC,
                ISNULL(Membresia, '') as Membresia,
                ISNULL(Nivel, 0) as Nivel,
                ISNULL(Modificado, '') as Modificado,
                ISNULL(Et1, '') as Et1,
                ISNULL(LineaDeCredito, '') as LineaDeCredito
            FROM Clientes4
            WHERE Saldo > 0
                   
        """
        
        logging.info(f"Ejecutando consulta SQL: {query}")
        cursor.execute(query)
        results = cursor.fetchall()
        
        logging.info(f"Registros encontrados: {len(results)}")
        def format_date(date_value):
            if date_value:
                if isinstance(date_value, (datetime, date)):
                    return date_value.strftime('%Y-%m-%d')
                try:
                    # Intenta convertir si es string
                    return datetime.strptime(str(date_value), '%Y-%m-%d').strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    logging.warning(f"Valor de fecha no válido: {date_value}")
                    return ""
            return ""
        
        clients_data = {
            str(row.Clave): {
                "estado": row.Estado.strip() if row.Estado else "",
                "fecha": format_date(row.Fecha),
                "nombre": row.Nombre.strip() if row.Nombre else "",
                "direccion": row.Direccion.strip() if row.Direccion else "",
                "telefono1": row.Telefono1.strip() if row.Telefono1 else "",
                "telefono2": row.Telefono2.strip() if row.Telefono2 else "",
                "descripcion": row.Descripcion.strip() if row.Descripcion else "",
                "email": row.Email.strip() if row.Email else "",
                "referencia": row.Referencia.strip() if row.Referencia else "",
                "obs": row.Obs.strip() if row.Obs else "",
                "credito": bool(row.Credito),
                "montoCredito": float(row.MontoCredito) if row.MontoCredito else 0.0,
                "diasCredito": int(row.DiasCredito) if row.DiasCredito else 0,
                "interesCredito": row.InteresCredito.strip() if row.InteresCredito else "",
                "saldo": float(row.Saldo) if row.Saldo else 0.0,
                "nl": int(row.NL) if row.NL else 0,
                "nc": row.NC.strip() if row.NC else "",
                "membresia": format_date(row.Membresia),
                "nivel": int(row.Nivel) if row.Nivel else 0,
                "modificado": format_date(row.Modificado),
                "et1": row.Et1.strip() if row.Et1 else "",
                "lineaDeCredito": row.LineaDeCredito.strip() if row.LineaDeCredito else ""
            } for row in results
        }
        
        logging.info(f"Datos procesados exitosamente. Total de registros: {len(clients_data)}")
        return clients_data
        
    except pyodbc.Error as e:
        logging.error(f"Error al obtener datos de clientes: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error inesperado al procesar datos: {e}")
        return {}
    finally:
        logging.info("Cerrando conexión a la base de datos")
        conn.close()
        
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
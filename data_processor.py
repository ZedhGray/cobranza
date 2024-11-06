import logging
import json
import os
from database import get_clients_data, get_ventas_data

def update_combined_json(combined_data):
    """
    Actualiza el archivo JSON con los datos combinados de clientes y ventas.
    """
    try:
        # Guardar en archivo JSON
        output_file = 'clientes_ventas_combined.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=4)
            
        logging.info(f"Datos combinados guardados exitosamente en {output_file}")
        
    except Exception as e:
        logging.error(f"Error al guardar datos combinados: {e}")

def update_line_json(combined_data):
    """
    Actualiza el archivo "line.json" con la información de la propiedad "timeline" de cada cliente.
    """
    try:
        line_data = {}
        
        # Verificar si el archivo "line.json" existe
        output_file = 'line.json'
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                line_data = json.load(f)
        
        # Actualizar o agregar datos de "timeline" para cada cliente
        for client_key, client_info in combined_data.items():
            if client_key not in line_data:
                line_data[client_key] = {
                    "day3": False,
                    "day2": False,
                    "day1": False,
                    "dueDay": False,
                    "promisePage": False,                    
                }
        
        # Eliminar los client_id que ya no existen en los datos combinados
        for client_id in list(line_data.keys()):
            if client_id not in combined_data:
                del line_data[client_id]
                logging.info(f"Eliminando client_id '{client_id}' de 'line.json' porque ya no existe en los datos combinados")
        
        # Guardar el archivo "line.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(line_data, f, ensure_ascii=False, indent=4)
        
        logging.info(f"Datos de 'timeline' guardados exitosamente en {output_file}")
        
    except Exception as e:
        logging.error(f"Error al guardar datos en 'line.json': {e}")
        
def update_json_data(new_client_data, client_json_file='clientes_data.json', timeline_json_file='line.json'):
    try:
        logging.info(f"Iniciando actualización de los archivos JSON: {client_json_file}, {timeline_json_file}")

        # Actualizar archivo JSON de clientes
        if os.path.exists(client_json_file):
            logging.info(f"Archivo JSON de clientes existente encontrado: {client_json_file}")
            with open(client_json_file, 'r', encoding='utf-8') as f:
                current_client_data = json.load(f)
        else:
            logging.info(f"No se encontró archivo JSON de clientes existente, se creará uno nuevo: {client_json_file}")
            current_client_data = {}

        # Agregar nuevos clientes sin modificar los existentes
        for client_id, client_info in new_client_data.items():
            if client_id not in current_client_data:
                current_client_data[client_id] = client_info

        with open(client_json_file, 'w', encoding='utf-8') as f:
            json.dump(current_client_data, f, ensure_ascii=False, indent=4)

        logging.info(f"Datos de clientes actualizados exitosamente. Total de registros: {len(current_client_data)}")

        # Actualizar archivo JSON de timeline
        if os.path.exists(timeline_json_file):
            logging.info(f"Archivo JSON de timeline existente encontrado: {timeline_json_file}")
            with open(timeline_json_file, 'r', encoding='utf-8') as f:
                current_timeline_data = json.load(f)
        else:
            logging.info(f"No se encontró archivo JSON de timeline existente, se creará uno nuevo: {timeline_json_file}")
            current_timeline_data = {}

        # Agregar nuevos datos de timeline sin modificar los existentes
        for client_id, timeline_info in new_client_data.items():
            if 'timeline' in timeline_info and client_id not in current_timeline_data:
                current_timeline_data[client_id] = timeline_info['timeline']

        with open(timeline_json_file, 'w', encoding='utf-8') as f:
            json.dump(current_timeline_data, f, ensure_ascii=False, indent=4)

        logging.info(f"Datos de timeline actualizados exitosamente. Total de registros: {len(current_timeline_data)}")

    except Exception as e:
        logging.error(f"Error al actualizar los archivos JSON: {e}")
        raise

def combine_client_sales_data() -> dict:
    """
    Combina los datos de clientes con sus ventas correspondientes.
    Retorna un diccionario donde cada cliente tiene sus datos y una lista de sus ventas.
    """
    try:
        logging.info("Iniciando proceso de combinación de datos de clientes y ventas")

        # Obtener datos de clientes y ventas
        clients_data = get_clients_data()
        ventas_data = get_ventas_data()

        if not clients_data:
            logging.error("No se pudieron obtener datos de clientes")
            return {}

        if not ventas_data:
            logging.warning("No se encontraron datos de ventas")

        # Crear estructura combinada
        combined_data = clients_data.copy()

        # Procesar cada cliente y agregar sus ventas
        for client_key, client_info in clients_data.items():
            combined_data[client_key]['ventas'] = []
            for venta_key, venta_info in ventas_data.items():
                if venta_info['cveCte'] == client_key:
                    combined_data[client_key]['ventas'].append(venta_info)

        logging.info(f"Proceso de combinación completado. Clientes procesados: {len(combined_data)}")
        return combined_data

    except Exception as e:
        logging.error(f"Error al combinar datos de clientes y ventas: {e}")
        return {}
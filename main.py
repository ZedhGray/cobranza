# main.py
import logging
from logging.handlers import RotatingFileHandler
import json
import os
from database import get_clients_data, get_ventas_data
from data_processor import update_combined_json, update_line_json, combine_client_sales_data

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = RotatingFileHandler('cobranza.log', maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)

def update_json_data(new_data, json_file='clientes_data.json'):
    try:
        logging.info(f"Iniciando actualización del archivo JSON: {json_file}")
        
        if os.path.exists(json_file):
            logging.info(f"Archivo JSON existente encontrado")
            with open(json_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            logging.info(f"Datos actuales cargados: {len(current_data)} registros")
        else:
            logging.info(f"No se encontró archivo JSON existente, se creará uno nuevo")
            current_data = {}
        
        current_data.update(new_data)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=4)
        
        logging.info(f"Datos actualizados exitosamente. Total de registros: {len(current_data)}")
        
    except Exception as e:
        logging.error(f"Error al actualizar el archivo JSON: {e}")
        raise

def main():
    try:
        setup_logging()
        logging.info("=== Iniciando actualización de datos ===")
        
        # Procesar datos combinados
        combined_data = combine_client_sales_data()
        update_combined_json(combined_data)
        
        # Actualizar datos de "timeline"
        update_line_json(combined_data)
        
        logging.info("=== Proceso completado ===")
            
    except Exception as e:
        logging.error(f"Error en el proceso principal: {e}")
        logging.info("=== Proceso completado con errores ===")
        raise
        
if __name__ == "__main__":
    main()
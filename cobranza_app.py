import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json
from datetime import datetime
import re
import os
import subprocess
from database import get_client_states, update_client_states, get_db_connection, get_clients_data
import logging
from tkinter import messagebox
from typing import Dict, Optional
import pyodbc

def extract_ticket_number(ticket_text):
    """Extract ticket number from ticket text using regex"""
    if not ticket_text:
        return "N/A"
    ticket_text = str(ticket_text)
    match = re.search(r'TICKET:(\d+)', ticket_text)
    if match:
        return match.group(1)
    # If it's just a number, return it directly
    return ticket_text if ticket_text.isdigit() else "N/A"

class DetalleClienteWindow:
    def __init__(self, parent, client_data, client_id):
        self.top = tk.Toplevel(parent)
        self.client_data = client_data
        self.client_id = client_id
        self.setup_window()
        #self.create_content()
        self.top.title("Detalle de Cliente")
        self.top.geometry("1000x800")
        
        # Colores
        self.COLOR_ROJO = "#E31837"
        self.COLOR_NEGRO = "#333333"
        self.COLOR_BLANCO = "#FFFFFF"
        self.COLOR_GRIS = "#F5F5F5"
        self.COLOR_GRIS_CLARO = "#EFEFEF"
            
        # Configurar la ventana
        self.top.configure(bg=self.COLOR_GRIS_CLARO)
            
        # Initialize timeline_container as instance variable
        self.timeline_container = None

        # Crear los frames principales
        self.create_cliente_frame()
        timeline_frame = self.create_timeline_frame(client_id)
        self.create_adeudo_frame()
        
     
    def setup_window(self):
        """Configura la ventana de detalles"""
        self.top.title(f"Detalle Cliente - {self.client_data.get('nombre', 'Sin nombre')}")
        window_width = 800
        window_height = 600
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.top.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
    def create_cliente_frame(self):
        # Frame principal del cliente
        client_frame = tk.LabelFrame(self.top, text="CLIENTE", 
                                    font=("Arial", 16, "bold"),
                                    bg=self.COLOR_BLANCO)
        client_frame.pack(fill='x', padx=20, pady=(20,10))
        
        # Contenedor para la información del cliente
        info_container = tk.Frame(client_frame, bg=self.COLOR_BLANCO)
        info_container.pack(fill='x', padx=20, pady=10)
        
        # Información del cliente con validación de datos
        self.create_info_field(info_container, "Número de Cliente:", str(self.client_id))
        self.create_info_field(info_container, "Nombre:", self.client_data.get('nombre', 'N/A'))
        self.create_info_field(info_container, "Teléfono:", self.client_data.get('telefono1', 'N/A'))
        self.create_info_field(info_container, "Telefono Referencia:", self.client_data.get('telefono2', 'N/A'))
        self.create_info_field(info_container, "Dirección:", self.client_data.get('direccion', 'N/A'))
        self.create_info_field(info_container, "Saldo:", f"${self.client_data.get('saldo', 0):,.2f}")
        self.create_info_field(info_container, "Crédito:", "Sí" if self.client_data.get('credito') else "No")
        
        # Estado (punto rojo y "Activo")
        estado_frame = tk.Frame(client_frame, bg=self.COLOR_BLANCO)
        estado_frame.place(relx=1.0, x=-20, y=10, anchor='ne')
        
        estado_label = tk.Label(estado_frame,
                            text="●",
                            font=("Arial", 12),
                            fg=self.COLOR_ROJO,
                            bg=self.COLOR_BLANCO)
        estado_label.pack(side='left')
        
        estado_texto = tk.Label(estado_frame,
                            text=self.client_data.get('estado', 'ACTIVO'),
                            font=("Arial", 12),
                            fg=self.COLOR_ROJO,
                            bg=self.COLOR_BLANCO)
        estado_texto.pack(side='left', padx=5)

    def create_info_field(self, parent, label, value):
        frame = tk.Frame(parent, bg=self.COLOR_BLANCO)
        frame.pack(fill='x', pady=5)
        
        # Etiqueta
        label_widget = tk.Label(frame,
                            text=label,
                            font=("Arial", 10, "bold"),
                            bg=self.COLOR_BLANCO)
        label_widget.pack(side='left', padx=(0,5))
        
        # Valor
        value_widget = tk.Label(frame,
                            text=str(value),
                            font=("Arial", 10),
                            bg=self.COLOR_BLANCO)
        value_widget.pack(side='left', padx=(0,10))
        
        return frame
       
    def create_timeline_frame(self, client_id):
        """Crea el frame principal de la timeline con datos del cliente específico"""
        timeline_frame = tk.LabelFrame(self.top, text="LINEA DE TIEMPO",
                                    font=("Arial", 16, "bold"),
                                    bg=self.COLOR_BLANCO)
        timeline_frame.pack(fill='x', padx=20, pady=10)

        # Canvas y Scrollbar para manejar el scroll
        self.canvas = tk.Canvas(timeline_frame, bg=self.COLOR_BLANCO, height=300)
        scrollbar = ttk.Scrollbar(timeline_frame, orient="vertical", command=self.canvas.yview)
        
        # Frame interior
        interior_frame = tk.Frame(self.canvas, bg=self.COLOR_BLANCO)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar canvas y scrollbar
        self.canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")
        
        canvas_frame = self.canvas.create_window((0, 0), window=interior_frame, anchor="nw")

        # Contenedor para datos y línea vertical
        data_container = tk.Frame(interior_frame, bg=self.COLOR_BLANCO)
        data_container.pack(fill='both', expand=True, padx=(30, 10))

        # Línea vertical
        line = tk.Frame(data_container, width=2, bg=self.COLOR_ROJO)
        line.pack(side='left', fill='y', padx=(0, 20))

        # Obtener datos del cliente
        client_data = self.get_client_data(client_id)
        if client_data:
            # Mostrar los datos del cliente
            data_frame = tk.Frame(data_container, bg=self.COLOR_BLANCO)
            data_frame.pack(fill='x', expand=True)
            
            for key, value in client_data.items():
                if key != "promisePage":  # No mostrar el estado de promesa como etiqueta
                    label = tk.Label(data_frame, 
                                text=f"{key}: {value}",
                                bg=self.COLOR_BLANCO,
                                font=("Arial", 12))
                    label.pack(anchor='w', pady=2)

            # Sección de notas
            notes_section = tk.Frame(data_container, bg=self.COLOR_BLANCO)
            notes_section.pack(fill='x', expand=True, pady=(20, 0))
            
            # Título de la sección de notas
            notes_title = tk.Label(notes_section,
                                text="NOTAS",
                                font=("Arial", 14, "bold"),
                                bg=self.COLOR_BLANCO)
            notes_title.pack(anchor='w', pady=(0, 10))
            
            # Obtener y mostrar las notas
            notes = self.get_client_notes(client_id)
            if notes:
                for note in notes:
                    note_frame = tk.Frame(notes_section, bg=self.COLOR_BLANCO)
                    note_frame.pack(fill='x', pady=5)
                    
                    timestamp = note['timestamp'].strftime("%d/%m/%Y %H:%M")
                    note_label = tk.Label(note_frame,
                                        text=f"{timestamp} - {note['text']}",
                                        bg=self.COLOR_BLANCO,
                                        font=("Arial", 11),
                                        wraplength=500,
                                        justify='left')
                    note_label.pack(anchor='w')
            else:
                # Mostrar mensaje cuando no hay notas
                no_notes_label = tk.Label(notes_section,
                                        text="No hay notas registradas",
                                        bg=self.COLOR_BLANCO,
                                        font=("Arial", 11, "italic"))
                no_notes_label.pack(anchor='w', pady=5)

        # Frame para botones
        buttons_frame = tk.Frame(timeline_frame, bg=self.COLOR_BLANCO)
        buttons_frame.pack(pady=5)

        # Botón para notas (ahora habilitado)
        add_note_btn = tk.Button(buttons_frame,
                                text="+ Agregar Nota",
                                font=("Arial", 10),
                                command=self.show_note_dialog)
        add_note_btn.pack(side='left', padx=5)

        # Configurar el botón de promesa según el estado actual
        promise_state = client_data.get("promisePage", False) if client_data else False
        button_text = "En Promesa" if promise_state else "Promesa"
        button_color = "red" if promise_state else "white"
        
        # Botón para promesa de pago
        self.promise_btn = tk.Button(buttons_frame,
                                text=button_text,
                                font=("Arial", 10),
                                bg=button_color,
                                command=lambda: self.toggle_promise(client_id))
        self.promise_btn.pack(side='left', padx=5)

        # Configurar scroll con mousewheel
        def _on_mousewheel(event):
            try:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass

        timeline_frame.bind('<Enter>', lambda e: self.canvas.bind_all("<MouseWheel>", _on_mousewheel))
        timeline_frame.bind('<Leave>', lambda e: self.canvas.unbind_all("<MouseWheel>"))

        # Configurar el ajuste del tamaño del canvas cuando el interior cambia
        def _configure_interior(event):
            size = (interior_frame.winfo_reqwidth(), interior_frame.winfo_reqheight())
            self.canvas.config(scrollregion="0 0 %s %s" % size)
            if interior_frame.winfo_reqwidth() != self.canvas.winfo_width():
                self.canvas.config(width=interior_frame.winfo_reqwidth())
        
        interior_frame.bind('<Configure>', _configure_interior)

        # Guardar referencia al client_id actual
        self.current_client_id = client_id
        
        return timeline_frame

    def get_client_data(self, client_id):
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
            cursor.execute(query, (client_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "ID Cliente": row.client_id,
                    "Día 1": "Sí" if row.day1 else "No",
                    "Día 2": "Sí" if row.day2 else "No",
                    "Día 3": "Sí" if row.day3 else "No",
                    "Día Vencimiento": "Sí" if row.dueday else "No",
                    "promisePage": bool(row.promisePage)
                }
            return None
            
        except pyodbc.Error as e:
            logging.error(f"Error al obtener datos del cliente {client_id}: {e}")
            return None
        finally:
            conn.close()

    def toggle_promise(self, client_id):
        """Alterna el estado de la promesa de pago"""
        try:
            conn = get_db_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            # Obtener el estado actual
            cursor.execute("SELECT promisePage FROM dbo.ClientsStates WHERE client_id = ?", (client_id,))
            current_state = cursor.fetchone()
            
            if current_state is not None:
                # Cambiar al estado opuesto
                new_state = not bool(current_state.promisePage)
                cursor.execute("""
                    UPDATE dbo.ClientsStates 
                    SET promisePage = ?
                    WHERE client_id = ?
                """, (new_state, client_id))
                conn.commit()
                
                # Actualizar solo el botón sin recargar toda la vista
                new_text = "En Promesa" if new_state else "Promesa"
                new_color = "red" if new_state else "white"
                self.promise_btn.configure(text=new_text, bg=new_color)
                
        except pyodbc.Error as e:
            logging.error(f"Error al actualizar promesa de pago: {e}")
        finally:
            if conn:
                conn.close()

    def refresh_timeline(self, client_id):
        """Actualiza la vista de la timeline"""
        # Limpiar el frame actual
        for widget in self.canvas.winfo_children():
            widget.destroy()
        
        # Volver a crear la timeline con los datos actualizados
        self.create_timeline_frame(client_id)  
    #================================================================
    def get_client_notes(self, client_id):
        """Obtiene todas las notas de un cliente específico"""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            query = """
                SELECT id, note_text, created_at
                FROM Notes
                WHERE client_id = ?
                ORDER BY created_at DESC
            """
            cursor.execute(query, (client_id,))
            notes = []
            for row in cursor.fetchall():
                notes.append({
                    'id': row.id,
                    'text': row.note_text,
                    'timestamp': row.created_at
                })
            return notes
                
        except pyodbc.Error as e:
            logging.error(f"Error al obtener notas del cliente {client_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def save_note_to_db(self, note_text):
        """Guarda una nueva nota en la base de datos"""
        conn = get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            # Modified query to exclude created_at from the INSERT statement
            query = """
                INSERT INTO Notes (client_id, note_text)
                VALUES (?, ?)
            """
            cursor.execute(query, (self.current_client_id, note_text))
            conn.commit()
            return True
                
        except pyodbc.Error as e:
            logging.error(f"Error al guardar nota: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def show_note_dialog(self):
        """Muestra un diálogo para agregar una nueva nota"""
        dialog = tk.Toplevel(self.top)
        dialog.title("Agregar Nota")
        dialog.geometry("400x200")
        dialog.configure(bg=self.COLOR_BLANCO)
        
        # Hacer la ventana modal
        dialog.transient(self.top)
        dialog.grab_set()
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg=self.COLOR_BLANCO)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Campo de texto para la nota
        note_label = tk.Label(main_frame,
                            text="Nota:",
                            font=("Arial", 10, "bold"),
                            bg=self.COLOR_BLANCO)
        note_label.pack(anchor='w')
        
        note_text = tk.Text(main_frame,
                        height=4,
                        font=("Arial", 10))
        note_text.pack(fill='x', pady=(5, 10))
        
        def save():
            text = note_text.get("1.0", "end-1c").strip()
            if not text:
                messagebox.showwarning("Advertencia", "Por favor ingrese una nota")
                return
                
            if self.save_note_to_db(text):
                dialog.destroy()
                self.refresh_timeline(self.current_client_id)
            else:
                messagebox.showerror("Error", "No se pudo guardar la nota")
        
        # Botones
        button_frame = tk.Frame(main_frame, bg=self.COLOR_BLANCO)
        button_frame.pack(fill='x', pady=(10, 0))
        
        cancel_btn = tk.Button(button_frame,
                            text="Cancelar",
                            command=dialog.destroy)
        cancel_btn.pack(side='right', padx=5)
        
        save_btn = tk.Button(button_frame,
                            text="Guardar",
                            command=save,
                            bg=self.COLOR_ROJO,
                            fg=self.COLOR_BLANCO)
        save_btn.pack(side='right', padx=5)
            
    def create_adeudo_frame(self):
        """
        Crea el frame que muestra la información de adeudos del cliente
        """
        # Frame principal de adeudos
        adeudo_frame = tk.LabelFrame(self.top, text="ADEUDOS",
                                    font=("Arial", 16, "bold"),
                                    bg=self.COLOR_BLANCO)
        adeudo_frame.pack(fill='x', padx=20, pady=(0,20))

        # Contenedor para la información de adeudos
        info_container = tk.Frame(adeudo_frame, bg=self.COLOR_BLANCO)
        info_container.pack(fill='x', padx=20, pady=10)

        try:
            # Obtener información de adeudos
            adeudos = self.get_adeudos_info()

            if not adeudos:
                # Si no hay adeudos, mostrar mensaje
                no_adeudos = tk.Label(info_container,
                                    text="No hay adeudos registrados",
                                    font=("Arial", 10, "italic"),
                                    bg=self.COLOR_BLANCO)
                no_adeudos.pack(pady=10)
                return

            # Crear encabezados
            headers_frame = tk.Frame(info_container, bg=self.COLOR_BLANCO)
            headers_frame.pack(fill='x', pady=(0,5))

            headers = ["Fecha", "Concepto", "Monto", "Estado"]
            for header in headers:
                header_label = tk.Label(headers_frame,
                                    text=header,
                                    font=("Arial", 10, "bold"),
                                    bg=self.COLOR_BLANCO)
                header_label.pack(side='left', padx=10, expand=True)

            # Línea separadora
            separator = ttk.Separator(info_container, orient='horizontal')
            separator.pack(fill='x', pady=5)

            # Mostrar adeudos
            for adeudo in adeudos:
                self.create_adeudo_row(info_container, adeudo)

            # Total
            total_frame = tk.Frame(info_container, bg=self.COLOR_BLANCO)
            total_frame.pack(fill='x', pady=(10,0))

            total_label = tk.Label(total_frame,
                                text="Total:",
                                font=("Arial", 12, "bold"),
                                bg=self.COLOR_BLANCO)
            total_label.pack(side='right', padx=(0,10))

            total = sum(adeudo.get('monto', 0) for adeudo in adeudos)
            total_amount = tk.Label(total_frame,
                                text=f"${total:,.2f}",
                                font=("Arial", 12, "bold"),
                                fg=self.COLOR_ROJO,
                                bg=self.COLOR_BLANCO)
            total_amount.pack(side='right', padx=(0,50))

        except Exception as e:
            logging.error(f"Error al crear frame de adeudos: {str(e)}")
            error_label = tk.Label(info_container,
                                text=f"Error al cargar adeudos: {str(e)}",
                                font=("Arial", 10),
                                fg="red",
                                bg=self.COLOR_BLANCO)
            error_label.pack(pady=10)

    def create_adeudo_row(self, container, adeudo):
        """
        Crea una fila para mostrar un adeudo
        Args:
            container: Frame contenedor
            adeudo (dict): Diccionario con la información del adeudo
        """
        row_frame = tk.Frame(container, bg=self.COLOR_GRIS_CLARO)
        row_frame.pack(fill='x', pady=2)

        # Fecha
        fecha = adeudo.get('fecha', 'N/A')
        fecha_label = tk.Label(row_frame,
                            text=fecha,
                            font=("Arial", 10),
                            bg=self.COLOR_GRIS_CLARO)
        fecha_label.pack(side='left', padx=10, expand=True)

        # Concepto
        concepto = adeudo.get('concepto', 'N/A')
        concepto_label = tk.Label(row_frame,
                                text=concepto,
                                font=("Arial", 10),
                                bg=self.COLOR_GRIS_CLARO)
        concepto_label.pack(side='left', padx=10, expand=True)

        # Monto
        monto = adeudo.get('monto', 0)
        monto_label = tk.Label(row_frame,
                            text=f"${monto:,.2f}",
                            font=("Arial", 10),
                            bg=self.COLOR_GRIS_CLARO)
        monto_label.pack(side='left', padx=10, expand=True)

        # Estado
        estado = adeudo.get('estado', 'Pendiente')
        estado_label = tk.Label(row_frame,
                            text=estado,
                            font=("Arial", 10),
                            bg=self.COLOR_GRIS_CLARO)
        estado_label.pack(side='left', padx=10, expand=True)

    def get_adeudos_info(self):
        """
        Obtiene la información de adeudos del cliente desde la base de datos
        Returns:
            list: Lista de diccionarios con la información de adeudos
        """
        try:
            # TODO: Implementar la conexión real a la base de datos
            # Por ahora retornamos datos de ejemplo
            return [
                {
                    'fecha': '2024-01-01',
                    'concepto': 'Mensualidad Enero',
                    'monto': 1500.00,
                    'estado': 'Pendiente'
                },
                {
                    'fecha': '2024-02-01',
                    'concepto': 'Mensualidad Febrero',
                    'monto': 1500.00,
                    'estado': 'Pendiente'
                }
            ]
        except Exception as e:
            logging.error(f"Error al obtener adeudos: {str(e)}")
            return [] 
class CobranzaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Cobranza")
        
        # Colores corporativos
        self.COLOR_ROJO = "#E31837"
        self.COLOR_NEGRO = "#333333"
        self.COLOR_BLANCO = "#FFFFFF"
        self.COLOR_GRIS = "#F5F5F5"
        
        # Colores para categorías
        self.COLOR_VERDE = "#4CAF50"
        self.COLOR_AMARILLO = "#FFC107"
        
        # Configurar la ventana principal
        self.setup_window()
        
        # Inicializar datos
        self.clientes_data = {}
        self.load_initial_data()
        
        # Variable para almacenar la referencia al main_frame
        self.main_frame = None
        
        self.create_header()
        self.create_main_content()
        
    def setup_window(self):
        """Configura las dimensiones y posición de la ventana principal"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1200
        window_height = 800
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg=self.COLOR_BLANCO)
      
    def create_header(self):
        header_frame = tk.Frame(self.root, bg=self.COLOR_ROJO, height=80)
        header_frame.pack(fill='x')
        
        # Frame blanco para el logo
        logo_container = tk.Frame(header_frame, bg=self.COLOR_BLANCO)
        logo_container.pack(side='left', pady=10, padx=20)
        
        try:
            logo_img = Image.open("logo.png")
            logo_img = logo_img.resize((150, 50), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(logo_container, image=logo_photo, bg=self.COLOR_BLANCO)
            logo_label.image = logo_photo
            logo_label.pack(padx=10)
        except:
            logo_label = tk.Label(logo_container, text="GARCIA", 
                                font=("Arial", 20, "bold"), 
                                bg=self.COLOR_BLANCO, 
                                fg=self.COLOR_NEGRO)
            logo_label.pack(padx=10)
        
        cobranza_label = tk.Label(header_frame, 
                                text="COBRANZA", 
                                font=("Arial", 24, "bold"),
                                bg=self.COLOR_ROJO, 
                                fg=self.COLOR_BLANCO)
        cobranza_label.pack(side='left', padx=20)
        
        reload_button = tk.Button(header_frame, 
                              text="⟳ Recargar Datos",
                              font=("Arial", 10),
                              bg=self.COLOR_ROJO,
                              fg=self.COLOR_BLANCO,
                              bd=0,
                              cursor="hand2",
                              command=self.recargar_datos)
        reload_button.pack(side='right', padx=20)
            
        # Botón WhatsApp
        whatsapp_button = tk.Button(header_frame,
                                text="WhatsApp",
                                font=("Arial", 10),
                                bg=self.COLOR_BLANCO,
                                fg=self.COLOR_NEGRO,
                                bd=0,
                                cursor="hand2",
                                command=self.open_whatsapp_bot)
        whatsapp_button.pack(side='right', padx=20)

    def open_whatsapp_bot(self):
        bat_file = r'C:\Users\USER\Documents\GitHub\chatbotwapp\run_whatsapp_bot.bat'  # Reemplaza con la ruta real del archivo .bat
        subprocess.Popen([bat_file], shell=True)
    
    def load_initial_data(self):
        """Carga los datos iniciales de clientes y sus categorías"""
        try:
            self.clientes_data = self.obtener_datos_clientes()
            self.categorias_clientes = self.procesar_todos_clientes()
        except Exception as e:
            logging.error(f"Error al cargar datos iniciales: {e}")
            messagebox.showerror("Error", "Error al cargar datos iniciales")

    def obtener_datos_clientes(self) -> Dict:
        """
        Obtiene los datos de clientes desde la base de datos
        
        Returns:
            Dict: Diccionario con datos de clientes
        """
        conn = get_db_connection()
        if not conn:
            return {}
            
        try:
            cursor = conn.cursor()
            query = """
                SELECT c.Clave, c.Nombre, c.Saldo,
                       v.Folio as Ticket, v.Fecha, v.Total, v.Estado
                FROM Clientes4 c
                LEFT JOIN Ventas v ON c.Clave = v.CveCte
                WHERE c.Saldo > 0
                  AND v.Estado != 'PAGADA'
                  AND v.Estado != 'CANCELADA'
            """
            cursor.execute(query)
            results = cursor.fetchall()
            
            clientes_data = {}
            for row in results:
                if row.Clave not in clientes_data:
                    clientes_data[row.Clave] = {
                        'nombre': row.Nombre,
                        'saldo': row.Saldo,
                        'ventas': []
                    }
                
                if row.Ticket:  # Si hay venta asociada
                    clientes_data[row.Clave]['ventas'].append({
                        'ticket': row.Ticket,
                        'fecha': row.Fecha.strftime("%Y-%m-%d"),
                        'total': row.Total,
                        'estado': row.Estado
                    })
            
            return clientes_data
            
        except Exception as e:
            logging.error(f"Error al obtener datos de clientes: {e}")
            return {}
        finally:
            conn.close()

    def recargar_datos(self):
        """Recarga todos los datos de la aplicación"""
        try:
            self.load_initial_data()
            self.refresh_ui()
            messagebox.showinfo("Éxito", "Datos actualizados correctamente")
        except Exception as e:
            logging.error(f"Error al recargar datos: {e}")
            messagebox.showerror("Error", "Error al recargar los datos")

    def refresh_ui(self):
        """Actualiza la interfaz de usuario con los datos más recientes"""
        # Limpiar y recrear el contenido principal
        if self.main_frame:
            self.main_frame.destroy()
        self.create_main_content()

    def generar_reporte_categoria(self, categoria: str):
        """
        Genera un reporte de clientes por categoría
        
        Args:
            categoria: str - "verde", "amarillo" o "rojo"
        """
        try:
            # Implementar lógica de generación de reportes
            pass
        except Exception as e:
            logging.error(f"Error al generar reporte: {e}")
            messagebox.showerror("Error", "Error al generar el reporte")
    
    def obtener_fecha_venta_antigua(self, cliente_id: str) -> Optional[datetime]:
        """
        Obtiene la fecha de venta más antigua para un cliente desde la base de datos.
        
        Args:
            cliente_id: str - ID del cliente
            
        Returns:
            Optional[datetime] - Fecha más antigua o None si no hay ventas
        """
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            query = """
                SELECT MIN(Fecha) as fecha_antigua
                FROM Ventas
                WHERE CveCte = ?
                AND Estado != 'PAGADA'
                AND Estado != 'CANCELADA'
                AND Restante > 0
            """
            cursor.execute(query, (cliente_id,))
            result = cursor.fetchone()
            
            if result and result.fecha_antigua:
                # Asegurarnos de que la fecha esté en formato datetime
                if isinstance(result.fecha_antigua, datetime):
                    return result.fecha_antigua
                else:
                    return datetime.combine(result.fecha_antigua, datetime.min.time())
            return None
            
        except Exception as e:
            logging.error(f"Error al obtener fecha de venta antigua para cliente {cliente_id}: {e}")
            return None
        finally:
            conn.close()
        
    def categorizar_cliente(self, cliente_id: str) -> str:
        """
        Categoriza un cliente basado en su historial de ventas y estado en ClientsStates.
        
        Args:
            cliente_id: str - ID del cliente
            
        Returns:
            str: "verde", "amarillo", o "rojo" según la categorización
        """
        try:
            # Obtener estados de clientes de la base de datos
            estados_clientes = get_client_states()
            
            # Verificar primero si tiene promisePage
            if cliente_id in estados_clientes and estados_clientes[cliente_id]['promisePage']:
                return "verde"
            
            # Obtener la fecha de venta más antigua
            fecha_venta_antigua = self.obtener_fecha_venta_antigua(cliente_id)
            if not fecha_venta_antigua:
                return "rojo"
            
            # Calcular la diferencia de días
            fecha_actual = datetime.now()
            # Asegurar que ambas fechas son datetime para la comparación
            if isinstance(fecha_venta_antigua, datetime):
                diferencia = fecha_actual - fecha_venta_antigua
            else:
                fecha_venta_antigua = datetime.combine(fecha_venta_antigua, datetime.min.time())
                diferencia = fecha_actual - fecha_venta_antigua
            
            # Categorizar basado en los días
            if diferencia.days < 30:
                return "amarillo"
            else:
                return "rojo"
                
        except Exception as e:
            logging.error(f"Error al categorizar cliente {cliente_id}: {e}")
            return "rojo"  # Por defecto si hay error
    def procesar_todos_clientes(self):
        """
        Procesa y categoriza todos los clientes con saldo pendiente.
        """
        conn = get_db_connection()
        
        if not conn:
            return {}
            
        try:
            cursor = conn.cursor()
            # Obtener todos los clientes con saldo pendiente
            query = """
                SELECT Clave
                FROM Clientes4
                WHERE Saldo > 0
            """
            cursor.execute(query)
            clientes = cursor.fetchall()
            
            categorias = {}
            for cliente in clientes:
                cliente_id = str(cliente.Clave)
                categorias[cliente_id] = self.categorizar_cliente(cliente_id)
                
            return categorias
            
        except Exception as e:
            logging.error(f"Error al procesar todos los clientes: {e}")
            return {}
        finally:
            conn.close()
      
    def create_main_content(self):
        # Contenedor principal que ocupará todo el espacio disponible
        self.main_frame = tk.Frame(self.root, bg=self.COLOR_BLANCO)
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Lista de clientes (izquierda - 2/3 del ancho)
        clientes_frame = tk.LabelFrame(self.main_frame, text="CLIENTES", 
                                     font=("Arial", 16, "bold"),
                                     bg=self.COLOR_BLANCO)
        clientes_frame.pack(side='left', fill='both', expand=True, padx=(0,10))
        
        # Frame contenedor para las categorías
        categories_container = tk.Frame(clientes_frame, bg=self.COLOR_BLANCO)
        categories_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Distribuir el espacio vertical equitativamente entre las tres categorías
        categories_container.grid_rowconfigure(0, weight=1)
        categories_container.grid_rowconfigure(1, weight=1)
        categories_container.grid_rowconfigure(2, weight=1)
        categories_container.grid_columnconfigure(0, weight=1)
        
        # Crear las tres categorías usando grid en lugar de pack
        self.create_category_section(categories_container, "ACUERDO DE PAGO", self.COLOR_VERDE, 0)
        self.create_category_section(categories_container, "MENOS DE 30 DIAS", self.COLOR_AMARILLO, 1)
        self.create_category_section(categories_container, "MAS DE 30 DIAS", self.COLOR_ROJO, 2)
        
        # Frame para detalles del cliente (derecha - 1/3 del ancho)
        self.detalles_frame = tk.LabelFrame(self.main_frame,
                                          text="ADEUDO",
                                          font=("Arial", 16, "bold"),
                                          bg=self.COLOR_BLANCO)
        self.detalles_frame.pack(side='right', fill='both', expand=True, padx=(10,0))

    def create_category_section(self, parent, title, color, row):
        """
        Crea una sección de categoría en la interfaz.
        
        Args:
            parent: tk.Widget - Widget padre donde se creará la sección
            title: str - Título de la sección
            color: str - Color de la categoría
            row: int - Fila donde se colocará la sección
        """
        # Frame para la categoría
        category_frame = tk.LabelFrame(parent, text=title,
                                    font=("Arial", 12, "bold"),
                                    bg=self.COLOR_BLANCO,
                                    fg=color)
        category_frame.grid(row=row, column=0, sticky='nsew', padx=5, pady=5)
        
        # Configurar el category_frame para expandirse
        category_frame.grid_rowconfigure(0, weight=1)
        category_frame.grid_columnconfigure(0, weight=1)
        
        # Crear Treeview con columna oculta para la clave
        visible_columns = ('Nombre', 'Monto', 'Fecha')
        tree = ttk.Treeview(category_frame, columns=('Clave',) + visible_columns, show='headings')
        
        # Configurar columnas - la columna Clave tiene width=0 para ocultarla
        tree.column('Clave', width=0, stretch=False)
        tree.column('Nombre', width=250, minwidth=250)
        tree.column('Monto', width=100, minwidth=100)
        tree.column('Fecha', width=100, minwidth=100)
        
        # Solo configurar headings para columnas visibles
        for col in visible_columns:
            tree.heading(col, text=col)
        
        # Estilo para el Treeview
        style = ttk.Style()
        style.configure("Treeview",
                    background=self.COLOR_BLANCO,
                    foreground=self.COLOR_NEGRO,
                    fieldbackground=self.COLOR_BLANCO)
        
        # Insertar datos según la categoría
        for clave, cliente in self.clientes_data.items():
            categoria = self.categorizar_cliente(clave)
            if ((color == self.COLOR_VERDE and categoria == "verde") or
                (color == self.COLOR_AMARILLO and categoria == "amarillo") or
                (color == self.COLOR_ROJO and categoria == "rojo")):
                
                fecha_antigua = self.obtener_fecha_venta_antigua(clave)
                if fecha_antigua:
                    fecha_str = fecha_antigua.strftime("%Y-%m-%d")
                else:
                    fecha_str = "N/A"
                
                tree.insert('', 'end', values=(
                    clave,  # Se mantiene pero no se muestra
                    cliente['nombre'],
                    f"${cliente['saldo']:,.2f}",
                    fecha_str
                ))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(category_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Usar grid para el tree y scrollbar
        tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Vincular eventos
        tree.bind('<<TreeviewSelect>>', self.mostrar_detalles_cliente)
        tree.bind('<Double-1>', self.abrir_detalle_cliente)
    
    def mostrar_detalles_cliente(self, event):
        # Obtener el Treeview que generó el evento
        tree = event.widget
        
        # Limpiar frame de detalles
        for widget in self.detalles_frame.winfo_children():
            widget.destroy()
            
        # Obtener el cliente seleccionado
        selected_item = tree.selection()[0]
        cliente_clave = tree.item(selected_item)['values'][0]
        cliente = self.clientes_data[cliente_clave]
        
        # Sección de Saldo Total
        saldo_frame = tk.Frame(self.detalles_frame, bg=self.COLOR_BLANCO)
        saldo_frame.pack(fill='x', padx=10, pady=10)
        
        saldo_label = tk.Label(saldo_frame,
                            text="Saldo Total:",
                            font=("Arial", 12, "bold"),
                            bg=self.COLOR_BLANCO)
        saldo_label.pack(side='left')
        
        saldo_value = tk.Label(saldo_frame,
                            text=f"${cliente['saldo']:,.2f}",
                            font=("Arial", 12, "bold"),
                            fg=self.COLOR_ROJO,
                            bg=self.COLOR_BLANCO)
        saldo_value.pack(side='right')
        
        # Separador
        separator = ttk.Separator(self.detalles_frame, orient='horizontal')
        separator.pack(fill='x', padx=10, pady=10)
        
        # Título de Ventas
        ventas_title = tk.Label(self.detalles_frame,
                            text="Tickets Pendientes",
                            font=("Arial", 11, "bold"),
                            bg=self.COLOR_BLANCO)
        ventas_title.pack(padx=10, pady=(0, 10))
        
        # Frame para la lista de ventas
        ventas_container = tk.Frame(self.detalles_frame, bg=self.COLOR_BLANCO)
        ventas_container.pack(fill='both', expand=True, padx=10)
        
        # Crear Treeview para ventas
        columns = ('Ticket', 'Fecha', 'Total')
        ventas_tree = ttk.Treeview(ventas_container, columns=columns, show='headings', height=10)
        
        # Configurar columnas
        ventas_tree.column('Ticket', width=80, minwidth=80)
        ventas_tree.column('Fecha', width=100, minwidth=100)
        ventas_tree.column('Total', width=100, minwidth=100)
        
        for col in columns:
            ventas_tree.heading(col, text=col)
        
        # Obtener y ordenar ventas
        if 'ventas' in cliente:
            ventas = sorted(
                [venta for venta in cliente['ventas'] if venta['estado'] == "X COBRAR"],
                key=lambda x: datetime.strptime(x['fecha'], "%Y-%m-%d"),
                reverse=True
            )
            
            # Insertar ventas ordenadas
            for venta in ventas:
                ticket_num = extract_ticket_number(venta.get('ticket', ''))
                ventas_tree.insert('', 'end', values=(
                    ticket_num,
                    venta['fecha'],
                    f"${venta['total']:,.2f}"
                ))
        
        # Scrollbar para las ventas
        scrollbar = ttk.Scrollbar(ventas_container, orient='vertical', command=ventas_tree.yview)
        ventas_tree.configure(yscrollcommand=scrollbar.set)
        
        # Colocar Treeview y scrollbar
        ventas_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def abrir_detalle_cliente(self, event):
        try:
            # 1. Obtener la clave del cliente seleccionado del TreeView
            tree = event.widget
            selected_item = tree.selection()[0]
            client_clave = tree.item(selected_item)['values'][0]  # Obtenemos el ID
            client_clave_str = str(client_clave)
            
            print(f"Buscando datos completos para el cliente: {client_clave_str}")
            
            # 2. Obtener los datos completos del cliente usando get_clients_data
            todos_los_clientes = get_clients_data()  # Nueva llamada para obtener datos completos
            
            # 3. Buscar el cliente específico
            client_detallado = todos_los_clientes.get(client_clave_str)
            
            if not client_detallado:
                messagebox.showwarning(
                    "Cliente no encontrado",
                    "No se encontraron datos detallados para este cliente. Es posible que no tenga saldo pendiente."
                )
                return
                
            print(f"Datos detallados encontrados: {client_detallado}")
            
            # 4. Crear la ventana de detalle con los datos completos
            detalle_window = DetalleClienteWindow(self.root, client_detallado, client_clave_str)
            detalle_window.top.focus_force()
            
        except IndexError:
            messagebox.showerror("Error", "Por favor seleccione un cliente de la lista")
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir detalle del cliente: {str(e)}")
            print(f"Error detallado: {e}")
if __name__ == "__main__":
    root = tk.Tk()
    app = CobranzaApp(root)
    root.mainloop()
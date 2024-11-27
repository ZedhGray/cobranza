import os
import sys
import subprocess

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import socketio
except ImportError:
    install_package('python-socketio')
    import socketio
# Ruta al entorno virtual
venv_path = os.path.join(os.path.dirname(sys.argv[0]), 'venv', 'Scripts', 'python.exe')

# Activar el entorno virtual
os.environ['VIRTUAL_ENV'] = os.path.dirname(venv_path)
os.environ['PATH'] = os.path.dirname(venv_path) + os.pathsep + os.environ['PATH']
sys.executable = venv_path

# Resto del código de la aplicación
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime
import re
from database import get_client_states, get_db_connection, get_clients_data
import logging
from tkinter import messagebox
from typing import Dict, Optional
import pyodbc
import threading
import time
import socketio
from main import actualizar_datos

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

class LoadingSplash:
    def __init__(self, root):
        self.root = root
        self.root.title("Cargando")
        # Hacer la ventana más pequeña y centrada
        window_width = 300
        window_height = 150
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Quitar bordes de ventana
        self.root.overrideredirect(True)
        
        # Mantener ventana siempre arriba
        self.root.attributes('-topmost', True)
        
        # Crear marco principal
        self.frame = ttk.Frame(root)
        self.frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Etiqueta de estado
        self.status_label = ttk.Label(
            self.frame, 
            text="Actualizando datos...",
            font=('Helvetica', 10)
        )
        self.status_label.pack(pady=10)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(
            self.frame,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(pady=10)
        
        # Mensaje adicional
        self.message = ttk.Label(
            self.frame,
            text="Por favor espere mientras se actualizan los datos",
            font=('Helvetica', 8),
            wraplength=250,
            justify='center'
        )
        self.message.pack(pady=10)
        
        # Referencias para evitar la recolección de basura
        self.root.splash_references = {
            'status_label': self.status_label,
            'progress': self.progress,
            'message': self.message
        }
        
    def start_progress(self):
        self.progress.start(10)
    
    def stop_progress(self):
        self.progress.stop()
        
    def update_status(self, text):
        self.status_label.config(text=text)
        
    def destroy(self):
        # Limpiar referencias antes de destruir
        if hasattr(self.root, 'splash_references'):
            del self.root.splash_references
        self.root.destroy()

class DetalleClienteWindow:
    def __init__(self, parent, client_data, client_id):
        self.top = tk.Toplevel(parent)
        self.client_data = client_data
        self.client_id = client_id
        self.setup_window()

        # Inicializar el socket de comunicación con WhatsApp
        self.sio = socketio.Client()
        
        # Configurar listeners de socket
        self.setup_socket_listeners()
        
        # Conectar al servidor de socket
        try:
            self.sio.connect('http://localhost:3000')
        except Exception as e:
            messagebox.showerror("Error de Conexión", 
                                 f"No se pudo conectar con WhatsApp: {str(e)}")
        
        # Colores
        self.COLOR_ROJO = "#E31837"
        self.COLOR_NEGRO = "#333333"
        self.COLOR_BLANCO = "#FFFFFF"
        self.COLOR_GRIS = "#F5F5F5"
        self.COLOR_GRIS_CLARO = "#EFEFEF"
        self.COLOR_ROJO_HOVER = "#C41230"  # Color más oscuro para hover
        self.COLOR_GRIS_HOVER = "#E8E8E8"  # Color más oscuro para hover

        # Guardar referencia al client_id actual
        self.current_client_id = client_id

        # Inicializar timeline_container
        self.timeline_container = None
        
        # Crear el frame principal que contendrá todo
        self.main_frame = tk.Frame(self.top, bg=self.COLOR_BLANCO)
        self.main_frame.pack(fill='both', expand=True)
        
        # Crear frame izquierdo para contenido principal
        self.left_frame = tk.Frame(self.main_frame, bg=self.COLOR_BLANCO)
        self.left_frame.pack(side='left', fill='both', expand=True)
        
        # Crear frame derecho para botones y controles
        self.right_frame = tk.Frame(self.main_frame, bg=self.COLOR_GRIS, width=150)
        self.right_frame.pack(side='right', fill='y', padx=10, pady=10)
        self.right_frame.pack_propagate(False)  # Mantener ancho fijo
        
        self.create_cliente_frame()
        self.create_timeline_frame(client_id)
        self.create_adeudo_frame()
        self.create_control_panel()

    def setup_window(self):
        """Configura la ventana de detalles"""
        self.top.title(f"Detalle Cliente - {self.client_data.get('nombre', 'Sin nombre')}")
        window_width = 800
        window_height = 800
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.top.geometry(f"{window_width}x{window_height}+{x}+{y}")
           
    def create_control_panel(self):
        """Crea el panel de control lateral derecho con estilo mejorado"""
        # Frame contenedor con borde redondeado
        control_container = tk.Frame(self.right_frame, bg=self.COLOR_GRIS)
        control_container.pack(fill='x', pady=10)

        controls_label = tk.Label(control_container, 
                                text="CONTROLES", 
                                font=("Arial", 12, "bold"),
                                bg=self.COLOR_GRIS,
                                fg=self.COLOR_NEGRO)
        controls_label.pack(pady=(10,20))

        # Estilo mejorado para el botón de agregar nota
        add_note_btn = tk.Button(control_container, 
                               text="+ Agregar Nota",
                               font=("Arial", 10, "bold"),
                               bg=self.COLOR_BLANCO,
                               fg=self.COLOR_NEGRO,
                               bd=0,  # Sin borde
                               relief="flat",  # Estilo plano
                               padx=15,  # Padding horizontal
                               pady=8,   # Padding vertical
                               width=15,  # Ancho fijo
                               cursor="hand2",  # Cursor tipo mano
                               command=lambda: self.show_note_dialog(self.client_id))
        
        add_note_btn.pack(pady=(0,10))

        # Configurar eventos hover para el botón de nota
        def on_enter_note(e):
            add_note_btn['bg'] = self.COLOR_GRIS_HOVER
        def on_leave_note(e):
            add_note_btn['bg'] = self.COLOR_BLANCO

        add_note_btn.bind("<Enter>", on_enter_note)
        add_note_btn.bind("<Leave>", on_leave_note)

        # Separador visual
        separator = tk.Frame(control_container, height=1, bg=self.COLOR_GRIS_HOVER)
        separator.pack(fill='x', pady=10)

        # Botón de promesa con estilo mejorado
        promise_state = self.get_promise_state(self.client_id)
        button_text = "En Promesa" if promise_state else "Promesa"
        button_color = self.COLOR_ROJO if promise_state else self.COLOR_BLANCO
        text_color = self.COLOR_BLANCO if promise_state else self.COLOR_NEGRO
        
        self.promise_btn = tk.Button(control_container,
                                   text=button_text,
                                   font=("Arial", 10, "bold"),
                                   bg=button_color,
                                   fg=text_color,
                                   bd=0,
                                   relief="flat",
                                   padx=15,
                                   pady=8,
                                   width=15,
                                   cursor="hand2",
                                   command=lambda: self.toggle_promise(self.client_id))
        
        self.promise_btn.pack(pady=(0,10))

        # Configurar eventos hover para el botón de promesa
        def on_enter_promise(e):
            if not promise_state:
                self.promise_btn['bg'] = self.COLOR_GRIS_HOVER
            else:
                self.promise_btn['bg'] = self.COLOR_ROJO_HOVER
        
        def on_leave_promise(e):
            if not promise_state:
                self.promise_btn['bg'] = self.COLOR_BLANCO
            else:
                self.promise_btn['bg'] = self.COLOR_ROJO

        self.promise_btn.bind("<Enter>", on_enter_promise)
        self.promise_btn.bind("<Leave>", on_leave_promise)
        
        # Separador visual
        separator = tk.Frame(control_container, height=1, bg=self.COLOR_GRIS_HOVER)
        separator.pack(fill='x', pady=10)

        # Botón de WhatsApp con estilo mejorado
        whatsapp_btn = tk.Button(control_container, 
                               text="Abrir Chat WhatsApp",
                               font=("Arial", 10, "bold"),
                               bg=self.COLOR_BLANCO,
                               fg=self.COLOR_NEGRO,
                               bd=0,  # Sin borde
                               relief="flat",  # Estilo plano
                               padx=15,  # Padding horizontal
                               pady=8,   # Padding vertical
                               width=15,  # Ancho fijo
                               cursor="hand2",  # Cursor tipo mano
                               command=self.abrir_chat_whatsapp)
        
        whatsapp_btn.pack(pady=(0,10))

        # Configurar eventos hover para el botón de WhatsApp
        def on_enter(e):
            whatsapp_btn['bg'] = self.COLOR_GRIS_HOVER
        def on_leave(e):
            whatsapp_btn['bg'] = self.COLOR_BLANCO

        whatsapp_btn.bind("<Enter>", on_enter)
        whatsapp_btn.bind("<Leave>", on_leave)

    def __del__(self):
        # Asegurarse de desconectar el socket al cerrar
        try:
            self.sio.disconnect()
        except:
            pass

    def setup_socket_listeners(self):
        @self.sio.on('chat-opened')
        def on_chat_opened(data):
            if data.get('success'):
                messagebox.showinfo("Éxito", "Chat de WhatsApp abierto")
            else:
                messagebox.showerror("Error", 
                                     data.get('error', "No se pudo abrir el chat"))     
    
    def abrir_chat_whatsapp(self, telefono=None):
        """
        Abre un chat de WhatsApp para un cliente específico
        
        :param telefono: Número de teléfono. Si es None, intenta obtenerlo de los datos del cliente
        """
        # Si no se proporciona teléfono, intentar obtenerlo de los datos del cliente
        if telefono is None:
            telefono = self.client_data.get('telefono1')
        
        if not telefono:
            messagebox.showerror("Error", "No se encontró número de teléfono")
            return
        
        try:
            # Emitir evento para abrir chat
            self.sio.emit('open-chat', telefono)
        except Exception as e:
            messagebox.showerror("Error de Comunicación", 
                                 f"No se pudo abrir el chat: {str(e)}")
    def create_cliente_frame(self):
        """Crea el frame principal del cliente"""
        client_frame = tk.LabelFrame(self.left_frame, text="CLIENTE", 
                                   font=("Arial", 16, "bold"), bg=self.COLOR_BLANCO)
        client_frame.pack(fill='x', padx=20, pady=(20,10))

        info_container = tk.Frame(client_frame, bg=self.COLOR_BLANCO)
        info_container.pack(fill='x', padx=20, pady=10)

        self.create_info_field(info_container, "Número de Cliente:", str(self.client_id))
        self.create_info_field(info_container, "Nombre:", self.client_data.get('nombre', 'N/A'))
        self.create_info_field(info_container, "Teléfono:", self.client_data.get('telefono1', 'N/A'))
        self.create_info_field(info_container, "Telefono Referencia:", self.client_data.get('telefono2', 'N/A'))
        self.create_info_field(info_container, "Dirección:", self.client_data.get('direccion', 'N/A'))
        self.create_info_field(info_container, "Saldo:", f"${self.client_data.get('saldo', 0):,.2f}")
        self.create_info_field(info_container, "Crédito:", "Sí" if self.client_data.get('credito') else "No")

        estado_frame = tk.Frame(client_frame, bg=self.COLOR_BLANCO)
        estado_frame.place(relx=1.0, x=-20, y=10, anchor='ne')

        estado_label = tk.Label(estado_frame, text="●", font=("Arial", 12), fg=self.COLOR_ROJO, bg=self.COLOR_BLANCO)
        estado_label.pack(side='left')

        estado_texto = tk.Label(estado_frame, text=self.client_data.get('estado', 'ACTIVO'), font=("Arial", 12), fg=self.COLOR_ROJO, bg=self.COLOR_BLANCO)
        estado_texto.pack(side='left', padx=5)

    def create_info_field(self, parent, label, value):
        """Crea un campo de información"""
        frame = tk.Frame(parent, bg=self.COLOR_BLANCO)
        frame.pack(fill='x', pady=5)

        label_widget = tk.Label(frame, text=label, font=("Arial", 10, "bold"), bg=self.COLOR_BLANCO)
        label_widget.pack(side='left', padx=(0,5))

        value_widget = tk.Label(frame, text=str(value), font=("Arial", 10), bg=self.COLOR_BLANCO)
        value_widget.pack(side='left', padx=(0,10))

        return frame
    
    def create_timeline_frame(self, client_id):
        """Crea el frame principal de la timeline"""
        timeline_frame = tk.LabelFrame(self.left_frame, text="LINEA DE TIEMPO", 
                                     font=("Arial", 16, "bold"), bg=self.COLOR_BLANCO)
        timeline_frame.pack(fill='x', padx=20, pady=10)

        self.canvas = tk.Canvas(timeline_frame, bg=self.COLOR_BLANCO, height=300)
        scrollbar = ttk.Scrollbar(timeline_frame, orient="vertical", command=self.canvas.yview)
        self.interior_frame = tk.Frame(self.canvas, bg=self.COLOR_BLANCO)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")

        self.canvas.create_window((0, 0), window=self.interior_frame, anchor="nw")

        states_section = tk.Frame(self.interior_frame, bg=self.COLOR_BLANCO)
        states_section.pack(fill='x', expand=True)
        self.create_states_section(states_section, client_id)

        notes_section = tk.Frame(self.interior_frame, bg=self.COLOR_BLANCO)
        notes_section.pack(fill='x', expand=True, pady=(20, 0))
        self.create_notes_section(notes_section, client_id)

        def _configure_interior(event):
            size = (self.interior_frame.winfo_reqwidth(), self.interior_frame.winfo_reqheight())
            self.canvas.config(scrollregion="0 0 %s %s" % size)
            if self.interior_frame.winfo_reqwidth() != self.canvas.winfo_width():
                self.canvas.config(width=self.interior_frame.winfo_reqwidth())

        self.interior_frame.bind('<Configure>', _configure_interior)
        
    def create_states_section(self, container, client_id):
        """Crea la sección de estados en la timeline"""
        client_data = self.get_client_data(client_id)
        if client_data:
            for key, value in client_data.items():
                if key != "promisePage":
                    label = tk.Label(container, text=f"{key}: {value}", bg=self.COLOR_BLANCO, font=("Arial", 12))
                    label.pack(anchor='w', pady=2)

    def create_notes_section(self, container, client_id):
        """Crea la sección de notas en la timeline"""
        notes_title = tk.Label(container, text="Detalles", 
                             font=("Arial", 14, "bold"), bg=self.COLOR_BLANCO)
        notes_title.pack(anchor='w', pady=(0, 10))

        self.notes_container = tk.Frame(container, bg=self.COLOR_BLANCO)
        self.notes_container.pack(fill='x', expand=True)

        self.update_notes_section(self.notes_container, client_id)
    
    def update_notes_section(self, container, client_id):
        """Actualiza la sección de notas en la timeline"""
        notes = self.get_client_notes(client_id)
        self.refresh_notes_display(notes)
        
    def get_promise_state(self, client_id):
        """Obtiene el estado actual de la promesa de pago"""
        try:
            conn = get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("SELECT promisePage FROM dbo.ClientsStates WHERE client_id = ?", (client_id,))
            result = cursor.fetchone()
            
            if result:
                return bool(result.promisePage)
            else:
                return False
        except pyodbc.Error as e:
            logging.error(f"Error al obtener estado de promesa: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
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
                    "Mensaje un dia antes": "Sí" if row.day1 else "No",
                    "Mensaje 2 dias antes": "Sí" if row.day2 else "No",
                    "Mensaje 3 dias antes": "Sí" if row.day3 else "No",
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
        """Alterna el estado de la promesa de pago con actualización visual mejorada"""
        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT promisePage FROM dbo.ClientsStates WHERE client_id = ?", (client_id,))
            current_state = cursor.fetchone()

            if current_state is not None:
                new_state = not bool(current_state.promisePage)
                cursor.execute("""
                    UPDATE dbo.ClientsStates 
                    SET promisePage = ?
                    WHERE client_id = ?
                """, (new_state, client_id))
                conn.commit()

                # Actualizar el botón con los nuevos estilos
                new_text = "En Promesa" if new_state else "Promesa"
                new_bg_color = self.COLOR_ROJO if new_state else self.COLOR_BLANCO
                new_fg_color = self.COLOR_BLANCO if new_state else self.COLOR_NEGRO
                
                self.promise_btn.configure(
                    text=new_text,
                    bg=new_bg_color,
                    fg=new_fg_color
                )

                # Actualizar los eventos hover
                def on_enter(e):
                    if new_state:
                        self.promise_btn['bg'] = self.COLOR_ROJO_HOVER
                    else:
                        self.promise_btn['bg'] = self.COLOR_GRIS_HOVER

                def on_leave(e):
                    self.promise_btn['bg'] = new_bg_color

                self.promise_btn.bind("<Enter>", on_enter)
                self.promise_btn.bind("<Leave>", on_leave)

        except pyodbc.Error as e:
            logging.error(f"Error al actualizar promesa de pago: {e}")
        finally:
            if conn:
                conn.close()                
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
            rows = cursor.fetchall()
            
            for row in rows:
                note = {
                    'id': row[0],  # Acceder por índice en lugar de nombre
                    'text': row[1],
                    'timestamp': row[2]
                }
                notes.append(note)
            return notes
        except pyodbc.Error as e:
            logging.error(f"Error al obtener notas del cliente {client_id}: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def update_timeline(self, notes):
        # Eliminar solo los widgets de notas anteriores
        for widget in self.canvas.winfo_children():
            if widget.winfo_class() == "Frame" and "note_frame" in str(widget):
                widget.destroy()

        # Recrear los frames de las nuevas notas
        for note in notes:
            note_frame = tk.Frame(self.canvas, bg=self.COLOR_GRIS_CLARO)
            note_frame.pack(fill='x', padx=20, pady=10)

            timestamp = note['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            tk.Label(note_frame, text=f"Nota del {timestamp}", font=("Arial", 10, "bold"), bg=self.COLOR_GRIS_CLARO).pack(side='left', padx=10)

            note_text = tk.Label(note_frame, text=note['text'], font=("Arial", 10), bg=self.COLOR_GRIS_CLARO, wraplength=600, anchor='w')
            note_text.pack(side='left', fill='x', expand=True, padx=10)
    
    def refresh_notes_display(self, notes):
        """Actualiza la visualización de las notas"""
        # Limpiar el contenedor de notas actual
        for widget in self.notes_container.winfo_children():
            widget.destroy()

        # Crear nuevos widgets para cada nota
        for note in notes:
            note_frame = tk.Frame(self.notes_container, bg=self.COLOR_GRIS_CLARO)
            note_frame.pack(fill='x', padx=20, pady=10)

            timestamp = note['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            tk.Label(note_frame, 
                    text=f"Nota del {timestamp}", 
                    font=("Arial", 10, "bold"), 
                    bg=self.COLOR_GRIS_CLARO).pack(side='left', padx=10)

            note_text = tk.Label(note_frame, 
                            text=note['text'], 
                            font=("Arial", 10), 
                            bg=self.COLOR_GRIS_CLARO, 
                            wraplength=600, 
                            anchor='w')
            note_text.pack(side='left', fill='x', expand=True, padx=10)

        # Actualizar el canvas para mostrar las nuevas notas
        self.interior_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
   
    def save_note_to_db(self, client_id, note_text):
        """Guarda una nueva nota en la base de datos"""
        conn = get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO Notes (client_id, note_text)
                VALUES (?, ?)
            """
            cursor.execute(query, (client_id, note_text))
            conn.commit()
            return True
        except pyodbc.Error as e:
            logging.error(f"Error al guardar nota: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def show_note_dialog(self, client_id):
        """Muestra un diálogo para agregar una nueva nota, centrado en la pantalla"""
        dialog = tk.Toplevel(self.top)
        dialog.title("Agregar Nota")
        dialog.configure(bg=self.COLOR_BLANCO)
        
        # Hacer la ventana modal
        dialog.transient(self.top)
        dialog.grab_set()
        
        # Establecer el tamaño de la ventana
        dialog_width = 400
        dialog_height = 200

        # Opción 1: Centrar respecto a la ventana padre
        parent_x = self.top.winfo_x()
        parent_y = self.top.winfo_y()
        parent_width = self.top.winfo_width()
        parent_height = self.top.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        # Opción 2: Centrar respecto a la pantalla
        # screen_width = dialog.winfo_screenwidth()
        # screen_height = dialog.winfo_screenheight()
        # x = (screen_width - dialog_width) // 2
        # y = (screen_height - dialog_height) // 2

        # Aplicar la geometría
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Frame principal con padding
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
                tk.messagebox.showwarning("Advertencia", "Por favor ingrese una nota")
                return
            if self.save_note_to_db(client_id, text):
                dialog.destroy()
                # Obtener las notas actualizadas y actualizar la interfaz
                notes = self.get_client_notes(client_id)
                self.refresh_notes_display(notes)
            else:
                tk.messagebox.showerror("Error", "No se pudo guardar la nota")
        
        # Frame para botones con padding
        button_frame = tk.Frame(main_frame, bg=self.COLOR_BLANCO)
        button_frame.pack(fill='x', pady=(10, 0))
        
        # Botón Cancelar con estilo
        cancel_btn = tk.Button(button_frame,
                            text="Cancelar",
                            command=dialog.destroy,
                            font=("Arial", 10),
                            bg=self.COLOR_GRIS,
                            fg=self.COLOR_NEGRO,
                            bd=0,
                            padx=15,
                            pady=5,
                            relief="flat",
                            cursor="hand2")
        cancel_btn.pack(side='right', padx=5)
        
        # Botón Guardar con estilo
        save_btn = tk.Button(button_frame,
                            text="Guardar",
                            command=save,
                            font=("Arial", 10, "bold"),
                            bg=self.COLOR_ROJO,
                            fg=self.COLOR_BLANCO,
                            bd=0,
                            padx=15,
                            pady=5,
                            relief="flat",
                            cursor="hand2")
        save_btn.pack(side='right', padx=5)

        # Eventos hover para los botones
        def on_enter_save(e):
            save_btn['bg'] = self.COLOR_ROJO_HOVER

        def on_leave_save(e):
            save_btn['bg'] = self.COLOR_ROJO

        def on_enter_cancel(e):
            cancel_btn['bg'] = self.COLOR_GRIS_HOVER

        def on_leave_cancel(e):
            cancel_btn['bg'] = self.COLOR_GRIS

        # Vincular eventos hover
        save_btn.bind("<Enter>", on_enter_save)
        save_btn.bind("<Leave>", on_leave_save)
        cancel_btn.bind("<Enter>", on_enter_cancel)
        cancel_btn.bind("<Leave>", on_leave_cancel)

        # Enfocar el campo de texto automáticamente
        note_text.focus_set()      
    
    #Adeudo frame =================================================================
    
    def create_adeudo_frame(self):
        """Crea el frame de adeudos con scrollbar para manejar múltiples tickets"""
        adeudo_frame = tk.LabelFrame(self.left_frame, text="ADEUDO", 
                                font=("Arial", 16, "bold"), bg=self.COLOR_BLANCO)
        adeudo_frame.pack(fill='x', padx=20, pady=(0,20))

        # Crear canvas y scrollbar
        canvas = tk.Canvas(adeudo_frame, bg=self.COLOR_BLANCO, height=150)
        scrollbar = ttk.Scrollbar(adeudo_frame, orient="vertical", command=canvas.yview)
        
        # Frame interior que contendrá todos los tickets
        interior_frame = tk.Frame(canvas, bg=self.COLOR_BLANCO)
        
        # Configurar el canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar el canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=(20,0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10, padx=(0,10))
        
        # Crear ventana en el canvas
        canvas.create_window((0, 0), window=interior_frame, anchor="nw", width=canvas.winfo_reqwidth())

        try:
            # Obtener adeudos desde la base de datos
            adeudos = self.get_adeudos_from_db()

            if not adeudos:
                no_adeudos = tk.Label(interior_frame,
                                    text="No hay adeudos registrados",
                                    font=("Arial", 10, "italic"),
                                    bg=self.COLOR_BLANCO)
                no_adeudos.pack(pady=10)
                return

            # Mostrar cada ticket
            for adeudo in adeudos:
                row_frame = tk.Frame(interior_frame, bg=self.COLOR_BLANCO)
                row_frame.pack(fill='x', pady=2)

                # Crear frame para el ticket (será clickeable)
                ticket_frame = tk.Frame(row_frame, bg=self.COLOR_BLANCO, cursor="hand2")
                ticket_frame.pack(side='left', fill='x', expand=True)
                
                # Ticket y fecha con estilo de enlace
                ticket_text = f"Ticket #{adeudo['ticket']} ({adeudo['fecha']})"
                ticket_label = tk.Label(ticket_frame,
                                    text=ticket_text,
                                    font=("Arial", 10, "underline"),
                                    bg=self.COLOR_BLANCO,
                                    fg="blue",
                                    cursor="hand2")
                ticket_label.pack(side='left')

                # Agregar eventos para efecto hover
                def on_enter(e, label=ticket_label):
                    label.configure(fg="purple")
                
                def on_leave(e, label=ticket_label):
                    label.configure(fg="blue")

                ticket_label.bind('<Enter>', on_enter)
                ticket_label.bind('<Leave>', on_leave)
                ticket_label.bind('<Button-1>', lambda e, a=adeudo: self.show_ticket_detail(a))

                # Monto con flecha hacia abajo (↓)
                monto_text = f"${adeudo['monto']:,.2f} ↓"
                monto_label = tk.Label(row_frame,
                                text=monto_text,
                                font=("Arial", 10),
                                bg=self.COLOR_BLANCO)
                monto_label.pack(side='right')

            # Separador antes del total
            separator = ttk.Separator(interior_frame, orient='horizontal')
            separator.pack(fill='x', pady=5)

            # Frame para el total
            total_frame = tk.Frame(interior_frame, bg=self.COLOR_BLANCO)
            total_frame.pack(fill='x', pady=5)

            # Total
            total_label = tk.Label(total_frame,
                                text="Total",
                                font=("Arial", 10),
                                bg=self.COLOR_BLANCO)
            total_label.pack(side='left')

            total = sum(adeudo['monto'] for adeudo in adeudos)
            total_amount = tk.Label(total_frame,
                                text=f"${total:,.2f}",
                                font=("Arial", 10, "bold"),
                                fg=self.COLOR_ROJO,
                                bg=self.COLOR_BLANCO)
            total_amount.pack(side='right')

            # Configurar el scrolling
            def _on_frame_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
                # Ajustar el ancho del frame interior al ancho del canvas
                canvas.itemconfig(canvas.find_withtag("all")[0], width=canvas.winfo_width())

            interior_frame.bind('<Configure>', _on_frame_configure)

            # Configurar el scroll con la rueda del mouse
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        except Exception as e:
            logging.error(f"Error al crear frame de adeudos: {str(e)}")
            error_label = tk.Label(interior_frame,
                                text="Error al cargar adeudos",
                                font=("Arial", 10),
                                fg="red",
                                bg=self.COLOR_BLANCO)
            error_label.pack(pady=10)
    
    def get_adeudos_from_db(self):
        """
        Obtiene los adeudos pendientes de la base de datos
        Returns:
            list: Lista de diccionarios con la información de tickets pendientes
        """
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    Folio as ticket,
                    Fecha,
                    Restante as monto,
                    Ticket as datos
                FROM Ventas
                WHERE Estado != 'PAGADA'
                AND Estado != 'CANCELADA'
                AND Estado IS NOT NULL
                AND Restante > 0
                AND CveCte = ?
            """
            cursor.execute(query, (self.client_id,))
            results = cursor.fetchall()

            adeudos = []
            for row in results:
                adeudo = {
                    'ticket': row.ticket,
                    'fecha': row.Fecha.strftime('%Y-%m-%d') if row.Fecha else '',
                    'monto': float(row.monto),
                    "datos": row.datos
                }
                adeudos.append(adeudo)
                print(adeudo)  # Imprime cada adeudo en consola
            
            return adeudos

        except pyodbc.Error as e:
            logging.error(f"Error al obtener adeudos: {str(e)}")
            return []
        finally:
            conn.close()
    
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

    def show_ticket_detail(self, ticket_data):
        """Muestra una ventana emergente con los detalles del ticket"""
        # Crear nueva ventana
        detail_window = tk.Toplevel(self.top)
        detail_window.title(f"Ticket #{ticket_data['ticket']}")
        
        # Configurar geometría
        window_width = 400
        window_height = 750
        screen_width = detail_window.winfo_screenwidth()
        screen_height = detail_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        detail_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        detail_window.configure(bg=self.COLOR_BLANCO)
        
        # Frame principal con padding
        main_frame = tk.Frame(detail_window, bg=self.COLOR_BLANCO)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Logo y encabezado
        logo_label = tk.Label(main_frame, 
                            text="GARCIA RINES Y NEUMATICOS",
                            font=("Arial", 16, "bold"),
                            bg=self.COLOR_BLANCO)
        logo_label.pack(pady=(0, 10))
        
        # Información del ticket
        info_frame = tk.Frame(main_frame, bg=self.COLOR_BLANCO)
        info_frame.pack(fill='x', pady=(0, 10))
        
        # Número de ticket y fecha
        ticket_info = tk.Label(info_frame,
                            text=f"TICKET: {ticket_data['ticket']} [{ticket_data['fecha']}]",
                            font=("Arial", 10),
                            bg=self.COLOR_BLANCO)
        ticket_info.pack(anchor='w')
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Frame para artículos con scroll
        canvas = tk.Canvas(main_frame, bg=self.COLOR_BLANCO)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        items_frame = tk.Frame(canvas, bg=self.COLOR_BLANCO)
        
        # Configurar scroll
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Crear ventana en canvas
        canvas.create_window((0, 0), window=items_frame, anchor="nw", width=canvas.winfo_reqwidth())
        
        # Procesar y mostrar los datos del ticket
        lines = ticket_data['datos'].split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Encabezados de sección
            if "CANT" in line and "DESCRIPCION" in line:
                current_section = "items"
                headers = tk.Label(items_frame,
                                text=line,
                                font=("Arial", 10, "bold"),
                                bg=self.COLOR_BLANCO)
                headers.pack(anchor='w')
                continue
                
            if current_section == "items":
                if "-------" in line:
                    ttk.Separator(items_frame, orient='horizontal').pack(fill='x', pady=5)
                    continue
                    
                if "IMPORTE:" in line or "EFECTIVO:" in line or "ADEUDA:" in line:
                    amount_frame = tk.Frame(items_frame, bg=self.COLOR_BLANCO)
                    amount_frame.pack(fill='x')
                    
                    label = tk.Label(amount_frame,
                                text=line.split(':')[0] + ":",
                                font=("Arial", 10),
                                bg=self.COLOR_BLANCO)
                    label.pack(side='left')
                    
                    amount = tk.Label(amount_frame,
                                    text=line.split(':')[1],
                                    font=("Arial", 10, "bold"),
                                    bg=self.COLOR_BLANCO)
                    amount.pack(side='right')
                    continue
                    
                # Artículos normales
                if line and not line.startswith("----"):
                    item_frame = tk.Frame(items_frame, bg=self.COLOR_BLANCO)
                    item_frame.pack(fill='x', pady=2)
                    
                    try:
                        qty, desc, price = line.split(None, 2)
                        
                        qty_label = tk.Label(item_frame,
                                        text=qty,
                                        font=("Arial", 10),
                                        bg=self.COLOR_BLANCO)
                        qty_label.pack(side='left', padx=(0, 10))
                        
                        desc_label = tk.Label(item_frame,
                                            text=desc,
                                            font=("Arial", 10),
                                            bg=self.COLOR_BLANCO)
                        desc_label.pack(side='left', expand=True, anchor='w')
                        
                        price_label = tk.Label(item_frame,
                                            text=price,
                                            font=("Arial", 10),
                                            bg=self.COLOR_BLANCO)
                        price_label.pack(side='right')
                    except ValueError:
                        # Si la línea no tiene el formato esperado, mostrarla completa
                        tk.Label(item_frame,
                                text=line,
                                font=("Arial", 10),
                                bg=self.COLOR_BLANCO).pack(anchor='w')
        
        # Configurar el scrolling
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas.find_withtag("all")[0], width=canvas.winfo_width())
        
        items_frame.bind('<Configure>', _on_frame_configure)
        
        # Botón de cerrar
        close_button = tk.Button(main_frame,
                                text="Cerrar",
                                command=detail_window.destroy,
                                bg=self.COLOR_ROJO,
                                fg=self.COLOR_BLANCO,
                                relief='flat',
                                padx=20)
        close_button.pack(pady=20)
        
        # Hacer la ventana modal
        detail_window.transient(self.top)
        detail_window.grab_set()
    
class CobranzaApp:
    def __init__(self, root):
        self.root = root
        self.images = {}
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
        
    def load_image(self, path, size=None):
        """Método para cargar y mantener referencia a las imágenes"""
        try:
            image = Image.open(path)
            if size:
                image = image.resize(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            # Guardar referencia
            self.images[path] = photo
            return photo
        except Exception as e:
            logging.error(f"Error loading image {path}: {e}")
            return None
    
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
        
        # Calcular deuda total
        deuda_total = sum(cliente['saldo'] for cliente in self.clientes_data.values())
        
        # Frame para la deuda total
        deuda_frame = tk.Frame(header_frame, bg=self.COLOR_ROJO)
        deuda_frame.pack(side='right', padx=20)
        
        deuda_label = tk.Label(deuda_frame,
                            text="Deuda Total:",
                            font=("Arial", 12, "bold"),
                            bg=self.COLOR_ROJO,
                            fg=self.COLOR_BLANCO)
        deuda_label.pack(side='left', padx=(0, 10))
        
        deuda_monto = tk.Label(deuda_frame,
                            text=f"${deuda_total:,.2f}",
                            font=("Arial", 12, "bold"),
                            bg=self.COLOR_ROJO,
                            fg=self.COLOR_BLANCO)
        deuda_monto.pack(side='left')
        
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
        bat_file = r'C:\Users\USER\Documents\GitHub\chatbotwapp\run_whatsapp_bot.bat'
        os.startfile(bat_file)
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
                return "verde"
            elif diferencia.days >= 30 and diferencia.days < 60:
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
        self.create_category_section(categories_container, "ACUERDO DE PAGO / MENOS DE 30 DIAS", self.COLOR_VERDE, 0)
        self.create_category_section(categories_container, "30 A 60 DIAS", self.COLOR_AMARILLO, 1)
        self.create_category_section(categories_container, "MAS DE 60 DIAS", self.COLOR_ROJO, 2)
        
        # Frame para detalles del cliente (derecha - 1/3 del ancho)
        self.detalles_frame = tk.LabelFrame(self.main_frame,
                                          text="ADEUDO",
                                          font=("Arial", 16, "bold"),
                                          bg=self.COLOR_BLANCO)
        self.detalles_frame.pack(side='right', fill='both', expand=True, padx=(10,0))

    def create_category_section(self, parent, title, color, row):
        """
        Crea una sección de categoría en la interfaz.
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
        visible_columns = ('Nombre', 'Monto', 'Fecha de compra', 'Días vencidos')
        tree = ttk.Treeview(category_frame, columns=('Clave',) + ('Nombre', 'Monto', 'Fecha', 'Dias'), show='headings')
        
        # Configurar columnas - la columna Clave tiene width=0 para ocultarla
        tree.column('Clave', width=0, stretch=False)
        tree.column('Nombre', width=250, minwidth=250)
        tree.column('Monto', width=100, minwidth=100)
        tree.column('Fecha', width=100, minwidth=100)
        tree.column('Dias', width=100, minwidth=100)
        
        # Configurar headings
        tree.heading('Nombre', text='Nombre')
        tree.heading('Monto', text='Monto')
        tree.heading('Fecha', text='Fecha de compra')
        tree.heading('Dias', text='Días vencidos')
        
        # Estilo para el Treeview
        style = ttk.Style()
        style.configure("Treeview",
                    background=self.COLOR_BLANCO,
                    foreground=self.COLOR_NEGRO,
                    fieldbackground=self.COLOR_BLANCO)
        
        # Fecha actual
        fecha_actual = datetime.now()
        
        # Insertar datos según la categoría
        for clave, cliente in self.clientes_data.items():
            categoria = self.categorizar_cliente(clave)
            if ((color == self.COLOR_VERDE and categoria == "verde") or
                (color == self.COLOR_AMARILLO and categoria == "amarillo") or
                (color == self.COLOR_ROJO and categoria == "rojo")):
                
                fecha_antigua = self.obtener_fecha_venta_antigua(clave)
                if fecha_antigua:
                    fecha_str = fecha_antigua.strftime("%Y-%m-%d")
                    # Calcular días vencidos
                    delta = fecha_actual - fecha_antigua
                    dias_vencidos = delta.days
                else:
                    fecha_str = "N/A"
                    dias_vencidos = "N/A"
                
                tree.insert('', 'end', values=(
                    clave,  # Se mantiene pero no se muestra
                    cliente['nombre'],
                    f"${cliente['saldo']:,.2f}",
                    fecha_str,
                    dias_vencidos if dias_vencidos != "N/A" else "N/A"
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

def iniciar_aplicacion():
    def launch_main_app():
        root = tk.Tk()
        app = CobranzaApp(root)
        root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root))
        root.mainloop()

    def on_closing(root):
        """Manejador para el cierre de la ventana"""
        try:
            # Limpiar recursos
            if hasattr(root, 'splash_references'):
                del root.splash_references
            root.destroy()
        except Exception as e:
            logging.error(f"Error during window closing: {e}")

    def proceso_carga():
        try:
            splash.update_status("Actualizando datos...")
            actualizar_datos()
            splash.update_status("¡Actualización completada!")
            time.sleep(1)
            
            # Cerrar splash y iniciar app principal
            root_splash.after(0, lambda: [
                splash.stop_progress(),
                splash.destroy(),
                launch_main_app()
            ])
            
        except Exception as e:
            splash.update_status(f"Error: {str(e)}")
            time.sleep(3)
            root_splash.destroy()

    # Iniciar splash screen
    root_splash = tk.Tk()
    splash = LoadingSplash(root_splash)
    splash.start_progress()

    # Iniciar proceso de carga en thread separado
    threading.Thread(target=proceso_carga, daemon=True).start()
    root_splash.mainloop()

if __name__ == "__main__":
    iniciar_aplicacion()
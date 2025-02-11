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
from datetime import date, datetime
import re
from database import validate_user, get_client_states, get_db_connection, get_clients_data, update_promise_date, sync_clients_to_buro, get_clients_without_credit
import logging
from tkinter import messagebox
from typing import Dict, Optional
import pyodbc
import threading
import time
import socketio
from tkcalendar import Calendar
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

class UserSession:
    """Clase singleton para manejar la sesión del usuario"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserSession, cls).__new__(cls)
            cls._instance.username = None
            cls._instance.login_time = None
        return cls._instance
    
    @classmethod
    def set_user(cls, username):
        instance = cls()
        instance.username = username
        instance.login_time = datetime.now()
    
    @classmethod
    def get_user(cls):
        instance = cls()
        return instance.username
    
    @classmethod
    def is_logged_in(cls):
        instance = cls()
        return instance.username is not None

class LoadingSplash:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Cobranza")
        self.user_session = UserSession()
        
        # Configuración de la ventana
        window_width = 350
        window_height = 450
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Colores y estilos
        self.COLORS = {
            'primary': '#e31837',      # Rojo Empresa color
            'secondary': '#f8f9fa',    # Gris muy claro
            'text': '#202124',         # Casi negro
            'error': '#d93025',        # Rojo error
            'white': '#ffffff',        # Blanco
            'border': '#dadce0'        # Gris borde
        }
        
        # Configuración de la ventana
        self.root.overrideredirect(True)
        self.root.configure(bg=self.COLORS['white'])
        
        # Crear borde personalizado
        self.create_window_border()
        
        # Frame principal con sombra
        self.main_frame = tk.Frame(
            self.root,
            bg=self.COLORS['white'],
            highlightbackground=self.COLORS['border'],
            highlightthickness=1
        )
        self.main_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Logo o título
        self.create_header()
        
        # Frame de carga
        self.loading_frame = tk.Frame(self.main_frame, bg=self.COLORS['white'])
        self.loading_frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        # Status y progreso
        self.create_loading_widgets()
        
        # Frame de login
        self.create_login_frame()
        
        # Ocultar login inicialmente
        self.login_frame.pack_forget()

    def create_window_border(self):
        """Crea una barra de título personalizada"""
        title_bar = tk.Frame(
            self.root,
            bg=self.COLORS['primary'],
            height=30
        )
        title_bar.pack(fill='x')
        
        # Título
        title_label = tk.Label(
            title_bar,
            text="Sistema de Cobranza",
            bg=self.COLORS['primary'],
            fg=self.COLORS['white'],
            font=('Segoe UI', 10)
        )
        title_label.pack(side='left', padx=10)
        
        
        # Botón cerrar
        close_button = tk.Label(
            title_bar,
            text="×",
            bg=self.COLORS['primary'],
            fg=self.COLORS['white'],
            font=('Segoe UI', 13, 'bold'),
            cursor='hand2'
        )
        close_button.pack(side='right', padx=10)
        close_button.bind('<Button-1>', lambda e: self.root.destroy())
        
        # Hacer la ventana arrastrable
        title_bar.bind('<Button-1>', self.start_move)
        title_bar.bind('<B1-Motion>', self.on_move)

    def create_header(self):
            """Crea el encabezado con logo"""
            header_frame = tk.Frame(self.main_frame, bg=self.COLORS['white'])
            header_frame.pack(fill='x', pady=20)
            
            # Aquí podrías agregar un logo real
            logo_label = tk.Label(
                header_frame,
                text="📊",  # Emoji como placeholder del logo
                font=('Segoe UI', 36),
                bg=self.COLORS['white'],
                fg=self.COLORS['primary']
            )
            logo_label.pack()
            
            company_label = tk.Label(
                header_frame,
                text="Sistema de Cobranza",
                font=('Segoe UI', 14, 'bold'),
                bg=self.COLORS['white'],
                fg=self.COLORS['text']
            )
            company_label.pack(pady=(5,0))
            
            # Añadimos el subtítulo
            subtitle_label = tk.Label(
                header_frame,
                text="Garcia Automotriz",
                font=('Segoe UI', 12),  # Fuente un poco más pequeña que el título
                bg=self.COLORS['white'],
                fg=self.COLORS['text']
            )
            subtitle_label.pack(pady=(2,0))

    def create_loading_widgets(self):
        """Crea los widgets de carga con estilo moderno"""
        self.status_label = tk.Label(
            self.loading_frame,
            text="Actualizando datos...",
            font=('Segoe UI', 10),
            bg=self.COLORS['white'],
            fg=self.COLORS['text']
        )
        self.status_label.pack(pady=10)
        
        # Frame para la barra de progreso con fondo gris
        progress_frame = tk.Frame(
            self.loading_frame,
            bg=self.COLORS['secondary'],
            height=6,
            width=200
        )
        progress_frame.pack(pady=10)
        progress_frame.pack_propagate(False)
        
        # Barra de progreso moderna
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=200,
            style='Modern.Horizontal.TProgressbar'
        )
        self.progress.pack(expand=True, fill='both')
        
        # Configurar estilo de la barra de progreso
        style = ttk.Style()
        style.configure(
            'Modern.Horizontal.TProgressbar',
            troughcolor=self.COLORS['secondary'],
            background=self.COLORS['primary'],
            thickness=6
        )
        
        self.message = tk.Label(
            self.loading_frame,
            text="Por favor espere mientras se actualizan los datos",
            font=('Segoe UI', 9),
            fg=self.COLORS['text'],
            bg=self.COLORS['white'],
            wraplength=250,
            justify='center'
        )
        self.message.pack(pady=10)

    def create_login_frame(self):
        """Crea el frame de login con diseño moderno"""
        self.login_frame = tk.Frame(self.main_frame, bg=self.COLORS['white'])
        self.login_frame.pack(fill='x', pady=10, padx=20)
        
        # Frame para el campo de entrada
        entry_frame = tk.Frame(
            self.login_frame,
            bg=self.COLORS['white'],
            highlightbackground=self.COLORS['border'],
            highlightthickness=1
        )
        entry_frame.pack(fill='x', pady=5)
        
        # Icono de usuario
        user_icon = tk.Label(
            entry_frame,
            text="👤",  # Emoji como placeholder
            font=('Segoe UI', 12),
            bg=self.COLORS['white']
        )
        user_icon.pack(side='left', padx=5)
        
        # Campo de entrada
        self.login_var = tk.StringVar()
        self.login_entry = tk.Entry(
            entry_frame,
            textvariable=self.login_var,
            font=('Segoe UI', 10),
            show="●",
            bd=0,
            bg=self.COLORS['white']
        )
        self.login_entry.pack(side='left', fill='x', expand=True, padx=5, pady=8)
        
        # Mensaje de error
        self.error_label = tk.Label(
            self.login_frame,
            text="",
            font=('Segoe UI', 8),
            fg=self.COLORS['error'],
            bg=self.COLORS['white']
        )
        self.error_label.pack(pady=5)
        
        # Bind eventos
        self.login_entry.bind('<Return>', self.attempt_login)
        
        # Hover effects para el entry frame
        entry_frame.bind('<Enter>', lambda e: entry_frame.configure(highlightbackground=self.COLORS['primary']))
        entry_frame.bind('<Leave>', lambda e: entry_frame.configure(highlightbackground=self.COLORS['border']))

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def show_login(self):
        self.message.config(text="Ingrese Usuario y Contraseña")
        self.login_frame.pack(fill='x', pady=10)
        self.login_entry.focus()
        
    def attempt_login(self, event=None):
        credentials = self.login_var.get().strip().upper()
        if validate_user(credentials):
            username = credentials.split()[0]
            UserSession.set_user(username)
            self.root.quit()
        else:
            self.error_label.config(text="Credenciales inválidas")
            self.login_var.set("")
            
    def start_progress(self):
        self.progress.start(10)
    
    def stop_progress(self):
        self.progress.stop()
        
    def update_status(self, text):
        self.status_label.config(text=text)
        
    def destroy(self):
        if hasattr(self.root, 'splash_references'):
            del self.root.splash_references
        self.root.destroy()


class DetalleClienteWindow:
    def __init__(self, parent, client_data, client_id):
        self.top = tk.Toplevel(parent)
        self.client_data = client_data
        self.client_id = client_id
        self.setup_window()

        # Inicializar el socket como None
        self.sio = None
        # Verificar si el servidor de WhatsApp está disponible
        self.whatsapp_available = self.check_whatsapp_server()
        if self.whatsapp_available:
            self.setup_socket_connection()
        
        # Configurar listeners de socket
        self.setup_socket_listeners()
        
            # Intentar conectar al servidor de socket sin mostrar error
        try:
            if self.sio:  # Solo intentar conectar si sio existe
                self.sio.connect('http://localhost:3000')
        except Exception as e:
            logging.debug(f"No se pudo conectar con WhatsApp: {str(e)}")
            self.whatsapp_available = False
            self.sio = None
        
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

    def check_whatsapp_server(self):
            """Verifica si el servidor de WhatsApp está disponible"""
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', 3000))
                sock.close()
                return result == 0
            except Exception as e:
                logging.debug(f"WhatsApp server no disponible: {str(e)}")
                return False
    def setup_socket_connection(self):
        """Configura la conexión del socket si el servidor está disponible"""
        try:
            self.sio = socketio.Client()
            
            # Configurar listeners solo si self.sio existe
            if self.sio is not None:
                @self.sio.on('chat-opened')
                def on_chat_opened(data):
                    if data.get('success'):
                        messagebox.showinfo("Éxito", "Chat de WhatsApp abierto")
            
            self.sio.connect('http://localhost:3000')
            
        except Exception as e:
            logging.debug(f"No se pudo establecer conexión con WhatsApp: {str(e)}")
            self.sio = None
            self.whatsapp_available = False
    def setup_window(self):
        """Configura la ventana de detalles"""
        self.top.title(f"Detalle Cliente - {self.client_data.get('nombre', 'Sin nombre')}")
        window_width = 1000
        window_height = 950
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

        # Botón de agregar nota con estilo mejorado
        add_note_btn = tk.Button(control_container, 
                            text="+ Agregar Nota",
                            font=("Arial", 10, "bold"),
                            bg=self.COLOR_BLANCO,
                            fg=self.COLOR_NEGRO,
                            bd=0,
                            relief="flat",
                            padx=15,
                            pady=8,
                            width=15,
                            cursor="hand2",
                            command=lambda: self.show_note_dialog(self.client_id))
        
        add_note_btn.pack(pady=(0,10))

        # Eventos hover para el botón de nota
        def on_enter_note(e):
            add_note_btn['bg'] = self.COLOR_GRIS_HOVER
        def on_leave_note(e):
            add_note_btn['bg'] = self.COLOR_BLANCO

        add_note_btn.bind("<Enter>", on_enter_note)
        add_note_btn.bind("<Leave>", on_leave_note)

        # Nuevos botones para notas rápidas
        quick_notes = [
            ("Buzón", "Mandó a buzón de voz"),
            ("No disponible", "El número marcado no está disponible"),
            ("Notifico a Whats", "Se le notifico via whatsapp")
        ]

        for btn_text, note_text in quick_notes:
            btn = tk.Button(control_container,
                        text=btn_text,
                        font=("Arial", 10),
                        bg=self.COLOR_BLANCO,
                        fg=self.COLOR_NEGRO,
                        bd=0,
                        relief="flat",
                        padx=15,
                        pady=8,
                        width=15,
                        cursor="hand2",
                        command=lambda t=note_text: self.create_quick_note(t))
            btn.pack(pady=(0,10))

            # Eventos hover para cada botón
            def on_enter(e, button=btn):
                button['bg'] = self.COLOR_GRIS_HOVER
            def on_leave(e, button=btn):
                button['bg'] = self.COLOR_BLANCO

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        # Separador visual
        separator = tk.Frame(control_container, height=1, bg=self.COLOR_GRIS_HOVER)
        separator.pack(fill='x', pady=10)

        calendar_btn = tk.Button(control_container,
                            text="Fecha Promesa",
                            font=("Arial", 10, "bold"),
                            bg=self.COLOR_BLANCO,
                            fg=self.COLOR_NEGRO,
                            bd=0,
                            relief="flat",
                            padx=15,
                            pady=8,
                            width=15,
                            cursor="hand2",
                            command=self.show_calendar_dialog)
        
        calendar_btn.pack(pady=(0,10))
        
        # Eventos hover para el botón de calendario
        def on_enter_calendar(e):
            calendar_btn['bg'] = self.COLOR_GRIS_HOVER
        def on_leave_calendar(e):
            calendar_btn['bg'] = self.COLOR_BLANCO
        
        calendar_btn.bind("<Enter>", on_enter_calendar)
        calendar_btn.bind("<Leave>", on_leave_calendar)

        # Separador visual
        separator2 = tk.Frame(control_container, height=1, bg=self.COLOR_GRIS_HOVER)
        separator2.pack(fill='x', pady=10)

        # Botón de Company con estilo mejorado
        company_state = self.get_company_state(self.client_id)
        company_text = "No es empresa" if company_state else "Empresa"
        company_color = self.COLOR_ROJO if company_state else self.COLOR_BLANCO
        company_text_color = self.COLOR_BLANCO if company_state else self.COLOR_NEGRO
        
        self.company_btn = tk.Button(control_container,
                                text=company_text,
                                font=("Arial", 10, "bold"),
                                bg=company_color,
                                fg=company_text_color,
                                bd=0,
                                relief="flat",
                                padx=15,
                                pady=8,
                                width=15,
                                cursor="hand2",
                                command=lambda: self.toggle_company(self.client_id))
        
        self.company_btn.pack(pady=(0,10))

        # Configurar eventos hover para el botón de company
        def on_enter_company(e):
            if not company_state:
                self.company_btn['bg'] = self.COLOR_GRIS_HOVER
            else:
                self.company_btn['bg'] = self.COLOR_ROJO_HOVER
        
        def on_leave_company(e):
            if not company_state:
                self.company_btn['bg'] = self.COLOR_BLANCO
            else:
                self.company_btn['bg'] = self.COLOR_ROJO

        self.company_btn.bind("<Enter>", on_enter_company)
        self.company_btn.bind("<Leave>", on_leave_company)

        # Separador visual
        separator3 = tk.Frame(control_container, height=1, bg=self.COLOR_GRIS_HOVER)
        separator3.pack(fill='x', pady=10)

        # Botón de WhatsApp
        whatsapp_btn = tk.Button(control_container, 
                            text="Abrir Chat WhatsApp",
                            font=("Arial", 10, "bold"),
                            bg=self.COLOR_BLANCO,
                            fg=self.COLOR_NEGRO,
                            bd=0,
                            relief="flat",
                            padx=15,
                            pady=8,
                            width=15,
                            cursor="hand2",
                            command=self.abrir_chat_whatsapp)
        
        whatsapp_btn.pack(pady=(0,10))

        # Eventos hover para el botón de WhatsApp
        def on_enter(e):
            whatsapp_btn['bg'] = self.COLOR_GRIS_HOVER
        def on_leave(e):
            whatsapp_btn['bg'] = self.COLOR_BLANCO

        whatsapp_btn.bind("<Enter>", on_enter)
        whatsapp_btn.bind("<Leave>", on_leave)

        # Buro state
        buro_state = self.get_buro_state(self.client_id)
        buro_text = "En Buro" if buro_state else "Buro"
        buro_color = self.COLOR_ROJO if buro_state else self.COLOR_BLANCO
        buro_text_color = self.COLOR_BLANCO if buro_state else self.COLOR_NEGRO

        self.buro_btn = tk.Button(control_container,
                                text=buro_text,
                                font=("Arial", 10, "bold"),
                                bg=buro_color,
                                fg=buro_text_color,
                                bd=0,
                                relief="flat",
                                padx=15,
                                pady=8,
                                width=15,
                                cursor="hand2",
                                command=lambda: self.toggle_buro(self.client_id))

        self.buro_btn.pack(pady=(0,10))

        # Configurar eventos hover para el botón de buro
        def on_enter_buro(e):
            if not buro_state:
                self.buro_btn['bg'] = self.COLOR_GRIS_HOVER
            else:
                self.buro_btn['bg'] = self.COLOR_ROJO_HOVER

        def on_leave_buro(e):
            if not buro_state:
                self.buro_btn['bg'] = self.COLOR_BLANCO
            else:
                self.buro_btn['bg'] = self.COLOR_ROJO

        self.buro_btn.bind("<Enter>", on_enter_buro)
        self.buro_btn.bind("<Leave>", on_leave_buro)

        # Separador visual
        separator4 = tk.Frame(control_container, height=1, bg=self.COLOR_GRIS_HOVER)
        separator4.pack(fill='x', pady=10)
    def __del__(self):
        """Limpieza al cerrar la ventana"""
        if hasattr(self, 'sio') and self.sio is not None:
            try:
                self.sio.disconnect()
            except:
                pass

    def create_quick_note(self, note_text):
        """Crea una nota rápida sin mostrar el diálogo"""
        if self.save_note_to_db(self.client_id, note_text):
            # Obtener las notas actualizadas y actualizar la interfaz
            notes = self.get_client_notes(self.client_id)
            self.refresh_notes_display(notes)
        else:
            tk.messagebox.showerror("Error", "No se pudo guardar la nota")
    def setup_socket_listeners(self):
        """Configura los listeners del socket solo si está disponible"""
        if self.sio is None:
            return
            
        @self.sio.on('chat-opened')
        def on_chat_opened(data):
            if data.get('success'):
                messagebox.showinfo("Éxito", "Chat de WhatsApp abierto")
            else:
                messagebox.showinfo("Información", 
                                  "No se pudo abrir el chat de WhatsApp.\n" +
                                  "Por favor, verifique que WhatsApp esté abierto.")
    def formatear_telefono(self, telefono):
        """
        Formatea un número de teléfono para uso en WhatsApp Web.

        Elimina todos los caracteres no numéricos y agrega el prefijo de país 521.

        Args:
            telefono (str): Número de teléfono a formatear.

        Returns:
            str: Número de teléfono formateado con prefijo 521.
        """
        # Elimina todos los caracteres no numéricos
        cleaned = ''.join(filter(str.isdigit, telefono))
        
        # Agrega el prefijo 521 si no está presente
        formatted = f"521{cleaned}" if not cleaned.startswith('52') else cleaned
        
        return formatted

    def get_company_state(self, client_id):
        """Obtiene el estado actual de company"""
        try:
            conn = get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("SELECT company FROM dbo.ClientsStates WHERE client_id = ?", (client_id,))
            result = cursor.fetchone()
            
            if result:
                return bool(result.company)
            else:
                return False
        except pyodbc.Error as e:
            logging.error(f"Error al obtener estado de company: {e}")
            return False
        finally:
            if conn:
                conn.close()
    def toggle_company(self, client_id):
        """Alterna el estado de company con actualización visual"""
        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT company FROM dbo.ClientsStates WHERE client_id = ?", (client_id,))
            current_state = cursor.fetchone()

            if current_state is not None:
                new_state = not bool(current_state.company)
                cursor.execute("""
                    UPDATE dbo.ClientsStates 
                    SET company = ?
                    WHERE client_id = ?
                """, (new_state, client_id))
                conn.commit()

                # Actualizar el botón con los nuevos estilos
                new_text = "No es empresa" if new_state else "Empresa"
                new_bg_color = self.COLOR_ROJO if new_state else self.COLOR_BLANCO
                new_fg_color = self.COLOR_BLANCO if new_state else self.COLOR_NEGRO
                
                self.company_btn.configure(
                    text=new_text,
                    bg=new_bg_color,
                    fg=new_fg_color
                )

                # Actualizar los eventos hover
                def on_enter(e):
                    if new_state:
                        self.company_btn['bg'] = self.COLOR_ROJO_HOVER
                    else:
                        self.company_btn['bg'] = self.COLOR_GRIS_HOVER

                def on_leave(e):
                    self.company_btn['bg'] = new_bg_color

                self.company_btn.bind("<Enter>", on_enter)
                self.company_btn.bind("<Leave>", on_leave)

        except pyodbc.Error as e:
            logging.error(f"Error al actualizar estado de company: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_buro_state(self, client_id):
        """Obtiene el estado actual de buro de crédito"""
        try:
            conn = get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("SELECT credit FROM dbo.ClientsBuro WHERE client_id = ?", (client_id,))
            result = cursor.fetchone()
            
            if result:
                return bool(result.credit)
            else:
                return False
        except pyodbc.Error as e:
            logging.error(f"Error al obtener estado de buro de crédito: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def toggle_buro(self, client_id):
        """Alterna el estado de buro de crédito con actualización visual"""
        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT credit FROM dbo.ClientsBuro WHERE client_id = ?", (client_id,))
            current_state = cursor.fetchone()

            if current_state is not None:
                new_state = not bool(current_state.credit)
                cursor.execute("""
                    UPDATE dbo.ClientsBuro 
                    SET credit = ?
                    WHERE client_id = ?
                """, (new_state, client_id))
                conn.commit()

                # Actualizar el botón con los nuevos estilos
                new_text = "En Buro" if new_state else "Buro"
                new_bg_color = self.COLOR_ROJO if new_state else self.COLOR_BLANCO
                new_fg_color = self.COLOR_BLANCO if new_state else self.COLOR_NEGRO
                
                self.buro_btn.configure(
                    text=new_text,
                    bg=new_bg_color,
                    fg=new_fg_color
                )

                # Actualizar los eventos hover
                def on_enter(e):
                    if new_state:
                        self.buro_btn['bg'] = self.COLOR_ROJO_HOVER
                    else:
                        self.buro_btn['bg'] = self.COLOR_GRIS_HOVER

                def on_leave(e):
                    self.buro_btn['bg'] = new_bg_color

                self.buro_btn.bind("<Enter>", on_enter)
                self.buro_btn.bind("<Leave>", on_leave)

        except pyodbc.Error as e:
            logging.error(f"Error al actualizar estado de buro de crédito: {e}")
        finally:
            if conn:
                conn.close()
    def abrir_chat_whatsapp(self, telefono=None):
        """Abre un chat de WhatsApp solo si el servidor está disponible"""
        if telefono is None:
            telefono = self.client_data.get('telefono1')
        
        if not telefono:
            return

        # Verificar si WhatsApp está disponible
        if not self.whatsapp_available or self.sio is None:
            return
                
        try:
            telefono_formateado = self.formatear_telefono(telefono)
            if self.sio and self.sio.connected:
                self.sio.emit('open-chat', telefono_formateado)
        except Exception as e:
            logging.debug(f"Error al abrir chat: {str(e)}")
    
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
        """Crea el frame principal de la timeline con scroll"""
        timeline_frame = tk.LabelFrame(self.left_frame, text="LINEA DE TIEMPO", 
                                    font=("Arial", 16, "bold"), bg=self.COLOR_BLANCO)
        timeline_frame.pack(fill='x', padx=20, pady=10)

        # Crear un frame con altura fija
        fixed_height_frame = tk.Frame(timeline_frame, height=400, bg=self.COLOR_BLANCO)
        fixed_height_frame.pack(fill='x', expand=True)
        fixed_height_frame.pack_propagate(False)  # Mantener altura fija

        # Canvas y scrollbar para el contenido - Asignar a self
        self.canvas = tk.Canvas(fixed_height_frame, bg=self.COLOR_BLANCO)
        self.scrollbar = ttk.Scrollbar(fixed_height_frame, orient="vertical", command=self.canvas.yview)
        
        # Frame interior para el contenido
        self.interior_frame = tk.Frame(self.canvas, bg=self.COLOR_BLANCO)
        
        # Configurar el scroll
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Empaquetar los widgets
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Crear ventana en el canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.interior_frame, anchor="nw")

        # Configurar el scroll para que se ajuste al contenido
        def configure_scroll(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # Asegurar que el ancho del frame interior coincida con el canvas
            self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())

        self.interior_frame.bind('<Configure>', configure_scroll)
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width()))

        # Crear las secciones dentro del interior_frame
        states_section = tk.Frame(self.interior_frame, bg=self.COLOR_BLANCO)
        states_section.pack(fill='x', expand=True)
        self.create_states_section(states_section, client_id)

        notes_section = tk.Frame(self.interior_frame, bg=self.COLOR_BLANCO)
        notes_section.pack(fill='x', expand=True, pady=(20, 0))
        self.create_notes_section(notes_section, client_id)

        # Agregar bind para el mousewheel
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
        
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
        """Obtiene todas las notas de un cliente específico incluyendo el usuario que las creó"""
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            query = """
                SELECT id, note_text, created_at, user_name
                FROM Notes
                WHERE client_id = ?
                ORDER BY created_at DESC
            """
            cursor.execute(query, (client_id,))
            notes = []
            rows = cursor.fetchall()
            
            for row in rows:
                note = {
                    'id': row[0],
                    'text': row[1],
                    'timestamp': row[2],
                    'user_name': row[3]  # Agregamos el usuario
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
        """Actualiza la visualización de las notas incluyendo el usuario"""
        # Limpiar el contenedor de notas actual
        for widget in self.notes_container.winfo_children():
            widget.destroy()

        # Crear nuevos widgets para cada nota
        for note in notes:
            # Frame principal de la nota con fondo gris claro
            note_frame = tk.Frame(self.notes_container, bg=self.COLOR_GRIS_CLARO)
            note_frame.pack(fill='x', padx=20, pady=10)
            note_frame.grid_columnconfigure(1, weight=1)

            # Frame para la marca de tiempo y usuario
            timestamp_frame = tk.Frame(note_frame, bg=self.COLOR_GRIS_CLARO)
            timestamp_frame.grid(row=0, column=0, padx=10, sticky='nw')

            # Etiqueta de tiempo
            timestamp = note['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            tk.Label(timestamp_frame, 
                    text=f"Nota del {timestamp}", 
                    font=("Arial", 10, "bold"), 
                    bg=self.COLOR_GRIS_CLARO).pack(anchor='w')
            
            # Etiqueta de usuario
            tk.Label(timestamp_frame,
                    text=f"Por: {note['user_name']}", 
                    font=("Arial", 9, "italic"),
                    bg=self.COLOR_GRIS_CLARO).pack(anchor='w')

            # Frame para el texto de la nota
            text_frame = tk.Frame(note_frame, bg=self.COLOR_GRIS_CLARO)
            text_frame.grid(row=0, column=1, padx=(0, 10), sticky='ew')
            text_frame.grid_columnconfigure(0, weight=1)

            # Etiqueta del texto de la nota con ajuste de línea
            note_text = tk.Label(text_frame, 
                            text=note['text'], 
                            font=("Arial", 10), 
                            bg=self.COLOR_GRIS_CLARO,
                            justify='left',
                            anchor='w',
                            wraplength=400)
            note_text.grid(row=0, column=0, sticky='ew')

        # Actualizar el canvas para mostrar las nuevas notas
        self.interior_frame.update_idletasks()
        if hasattr(self, 'canvas'):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def save_note_to_db(self, client_id, note_text):
        """Guarda una nueva nota en la base de datos incluyendo el usuario"""
        conn = get_db_connection()
        if not conn:
            return False

        try:
            # Obtener el usuario actual
            current_user = UserSession.get_user()
            user_name = current_user if current_user else "Sistema"  # Usuario por defecto si no hay sesión
            
            cursor = conn.cursor()
            query = """
                INSERT INTO Notes (client_id, note_text, user_name)
                VALUES (?, ?, ?)
            """
            cursor.execute(query, (client_id, note_text, user_name))
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
    
    #############################################################################################
    
    def show_calendar_dialog(self):
        """Muestra un diálogo con un calendario para seleccionar la fecha de promesa"""
        dialog = tk.Toplevel(self.top)
        dialog.title("Seleccionar Fecha de Promesa")
        dialog.configure(bg=self.COLOR_BLANCO)
        
        # Hacer la ventana modal
        dialog.transient(self.top)
        dialog.grab_set()
        
        # Configurar tamaño y posición
        dialog_width = 300
        dialog_height = 400
        parent_x = self.top.winfo_x()
        parent_y = self.top.winfo_y()
        parent_width = self.top.winfo_width()
        parent_height = self.top.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Frame principal
        main_frame = tk.Frame(dialog, bg=self.COLOR_BLANCO)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(main_frame,
                            text="Seleccione la fecha de promesa",
                            font=("Arial", 12, "bold"),
                            bg=self.COLOR_BLANCO)
        title_label.pack(pady=(0, 10))
        
        # Calendario con la fecha mínima corregida
        cal = Calendar(main_frame,
                    selectmode='day',
                    date_pattern='yyyy-mm-dd',
                    mindate=date.today(),
                    locale='es_ES')
            
        cal.pack(pady=10)
        
        # Después del calendario, agregar el selector de método de pago
        payment_frame = tk.Frame(main_frame, bg=self.COLOR_BLANCO)
        payment_frame.pack(fill='x', pady=10)
        
        payment_label = tk.Label(payment_frame,
                            text="Método de pago:",
                            font=("Arial", 10),
                            bg=self.COLOR_BLANCO)
        payment_label.pack(side='left', padx=5)
        
        # Variable para almacenar la selección del método de pago
        payment_method = tk.StringVar(value="No especificado")
        
        # Crear el menú desplegable
        payment_select = ttk.Combobox(payment_frame,
                                    textvariable=payment_method,
                                    values=["Efectivo", "Tarjeta", "Transferencia", "Cheque", "No especificado"],
                                    state="readonly",
                                    width=15)
        payment_select.pack(side='left', padx=5)
        
        def save_date():
            selected_date = datetime.strptime(cal.get_date(), '%Y-%m-%d').date()
            selected_payment = payment_method.get()
            
            if update_promise_date(self.client_id, selected_date):
                # Crear nota automática con el método de pago
                note_text = f"Promesa de pago generada para el día {selected_date.strftime('%d/%m/%Y')}. Método de pago: {selected_payment}"
                
                if self.save_note_to_db(self.client_id, note_text):
                    notes = self.get_client_notes(self.client_id)
                    self.refresh_notes_display(notes)
                    dialog.destroy()
                    messagebox.showinfo("Éxito", "Fecha de promesa guardada correctamente")
                else:
                    messagebox.showerror("Error", "No se pudo guardar la nota")
            else:
                messagebox.showerror("Error", "No se pudo guardar la fecha de promesa")
        
        # Frame para botones
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
                            command=save_date,
                            font=("Arial", 10, "bold"),
                            bg=self.COLOR_ROJO,
                            fg=self.COLOR_BLANCO,
                            bd=0,
                            padx=15,
                            pady=5,
                            relief="flat",
                            cursor="hand2")
        save_btn.pack(side='right', padx=5)
    
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
        window_width = 420
        window_height = 700  # Aumentado para acomodar el contenido adicional
        screen_width = detail_window.winfo_screenwidth()
        screen_height = detail_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = 0
        detail_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        detail_window.configure(bg=self.COLOR_BLANCO)
        
        # Frame principal con padding y scroll
        main_frame = tk.Frame(detail_window, bg=self.COLOR_BLANCO)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Canvas para scroll
        canvas = tk.Canvas(main_frame, bg=self.COLOR_BLANCO)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg=self.COLOR_BLANCO)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Procesar el contenido del ticket
        lines = ticket_data['datos'].split('\r\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Título de la empresa
            if "GARCIA RINES" in line:
                tk.Label(content_frame, 
                        text=line,
                        font=("Courier", 12, "bold"),
                        bg=self.COLOR_BLANCO).pack(pady=(0, 10))
                continue
                
            # Información del ticket
            if line.startswith("TICKET:"):
                tk.Label(content_frame,
                        text=line,
                        font=("Courier", 10),
                        bg=self.COLOR_BLANCO).pack(anchor='w')
                continue
                
            # Cliente
            if line.startswith("CLIENTE:"):
                tk.Label(content_frame,
                        text=line,
                        font=("Courier", 10),
                        bg=self.COLOR_BLANCO).pack(anchor='w')
                continue
                
            # Encabezados y separadores
            if "CANT" in line and "DESCRIPCION" in line:
                tk.Label(content_frame,
                        text=line,
                        font=("Courier", 10),
                        bg=self.COLOR_BLANCO).pack(anchor='w')
                continue
                
            if "--------" in line or "=======" in line:
                tk.Label(content_frame,
                        text=line,
                        font=("Courier", 10),
                        bg=self.COLOR_BLANCO).pack(fill='x')
                continue
                
            # Artículos y montos
            if "ARTICULOS" in line or "IMPORTE:" in line or "ADEUDA:" in line:
                tk.Label(content_frame,
                        text=line,
                        font=("Courier", 10),
                        bg=self.COLOR_BLANCO,
                        justify='right').pack(anchor='e')
                continue
                
            # Pagaré
            if "DEBO Y PAGARE" in line:
                current_section = "pagare"
                
            if current_section == "pagare":
                tk.Label(content_frame,
                        text=line,
                        font=("Courier", 10),
                        bg=self.COLOR_BLANCO).pack(anchor='center')
                if "ACEPTO" in line:
                    current_section = None
                continue
                
            # Líneas normales (artículos y otros)
            tk.Label(content_frame,
                    text=line,
                    font=("Courier", 10),
                    bg=self.COLOR_BLANCO,
                    justify='left').pack(anchor='w')
        
        # Configurar el scrolling
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        content_frame.bind('<Configure>', _on_frame_configure)
        
        # Botón de cerrar
        close_button = tk.Button(detail_window,
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
        self.COLOR_AZUL = "#87CEEB"
        
        # Variable para controlar vista actual
        self.current_view = "clientes"
        
        # Configurar la ventana principal
        self.setup_window()
        
        # Inicializar datos
        self.clientes_data = {}
        self.load_initial_data()
        
        # Variable para almacenar la referencia al main_frame
        self.main_frame = None
        
        self.create_header()
        self.create_view_buttons()
        self.create_main_content()
        

    def load_image(self, path, size=None, keep_aspect=True):
        """
        Método mejorado para cargar y redimensionar imágenes manteniendo la calidad
        
        Args:
            path (str): Ruta de la imagen
            size (tuple): Tupla con el tamaño deseado (width, height)
            keep_aspect (bool): Mantener la relación de aspecto
        
        Returns:
            PhotoImage: Imagen procesada para Tkinter
        """
        try:
            image = Image.open(path)
            
            if size:
                original_width, original_height = image.size
                target_width, target_height = size
                
                if keep_aspect:
                    # Calcular la relación de aspecto
                    aspect_ratio = original_width / original_height
                    
                    # Determinar las nuevas dimensiones manteniendo la relación de aspecto
                    if target_width / target_height > aspect_ratio:
                        # Ajustar por altura
                        new_height = target_height
                        new_width = int(aspect_ratio * new_height)
                    else:
                        # Ajustar por ancho
                        new_width = target_width
                        new_height = int(new_width / aspect_ratio)
                    
                    # Crear un nuevo fondo blanco del tamaño objetivo
                    background = Image.new('RGBA', size, (255, 255, 255, 0))
                    
                    # Redimensionar la imagen original
                    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Calcular la posición para centrar
                    x = (target_width - new_width) // 2
                    y = (target_height - new_height) // 2
                    
                    # Pegar la imagen redimensionada en el centro del fondo
                    background.paste(resized_image, (x, y), resized_image if image.mode == 'RGBA' else None)
                    final_image = background
                else:
                    # Redimensionar directamente si no necesitamos mantener la relación de aspecto
                    final_image = image.resize(size, Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(final_image)
            else:
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
        logo_container = tk.Frame(header_frame, bg=self.COLOR_ROJO)
        logo_container.pack(side='left', pady=10, padx=20)
        
        try:
            # Cargar el logo manteniendo la relación de aspecto
            logo_photo = self.load_image("Logo-Blanco.png", size=(200, 75), keep_aspect=True)
            if logo_photo:
                logo_label = tk.Label(logo_container, image=logo_photo, bg=self.COLOR_ROJO)
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
        
        # Calcular todos los totales
        total_clientes = sum(cliente['saldo'] for clave, cliente in self.clientes_data.items() 
                            if not self.should_show_client(clave))
        total_empresas = sum(cliente['saldo'] for clave, cliente in self.clientes_data.items() 
                            if self.should_show_client(clave))
        
        # Obtener el total de buró
        clientes_buro = get_clients_without_credit()
        total_buro = sum(cliente['saldo'] for cliente in clientes_buro.values())
        
        # Calcular el total general incluyendo buró
        deuda_total = total_clientes + total_empresas + total_buro
        
        # Frame para la deuda total
        deuda_frame = tk.Frame(header_frame, bg=self.COLOR_ROJO)
        deuda_frame.pack(side='right', padx=20)
        
        # Total general
        deuda_label = tk.Label(deuda_frame,
                            text="Deuda Total:",
                            font=("Arial", 12, "bold"),
                            bg=self.COLOR_ROJO,
                            fg=self.COLOR_BLANCO)
        deuda_label.pack(anchor='e', pady=(0,5))
        
        deuda_monto = tk.Label(deuda_frame,
                            text=f"${deuda_total:,.2f}",
                            font=("Arial", 12, "bold"),
                            bg=self.COLOR_ROJO,
                            fg=self.COLOR_BLANCO)
        deuda_monto.pack(anchor='e')
        
        # Desglose por tipo
        clientes_label = tk.Label(deuda_frame,
                            text=f"Clientes: ${total_clientes:,.2f}",
                            font=("Arial", 10),
                            bg=self.COLOR_ROJO,
                            fg=self.COLOR_BLANCO)
        clientes_label.pack(anchor='e')
        
        empresas_label = tk.Label(deuda_frame,
                            text=f"Empresas: ${total_empresas:,.2f}",
                            font=("Arial", 10),
                            bg=self.COLOR_ROJO,
                            fg=self.COLOR_BLANCO)
        empresas_label.pack(anchor='e')
        
        # Agregar el total de buró
        buro_label = tk.Label(deuda_frame,
                            text=f"Buró: ${total_buro:,.2f}",
                            font=("Arial", 10),
                            bg=self.COLOR_ROJO,
                            fg=self.COLOR_BLANCO)
        buro_label.pack(anchor='e')
        
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

    def calcular_total_categoria(self, categoria: str) -> float:
        """Calcula el total de deuda para una categoría específica"""
        total = 0
        for clave, cliente in self.clientes_data.items():
            if not self.should_show_client(clave):
                continue
            if self.categorizar_cliente(clave) == categoria:
                total += cliente['saldo']
        return total
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

    def create_view_buttons(self):
        """Crea los botones de CLIENTES, EMPRESAS y BURO DE CREDITO"""
        buttons_frame = tk.Frame(self.root, bg=self.COLOR_ROJO)
        buttons_frame.pack(fill='x')
        
        # Estilo común para los botones
        button_style = {
            'font': ('Arial', 12, 'bold'),
            'bd': 0,
            'pady': 5,
            'padx': 20,
            'cursor': 'hand2'
        }
        
        # Botón CLIENTES
        self.clientes_btn = tk.Button(
            buttons_frame,
            text="CREDITOS PERSONALES",
            command=lambda: self.switch_view("clientes"),
            bg=self.COLOR_BLANCO if self.current_view == "clientes" else self.COLOR_ROJO,
            fg=self.COLOR_NEGRO if self.current_view == "clientes" else self.COLOR_BLANCO,
            **button_style
        )
        self.clientes_btn.pack(side='left', padx=2)
        
        # Botón EMPRESAS
        self.empresas_btn = tk.Button(
            buttons_frame,
            text="CREDITOS EMPRESARIALES",
            command=lambda: self.switch_view("empresas"),
            bg=self.COLOR_BLANCO if self.current_view == "empresas" else self.COLOR_ROJO,
            fg=self.COLOR_NEGRO if self.current_view == "empresas" else self.COLOR_BLANCO,
            **button_style
        )
        self.empresas_btn.pack(side='left', padx=2)
        
        # Botón BURO DE CREDITO
        self.buro_btn = tk.Button(
            buttons_frame,
            text="BURO DE CREDITO",
            command=lambda: self.switch_view("buro"),
            bg=self.COLOR_BLANCO if self.current_view == "buro" else self.COLOR_ROJO,
            fg=self.COLOR_NEGRO if self.current_view == "buro" else self.COLOR_BLANCO,
            **button_style
        )
        self.buro_btn.pack(side='left', padx=2)

    def switch_view(self, view):
        """Cambia entre vista de clientes, empresas y buro de credito"""
        if self.current_view != view:
            self.current_view = view
            # Actualizar estilo de botones
            self.clientes_btn.configure(
                bg=self.COLOR_BLANCO if view == "clientes" else self.COLOR_ROJO,
                fg=self.COLOR_NEGRO if view == "clientes" else self.COLOR_BLANCO
            )
            self.empresas_btn.configure(
                bg=self.COLOR_BLANCO if view == "empresas" else self.COLOR_ROJO,
                fg=self.COLOR_NEGRO if view == "empresas" else self.COLOR_BLANCO
            )
            self.buro_btn.configure(
                bg=self.COLOR_BLANCO if view == "buro" else self.COLOR_ROJO,
                fg=self.COLOR_NEGRO if view == "buro" else self.COLOR_BLANCO
            )
            # Recargar contenido
            self.refresh_ui()
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

    def should_show_client(self, client_id):
            """Determina si un cliente debe mostrarse en la vista actual"""
            estados_clientes = get_client_states()
            
            # Si el cliente no está en estados_clientes, asumimos que no es empresa
            is_company = estados_clientes.get(client_id, {}).get('company', False)
            
            if self.current_view == "empresas":
                return is_company
            else:  # vista de clientes
                return not is_company

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
        Categoriza un cliente basado en su historial de ventas, estado y promesa de pago.
        No categoriza clientes que estén en buró de crédito.
        
        Args:
            cliente_id: str - ID del cliente
            
        Returns:
            str: "promesa", "verde", "amarillo", o "rojo" según la categorización
            None: si el cliente está en buró de crédito
        """
        try:
            # Primero verificar si el cliente está en buró de crédito
            conn = get_db_connection()
            if not conn:
                return "rojo"
                
            cursor = conn.cursor()
            query = """
                SELECT credit
                FROM ClientsBuro
                WHERE client_id = ?
            """
            cursor.execute(query, (cliente_id,))
            result = cursor.fetchone()
            
            # Si el cliente está en buró (credit = True/1), retornar None
            if result and result.credit:
                return None
                
            # Si no está en buró o no tiene registro, continuar con la categorización normal
            # Obtener estados de clientes de la base de datos
            estados_clientes = get_client_states()
            
            # Verificar si tiene promiseDate y si es vigente
            fecha_actual = datetime.now().date()
            
            if cliente_id in estados_clientes and estados_clientes[cliente_id].get('promiseDate'):
                promise_date = estados_clientes[cliente_id]['promiseDate']
                
                # Asegurar que promiseDate sea un objeto date
                if isinstance(promise_date, datetime):
                    promise_date = promise_date.date()
                elif isinstance(promise_date, str):
                    try:
                        promise_date = datetime.strptime(promise_date, "%Y-%m-%d").date()
                    except ValueError:
                        promise_date = None
                
                # Solo categorizar como promesa si la fecha es hoy o futura
                if promise_date and promise_date >= fecha_actual:
                    return "promesa"
            
            # Si no tiene promesa vigente, continuar con la categorización normal
            fecha_venta_antigua = self.obtener_fecha_venta_antigua(cliente_id)
            if not fecha_venta_antigua:
                return "rojo"
            
            # Calcular la diferencia de días
            if isinstance(fecha_venta_antigua, datetime):
                diferencia = fecha_actual - fecha_venta_antigua.date()
            else:
                fecha_venta_antigua = datetime.combine(fecha_venta_antigua, datetime.min.time())
                diferencia = fecha_actual - fecha_venta_antigua.date()
            
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
        finally:
            if 'conn' in locals() and conn:
                conn.close()
    
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
      
    def create_buro_section(self, parent):
        """
        Crea una sección para la vista de buró de crédito utilizando todo el espacio disponible.
        """
        # Frame principal - Usar fill='both' y expand=True para ocupar todo el espacio
        buro_frame = tk.Frame(parent)
        buro_frame.pack(fill='both', expand=True)

        # Frame superior para el título y total
        header_frame = tk.Frame(buro_frame)
        header_frame.pack(fill='x', padx=10, pady=20)

        # Título
        title_label = tk.Label(
            header_frame,
            text="CLIENTES EN BURÓ DE CRÉDITO",
            font=("Arial", 16, "bold")
        )
        title_label.pack(side='left')

        # Calcular el total de deuda en buró
        total_buro = sum(datos['saldo'] for datos in get_clients_without_credit().values())

        # Label para el total
        total_label = tk.Label(
            header_frame,
            text=f"Deuda Total en Buró: ${total_buro:,.2f}",
            font=("Arial", 12, "bold"),
            fg=self.COLOR_ROJO
        )
        total_label.pack(side='right')

        # Frame contenedor principal - Usar fill='both' y expand=True
        content_frame = tk.Frame(buro_frame)
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0,5))

        # Frame para la tabla - Usar fill='both' y expand=True
        table_frame = tk.Frame(content_frame)
        table_frame.pack(side='left', fill='both', expand=True, padx=(0,5))

        # Frame para detalles
        details_frame = tk.LabelFrame(
            content_frame,
            text="DETALLES",
            font=("Arial", 12, "bold")
        )
        details_frame.pack(side='right', fill='both', expand=True, padx=(5,0))

        # Configurar el estilo para la tabla
        style = ttk.Style()
        style.configure(
            "Buro.Treeview",
            font=('Arial', 10),
            rowheight=25
        )
        
        # Configurar el tag para el fondo rojo claro
        style.map('Buro.Treeview',
            background=[('selected', '#FFB6C1')])  # Color cuando está seleccionado

        # Crear Treeview con scrollbar
        columns = ('ID', 'Nombre', 'Saldo', 'Última Compra', 'Días en Buró')
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            style="Buro.Treeview"
        )

        # Configurar el tag para el fondo rojo claro
        tree.tag_configure('buro', background='#FFB6C1')  # Mismo color rojo claro que los de más de 60 días

        # Configurar columnas
        tree.column('ID', width=100, anchor='center')
        tree.column('Nombre', width=300, anchor='center')
        tree.column('Saldo', width=120, anchor='center')
        tree.column('Última Compra', width=120, anchor='center')
        tree.column('Días en Buró', width=100, anchor='center')

        for col in columns:
            tree.heading(col, text=col, anchor='center')

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Colocar elementos - Usar fill='both' y expand=True para el tree
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Insertar datos
        clientes_sin_credito = get_clients_without_credit()
        for client_id, datos in clientes_sin_credito.items():
            fecha_ultima_compra = self.obtener_fecha_venta_antigua(client_id)
            dias_en_buro = ""
            if fecha_ultima_compra:
                dias_en_buro = (datetime.now() - fecha_ultima_compra).days

            tree.insert('', 'end', values=(
                client_id,
                datos['nombre'],
                f"${datos['saldo']:,.2f}",
                fecha_ultima_compra.strftime("%Y-%m-%d") if fecha_ultima_compra else "N/A",
                f"{dias_en_buro} días" if dias_en_buro else "N/A"
            ), tags=('buro',))  # Aplicar el tag 'buro' a todas las filas

        # Vincular eventos
        tree.bind('<<TreeviewSelect>>', lambda e: self.mostrar_detalles_cliente_buro(e, details_frame))
        tree.bind('<Double-1>', self.abrir_detalle_cliente)

        # Label de detalles inicial
        tk.Label(details_frame, 
                text="Seleccione un cliente para ver detalles",
                font=("Arial", 10)).pack(expand=True)
    def mostrar_detalles_cliente_buro(self, event, details_frame):
        """
        Muestra los detalles del cliente seleccionado en el panel de detalles del buró.
        """
        # Limpiar el frame de detalles
        for widget in details_frame.winfo_children():
            widget.destroy()

        try:
            # Obtener el cliente seleccionado
            tree = event.widget
            selected_item = tree.selection()[0]
            values = tree.item(selected_item)['values']
            cliente_id = values[0]
            
            # Obtener datos detallados del cliente
            clientes_sin_credito = get_clients_without_credit()
            cliente = clientes_sin_credito.get(str(cliente_id))
            
            if not cliente:
                return
                
            # Crear widgets para mostrar la información
            tk.Label(details_frame,
                    text=f"Cliente: {cliente['nombre']}",
                    font=("Arial", 11, "bold"),
                    bg=self.COLOR_BLANCO).pack(anchor='w', padx=10, pady=5)
                    
            tk.Label(details_frame,
                    text=f"ID: {cliente_id}",
                    font=("Arial", 10),
                    bg=self.COLOR_BLANCO).pack(anchor='w', padx=10, pady=2)
                    
            tk.Label(details_frame,
                    text=f"Saldo: ${cliente['saldo']:,.2f}",
                    font=("Arial", 10, "bold"),
                    fg=self.COLOR_ROJO,
                    bg=self.COLOR_BLANCO).pack(anchor='w', padx=10, pady=2)
                    
            # Mostrar información adicional si está disponible
            fecha_ultima = self.obtener_fecha_venta_antigua(cliente_id)
            if fecha_ultima:
                dias = (datetime.now() - fecha_ultima).days
                tk.Label(details_frame,
                        text=f"Última compra: {fecha_ultima.strftime('%Y-%m-%d')}",
                        font=("Arial", 10),
                        bg=self.COLOR_BLANCO).pack(anchor='w', padx=10, pady=2)
                        
                tk.Label(details_frame,
                        text=f"Días en buró: {dias}",
                        font=("Arial", 10),
                        bg=self.COLOR_BLANCO).pack(anchor='w', padx=10, pady=2)
                        
            # Botón para ver detalles completos
            tk.Button(details_frame,
                    text="Ver Detalles Completos",
                    command=lambda: self.abrir_detalle_cliente(event),
                    font=("Arial", 10),
                    bg=self.COLOR_ROJO,
                    fg=self.COLOR_BLANCO,
                    cursor="hand2").pack(pady=10)
                    
        except Exception as e:
            logging.error(f"Error al mostrar detalles del cliente: {e}")
            tk.Label(details_frame,
                    text="Error al cargar detalles",
                    font=("Arial", 10),
                    fg="red",
                    bg=self.COLOR_BLANCO).pack(expand=True)
    def create_main_content(self):
        """
        Versión modificada de create_main_content que maximiza el espacio
        """
        if self.main_frame:
            self.main_frame.destroy()

        # Contenedor principal sin padding
        self.main_frame = tk.Frame(self.root, bg="blue")
        self.main_frame.pack(fill='both', expand=True)
        
        # Configurar el contenedor como flexbox vertical
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Contenedor interno para la sección de buro
        self.buro_section_frame = tk.Frame(self.main_frame)
        self.buro_section_frame.grid(row=0, column=0, sticky="nsew")

        if self.current_view == "buro":
            sync_clients_to_buro()
            self.create_buro_section(self.buro_section_frame)
            
            # Agregar un espacio vacío al final de la sección de buró
            empty_space = tk.Frame(self.buro_section_frame, bg=self.buro_section_frame.cget("bg"), height=300)
            empty_space.pack(fill='both', expand=True)
            
        else:
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
            categories_container.grid_rowconfigure(3, weight=1)
            
            # Configurar el estilo para centrar el texto en todas las tablas
            style = ttk.Style()
            style.configure("Treeview", anchor="center")  # Centra el texto en todas las celdas
            style.configure("Treeview.Heading", anchor="center")  # Centra los encabezados
            
            # Crear las tres categorías usando grid en lugar de pack
            self.create_category_section(categories_container, "PROMESA DE PAGO", self.COLOR_AZUL, 0)
            self.create_category_section(categories_container, "MENOS DE 30 DIAS", self.COLOR_VERDE, 1)
            self.create_category_section(categories_container, "30 A 60 DIAS", self.COLOR_AMARILLO, 2)
            self.create_category_section(categories_container, "MAS DE 60 DIAS", self.COLOR_ROJO, 3)
            
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
        # Calcular el total para esta categoría
        categoria = "promesa" if "PROMESA" in title else \
                "verde" if "30 DIAS" in title else \
                "amarillo" if "30 A 60" in title else "rojo"
        total_categoria = self.calcular_total_categoria(categoria)
        
        # Frame para la categoría completa
        category_frame = tk.LabelFrame(parent, bg=self.COLOR_BLANCO)
        category_frame.grid(row=row, column=0, sticky='nsew', padx=5, pady=5)
        
        # Frame para el título y total
        title_frame = tk.Frame(category_frame, bg=self.COLOR_BLANCO)
        title_frame.pack(fill='x', padx=5, pady=2)
        
        # Label para el título
        title_label = tk.Label(title_frame,
                            text=title,
                            font=("Arial", 12, "bold"),
                            fg=color,
                            bg=self.COLOR_BLANCO)
        title_label.pack(side='left')
        
        # Label para el total
        total_label = tk.Label(title_frame,
                            text=f"Total: ${total_categoria:,.2f}",
                            font=("Arial", 10),
                            fg=color,
                            bg=self.COLOR_BLANCO)
        total_label.pack(side='right')
        
        # Frame contenedor para el tree y scrollbar
        tree_container = tk.Frame(category_frame, bg=self.COLOR_BLANCO)
        tree_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Crear Treeview con columna oculta para la clave
        tree = ttk.Treeview(tree_container, 
                        columns=('Clave', 'Nombre', 'Monto', 'Fecha', 'Dias'),
                        show='headings',
                        height=5,
                        style="Treeview")
        
        # Configurar columnas
        tree.column('Clave', width=0, stretch=False)
        tree.column('Nombre', width=250, minwidth=250, anchor='center')
        tree.column('Monto', width=100, minwidth=100, anchor='center')
        tree.column('Fecha', width=100, minwidth=100, anchor='center')
        tree.column('Dias', width=100, minwidth=100, anchor='center')
        
        # Configurar headings - centrados
        tree.heading('Nombre', text='Nombre', anchor='center')
        tree.heading('Monto', text='Monto', anchor='center')
        tree.heading('Fecha', text='Fecha de compra', anchor='center')
        tree.heading('Dias', text='Días vencidos', anchor='center')
        
        # Estilo para el Treeview y configuración de tags para colores
        style = ttk.Style()
        style.configure("Treeview",
                    background=self.COLOR_BLANCO,
                    foreground=self.COLOR_NEGRO,
                    fieldbackground=self.COLOR_BLANCO)
        
        # Configurar tags para los diferentes colores de fondo
        tree.tag_configure('promise', background='#87CEEB')  # Azul claro para promesas
        tree.tag_configure('recent', background='#90EE90')   # Verde claro para menos de 30 días
        tree.tag_configure('medium', background='#FFE4B5')   # Amarillo para 30-60 días
        tree.tag_configure('late', background='#FFB6C1')     # Rojo claro para más de 60 días
        
        # Fecha actual
        fecha_actual = datetime.now()
        
        # Obtener estados de clientes para verificar promesas
        estados_clientes = get_client_states()
        
        # Insertar datos según la categoría
        for clave, cliente in self.clientes_data.items():
            if not self.should_show_client(clave):
                continue
                
            categoria_cliente = self.categorizar_cliente(clave)
            if ((color == self.COLOR_AZUL and categoria_cliente == "promesa") or
                (color == self.COLOR_VERDE and categoria_cliente == "verde") or
                (color == self.COLOR_AMARILLO and categoria_cliente == "amarillo") or
                (color == self.COLOR_ROJO and categoria_cliente == "rojo")):
                
                fecha_antigua = self.obtener_fecha_venta_antigua(clave)
                if fecha_antigua:
                    fecha_str = fecha_antigua.strftime("%Y-%m-%d")
                    delta = fecha_actual - fecha_antigua
                    dias_vencidos = delta.days
                else:
                    fecha_str = "N/A"
                    dias_vencidos = "N/A"
                
                # Determinar el tag según la categoría
                tag = None
                if categoria_cliente == "promesa":
                    tag = 'promise'
                elif categoria_cliente == "verde":
                    tag = 'recent'
                elif categoria_cliente == "amarillo":
                    tag = 'medium'
                else:  # rojo
                    tag = 'late'
                
                item = tree.insert('', 'end', values=(
                    clave,
                    cliente['nombre'],
                    f"${cliente['saldo']:,.2f}",
                    fecha_str,
                    dias_vencidos if dias_vencidos != "N/A" else "N/A"
                ))
                
                if tag:
                    tree.item(item, tags=(tag,))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Colocar Treeview y scrollbar
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Vincular eventos
        tree.bind('<<TreeviewSelect>>', self.mostrar_detalles_cliente)
        tree.bind('<Double-1>', self.abrir_detalle_cliente)
        
        # Configurar el grid para expandirse apropiadamente
        parent.grid_rowconfigure(row, weight=1)
        parent.grid_columnconfigure(0, weight=1)  
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
        
        # Frame principal para detalles
        details_container = tk.Frame(self.detalles_frame, bg=self.COLOR_BLANCO)
        details_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Sección de Saldo Total
        saldo_frame = tk.Frame(details_container, bg=self.COLOR_BLANCO)
        saldo_frame.pack(fill='x', padx=5, pady=5)
        
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
        separator = ttk.Separator(details_container, orient='horizontal')
        separator.pack(fill='x', padx=5, pady=10)
        
        # Título de Ventas
        ventas_title = tk.Label(details_container,
                            text="Tickets Pendientes",
                            font=("Arial", 11, "bold"),
                            bg=self.COLOR_BLANCO)
        ventas_title.pack(pady=(0, 10))
        
        # Frame para la lista de ventas
        ventas_container = tk.Frame(details_container, bg=self.COLOR_BLANCO)
        ventas_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Configurar el estilo para centrar el texto
        style = ttk.Style()
        style.configure("Treeview", anchor="center")
        style.configure("Treeview.Heading", anchor="center")
        
        # Crear Treeview para ventas
        columns = ('Ticket', 'Fecha', 'Total')
        ventas_tree = ttk.Treeview(ventas_container, 
                                columns=columns, 
                                show='headings', 
                                height=10,
                                style="Treeview")
        
        # Configurar columnas con anchor='center'
        ventas_tree.column('Ticket', width=80, minwidth=80, anchor='center')
        ventas_tree.column('Fecha', width=100, minwidth=100, anchor='center')
        ventas_tree.column('Total', width=100, minwidth=100, anchor='center')
        
        # Configurar headings - centrados
        for col in columns:
            ventas_tree.heading(col, text=col, anchor='center')
        
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
        
        # Frame contenedor para el árbol y la barra de desplazamiento
        tree_frame = tk.Frame(ventas_container, bg=self.COLOR_BLANCO)
        tree_frame.pack(fill='both', expand=True)
        
        # Scrollbar para las ventas
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=ventas_tree.yview)
        ventas_tree.configure(yscrollcommand=scrollbar.set)
        
        # Colocar Treeview y scrollbar
        ventas_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Ajustar el estilo del Treeview
        style = ttk.Style()
        style.configure("Treeview",
                    background=self.COLOR_BLANCO,
                    foreground=self.COLOR_NEGRO,
                    fieldbackground=self.COLOR_BLANCO)

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
        try:
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
            splash.stop_progress()
            
            # Show login instead of launching main app
            root_splash.after(0, splash.show_login)
            
        except Exception as e:
            splash.update_status(f"Error: {str(e)}")
            time.sleep(3)
            root_splash.destroy()

    # Initialize splash screen
    root_splash = tk.Tk()
    splash = LoadingSplash(root_splash)
    splash.start_progress()

    # Start loading process in separate thread
    threading.Thread(target=proceso_carga, daemon=True).start()
    
    # Wait for login
    root_splash.mainloop()
    
    # After successful login, destroy splash and launch main app
    splash.destroy()
    launch_main_app()

if __name__ == "__main__":
    iniciar_aplicacion()
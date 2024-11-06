import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json
from datetime import datetime
import re
import os

def extract_ticket_number(ticket_text):
    """Extract ticket number from ticket text using regex"""
    if not ticket_text:
        return "N/A"
    match = re.search(r'TICKET:(\d+)', ticket_text)
    return match.group(1) if match else "N/A"

class DetalleClienteWindow:
    def __init__(self, parent, client_data, client_id=None):
        self.top = tk.Toplevel(parent)
        self.top.title("Detalle de Cliente")
        self.top.geometry("1000x800")
        
        # Store cliente_data and client_id as instance variables
        self.client_data = client_data
        self.client_id = client_id
        
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
        self.create_timeline_frame()
        self.create_adeudo_frame()
        
    def create_cliente_frame(self):
        # Frame principal del cliente
        client_frame = tk.LabelFrame(self.top, text="CLIENTE", 
                                    font=("Arial", 16, "bold"),
                                    bg=self.COLOR_BLANCO)
        client_frame.pack(fill='x', padx=20, pady=(20,10))
        
        # Contenedor para la información del cliente
        info_container = tk.Frame(client_frame, bg=self.COLOR_BLANCO)
        info_container.pack(fill='x', padx=20, pady=10)
        
        # Información del cliente
        self.create_info_field(info_container, "Número de Cliente:", self.client_id)
        self.create_info_field(info_container, "Nombre:", self.client_data.get('nombre', 'N/A'))
        self.create_info_field(info_container, "Teléfono:", self.client_data.get('telefono1', 'N/A'))
        self.create_info_field(info_container, "Correo:", self.client_data.get('email', 'N/A'))
        self.create_info_field(info_container, "Direccion:", self.client_data.get('direccion', 'N/A'))

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
        
    def create_timeline_frame(self):
        """Crea el frame principal de la timeline"""
        timeline_frame = tk.LabelFrame(self.top, text="LINEA DE TIEMPO",
                                    font=("Arial", 16, "bold"),
                                    bg=self.COLOR_BLANCO)
        timeline_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Contenedor para la línea vertical y eventos
        events_container = tk.Frame(timeline_frame, bg=self.COLOR_BLANCO)
        events_container.pack(fill='both', expand=True, padx=(30, 10))  # Padding ajustado

        # Línea vertical roja (ahora parte de events_container)
        line = tk.Frame(events_container, width=2, bg=self.COLOR_ROJO)
        line.pack(side='left', fill='y', padx=(0, 20))

        self.timeline_container = events_container
        
        # Mostrar eventos iniciales
        self.mostrar_eventos_timeline(events_container)

        # Frame para los botones
        buttons_frame = tk.Frame(timeline_frame, bg=self.COLOR_BLANCO)
        buttons_frame.pack(pady=5)

        # Botón para nueva nota
        add_note_btn = tk.Button(buttons_frame,
                                text="+ Agregar Nota",
                                font=("Arial", 10),
                                command=self.show_note_dialog)
        add_note_btn.pack(side='left', padx=5)

        # Botón para alternar promesa de pago
        self.promise_btn = tk.Button(buttons_frame,
                                   text="Promesa de Pago",
                                   font=("Arial", 10),
                                   command=self.toggle_promise_page)
        self.promise_btn.pack(side='left', padx=5)

        # Actualizar el estado inicial del botón
        self.update_promise_button_state()
            
    def create_timeline(self, container):
        """
        Crea la línea vertical y los eventos de la línea de tiempo.
        """
        # Línea vertical roja
        line = tk.Frame(container, width=2, bg=self.COLOR_ROJO)
        line.pack(side='left', fill='y', padx=(10, 20))

        # Contenedor de eventos
        events_container = tk.Frame(container, bg=self.COLOR_BLANCO)
        events_container.pack(fill='both', expand=True)

        # Cargar y mostrar los eventos de la línea de tiempo
        self.mostrar_eventos_timeline(events_container)

        return events_container
    
    def cargar_timeline(self):
        """
        Carga la línea del tiempo del cliente desde line.json
        """
        try:
            with open('line.json', 'r', encoding='utf-8') as file:
                timeline_data = json.load(file)
                client_id_str = str(self.client_id)
                return timeline_data.get(client_id_str, {})
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return {}

    def toggle_promise_page(self):
        """
        Alterna el estado de promisePage entre true y false
        """
        try:
            with open('line.json', 'r', encoding='utf-8') as file:
                timeline_data = json.load(file)

            client_id_str = str(self.client_id)
            if client_id_str not in timeline_data:
                timeline_data[client_id_str] = {
                    "day1": False,
                    "day2": False,
                    "day3": False,
                    "dueDay": False,
                    "promisePage": False
                }

            # Alternar el estado
            timeline_data[client_id_str]["promisePage"] = not timeline_data[client_id_str].get("promisePage", False)

            # Guardar los cambios
            with open('line.json', 'w', encoding='utf-8') as file:
                json.dump(timeline_data, file, indent=4)

            # Actualizar la visualización
            self.refresh_timeline()
            self.update_promise_button_state()

        except Exception as e:
            print(f"Error toggling promise page: {e}")
    
    def update_promise_button_state(self):
        """
        Actualiza el estado visual del botón de promesa de pago
        """
        timeline_data = self.cargar_timeline()
        is_promised = timeline_data.get("promisePage", False)
        
        if is_promised:
            self.promise_btn.configure(
                text="Cancelar Promesa",
                bg=self.COLOR_ROJO,
                fg=self.COLOR_BLANCO
            )
        else:
            self.promise_btn.configure(
                text="Promesa de Pago",
                bg="SystemButtonFace",
                fg="black"
            )
    
    def agregar_nota_a_timeline(self, evento, nota):
        """
        Agrega una nueva nota a la línea de tiempo del cliente.
        """
        try:
            with open('line.json', 'r', encoding='utf-8') as file:
                timeline_data = json.load(file)

            client_id_str = str(self.client_id)
            if client_id_str not in timeline_data:
                timeline_data[client_id_str] = {}

            timeline_data[client_id_str][evento] = {
                'type': 'note',
                'text': nota,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            with open('line.json', 'w', encoding='utf-8') as file:
                json.dump(timeline_data, file, indent=4)

            # Actualizar la visualización
            self.refresh_timeline()
        except Exception as e:
            print(f"Error al agregar nota a la línea de tiempo: {e}")
            
    def show_note_dialog(self):
        """
        Muestra un diálogo para agregar una nueva nota al timeline.
        """
        dialog = tk.Toplevel(self.top)
        dialog.title("Agregar Nueva Nota")
        dialog.geometry("300x200")
        dialog.configure(bg=self.COLOR_BLANCO)
        
        # Hacer la ventana modal
        dialog.transient(self.top)
        dialog.grab_set()
        
        # Text area para la nota
        note_text = tk.Text(dialog, height=5, width=30)
        note_text.pack(padx=10, pady=10)
        
        def save_new_note():
            note_content = note_text.get("1.0", "end-1c").strip()
            if note_content:
                self.agregar_nota_a_timeline(f"note_{datetime.now().strftime('%Y%m%d%H%M%S')}", note_content)
                dialog.destroy()
        
        # Botón guardar
        save_btn = tk.Button(dialog,
                            text="Guardar",
                            command=save_new_note)
        save_btn.pack(pady=10)
        
    def mostrar_eventos_timeline(self, container):
        """Muestra los eventos de la timeline en la interfaz"""
        timeline_data = self.cargar_timeline()
        
        if not timeline_data:
            no_data_label = tk.Label(container,
                                    text="No hay datos de seguimiento disponibles",
                                    font=("Arial", 10),
                                    fg=self.COLOR_NEGRO,
                                    bg=self.COLOR_BLANCO)
            no_data_label.pack(pady=20, padx=(30, 0))  # Ajustar padding
            return

        # Ordenar eventos por timestamp de más antiguo a más reciente
        sorted_events = []
        for evento, data in timeline_data.items():
            timestamp = data.get('timestamp', '') if isinstance(data, dict) else ''
            # Para eventos sin timestamp (como day1, day2, etc.), asignar una fecha muy antigua
            if not timestamp:
                if evento == "day1":
                    timestamp = "0001-01-01"
                elif evento == "day2":
                    timestamp = "0001-01-02"
                elif evento == "day3":
                    timestamp = "0001-01-03"
                elif evento == "dueDay":
                    timestamp = "0001-01-04"
            sorted_events.append((evento, data, timestamp))
        
        # Ordenar por timestamp de más antiguo a más reciente
        sorted_events.sort(key=lambda x: x[2])
        
        for evento, data, _ in sorted_events:
            self.mostrar_evento(container, evento, data)

    def mostrar_evento(self, container, evento, data):
        """Muestra un evento individual en el timeline"""
        event_frame = tk.Frame(container, bg=self.COLOR_BLANCO)
        event_frame.pack(fill='x', pady=5, padx=(30, 0))  # Ajustar padding

        # Frame izquierdo para el icono y descripción
        left_frame = tk.Frame(event_frame, bg=self.COLOR_BLANCO)
        left_frame.pack(side='left', fill='x', expand=True)

        # Configurar el icono y descripción
        if isinstance(data, dict) and data.get('type') == 'note':
            icon_text = "📝"
            icon_color = self.COLOR_ROJO
            timestamp = data.get('timestamp', '')
            descripcion = f"{data['text']}\n{timestamp}" if timestamp else data['text']
        else:
            status = data if isinstance(data, bool) else data.get('status', False)
            icon_text = "✔" if status else "⏰"
            icon_color = self.COLOR_ROJO if status else "#666666"
            descripcion = {
                "day1": "Primer día de seguimiento",
                "day2": "Segundo día de seguimiento",
                "day3": "Tercer día de seguimiento",
                "dueDay": "Día de vencimiento",
                "promisePage": "Promesa de pago"
            }.get(evento, evento)

        icon_label = tk.Label(left_frame,
                            text=icon_text,
                            font=("Arial", 14),
                            fg=icon_color,
                            bg=self.COLOR_BLANCO)
        icon_label.pack(side='left', padx=5)

        text_label = tk.Label(left_frame,
                            text=descripcion,
                            font=("Arial", 10),
                            fg=self.COLOR_NEGRO,
                            bg=self.COLOR_BLANCO,
                            justify='left',
                            wraplength=400)
        text_label.pack(side='left', padx=5, fill='x', expand=True)
    
    def add_new_timeline_note(self):
        """
        Muestra un diálogo para agregar una nueva nota al timeline.
        """
        self.dialog = tk.Toplevel(self.top)
        self.dialog.title("Agregar Nueva Nota")
        self.dialog.geometry("300x200")
        self.dialog.configure(bg=self.COLOR_BLANCO)
            
        # Hacer la ventana modal
        self.dialog.transient(self.top)
        self.dialog.grab_set()
            
        # Text area para la nota
        note_text = tk.Text(self.dialog, height=5, width=30)
        note_text.pack(padx=10, pady=10)
            
        def save_new_note():
            note_content = note_text.get("1.0", "end-1c").strip()
            if note_content:
                self.add_note_to_timeline(f"note_{datetime.now().strftime('%Y%m%d%H%M%S')}", note_content)
                self.dialog.destroy()
                # Actualizar la visualización
                self.refresh_timeline()
            
            # Botón guardar
            save_btn = tk.Button(self.dialog,
                                text="Guardar",
                                command=save_new_note)
            save_btn.pack(pady=10)
    
    def add_note_to_timeline(self, evento, note_content):
        """
        Adds a new note to the client's timeline data.
        """
        try:
            with open('line.json', 'r', encoding='utf-8') as file:
                timeline_data = json.load(file)

            client_id_str = str(self.client_id)
            if client_id_str not in timeline_data:
                timeline_data[client_id_str] = {}

            timeline_data[client_id_str][evento] = {
                'type': 'note',
                'text': note_content,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            with open('line.json', 'w', encoding='utf-8') as file:
                json.dump(timeline_data, file, indent=4)

            # Actualizar la vista de la línea de tiempo
            self.refresh_timeline()
        except Exception as e:
            print(f"Error adding note to timeline: {e}")
            
    def refresh_timeline(self):
        """Actualiza solo los eventos de la timeline sin recrear la estructura"""
        # Eliminar solo los eventos existentes, manteniendo la línea vertical
        for widget in self.timeline_container.winfo_children():
            if isinstance(widget, tk.Frame) and widget != self.timeline_container.winfo_children()[0]:  # Preservar la línea vertical
                widget.destroy()
        
        # Mostrar eventos actualizados
        self.mostrar_eventos_timeline(self.timeline_container)

    def create_adeudo_frame(self):
        adeudo_frame = tk.LabelFrame(self.top, text="ADEUDO",
                                font=("Arial", 16, "bold"),
                                bg=self.COLOR_BLANCO)
        adeudo_frame.pack(fill='x', padx=20, pady=10)
        
        # Contenedor para los tickets y montos
        amounts_container = tk.Frame(adeudo_frame, bg=self.COLOR_BLANCO)
        amounts_container.pack(fill='x', padx=20, pady=20)
        
        # Mostrar cada ticket pendiente
        total_adeudo = 0
        if 'ventas' in self.client_data:
            ventas_pendientes = [venta for venta in self.client_data['ventas'] 
                               if venta['estado'] == "X COBRAR"]
            
            for venta in ventas_pendientes:
                # Frame para cada ticket
                ticket_frame = tk.Frame(amounts_container, bg=self.COLOR_BLANCO)
                ticket_frame.pack(fill='x', pady=2)
                
                # Extraer número de ticket del texto del ticket
                ticket_num = extract_ticket_number(venta.get('ticket', ''))
                
                # Etiqueta del ticket
                ticket_label = tk.Label(ticket_frame,
                                    text=f"Ticket #{ticket_num} ({venta['fecha']})",
                                    font=("Arial", 10),
                                    bg=self.COLOR_BLANCO)
                ticket_label.pack(side='left')
                
                # Monto del ticket
                monto = venta['total']
                total_adeudo += monto
                
                # Contenedor derecho para flecha y monto
                right_container = tk.Frame(ticket_frame, bg=self.COLOR_BLANCO)
                right_container.pack(side='right')
                
                # Flecha
                arrow_label = tk.Label(right_container,
                                    text="↓",
                                    font=("Arial", 10),
                                    bg=self.COLOR_BLANCO)
                arrow_label.pack(side='right', padx=(0,5))
                
                # Monto
                amount_label = tk.Label(right_container,
                                    text=f"${monto:,.2f}",
                                    font=("Arial", 10),
                                    bg=self.COLOR_BLANCO)
                amount_label.pack(side='right')
        
        # Separador antes del total
        separator = tk.Frame(amounts_container, height=1, bg=self.COLOR_GRIS)
        separator.pack(fill='x', pady=10)
        
        # Total (saldo pendiente)
        total_frame = tk.Frame(amounts_container, bg=self.COLOR_BLANCO)
        total_frame.pack(fill='x', pady=5)
        
        total_label = tk.Label(total_frame,
                            text="Total",
                            font=("Arial", 10, "bold"),
                            bg=self.COLOR_BLANCO)
        total_label.pack(side='left')
        
        total_amount = tk.Label(total_frame,
                            text=f"${total_adeudo:,.2f}",
                            font=("Arial", 10, "bold"),
                            fg=self.COLOR_ROJO,
                            bg=self.COLOR_BLANCO)
        total_amount.pack(side='right')       
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
        
        # Cargar datos
        self.clientes_data = self.cargar_datos()
        self.line_data = self.cargar_line_data()
        
        # Configurar la ventana principal
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = 1200
        window_height = 800
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg=self.COLOR_BLANCO)
        
        # Variable para almacenar la referencia al main_frame
        self.main_frame = None
        
        self.create_header()
        self.create_main_content()
        
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
        
    def recargar_datos(self):
        """Función para recargar los datos de los archivos JSON y actualizar la interfaz"""
        # Recargar los datos
        self.clientes_data = self.cargar_datos()
        self.line_data = self.cargar_line_data()
        
        # Destruir el contenido actual
        if self.main_frame:
            self.main_frame.destroy()
            
        # Recrear el contenido
        self.create_main_content()
    
    def cargar_datos(self):
        try:
            with open('clientes_ventas_combined.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print("Error: No se encontró el archivo clientes_ventas_combined.json")
            return {}
        except json.JSONDecodeError:
            print("Error: El archivo JSON no tiene un formato válido")
            return {}
        
    def cargar_line_data(self):
        try:
            with open('line.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print("Error: No se encontró el archivo line.json")
            return {}
        except json.JSONDecodeError:
            print("Error: El archivo line.json no tiene un formato válido")
            return {}
    
    def obtener_fecha_venta_antigua(self, cliente):
        if 'ventas' not in cliente or not cliente['ventas']:
            return datetime.now()
        
        # Filtrar ventas pendientes (estado "X COBRAR")
        ventas_pendientes = [venta for venta in cliente['ventas'] 
                            if venta['estado'] == "X COBRAR"]
        
        if not ventas_pendientes:
            return datetime.now()
        
        # Obtener la fecha más antigua de las ventas pendientes
        fechas = [datetime.strptime(venta['fecha'], "%Y-%m-%d") 
                for venta in ventas_pendientes]
        return min(fechas)

    def categorizar_cliente(self, cliente_id, cliente):
        try:
            fecha_venta_antigua = self.obtener_fecha_venta_antigua(cliente)
            fecha_actual = datetime.now()
            diferencia = fecha_actual - fecha_venta_antigua
            
            # Verde: Si tiene promisePage true en line.json
            if cliente_id in self.line_data and self.line_data[cliente_id]['promisePage']:
                return "verde"
            # Amarillo: menos de 30 días
            elif diferencia.days < 30:
                return "amarillo"
            # Rojo: más de 30 días
            else:
                return "rojo"
        except Exception as e:
            print(f"Error al categorizar cliente: {e}")
            return "rojo"  # Por defecto si hay error

        
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
        # Frame para la categoría
        category_frame = tk.LabelFrame(parent, text=title,
                                    font=("Arial", 12, "bold"),
                                    bg=self.COLOR_BLANCO,
                                    fg=color)
        category_frame.grid(row=row, column=0, sticky='nsew', padx=5, pady=5)
        
        # Configurar el category_frame para expandirse
        category_frame.grid_rowconfigure(0, weight=1)
        category_frame.grid_columnconfigure(0, weight=1)
        
        # Crear Treeview
        columns = ('Clave', 'Nombre', 'Monto', 'Fecha')
        tree = ttk.Treeview(category_frame, columns=columns, show='headings')
        
        # Configurar columnas
        tree.column('Clave', width=100, minwidth=100)
        tree.column('Nombre', width=250, minwidth=250)
        tree.column('Monto', width=100, minwidth=100)
        tree.column('Fecha', width=100, minwidth=100)
        
        for col in columns:
            tree.heading(col, text=col)
        
        # Estilo para el Treeview
        style = ttk.Style()
        style.configure("Treeview",
                    background=self.COLOR_BLANCO,
                    foreground=self.COLOR_NEGRO,
                    fieldbackground=self.COLOR_BLANCO)
        
        # Insertar datos según la categoría
        for clave, cliente in self.clientes_data.items():
            categoria = self.categorizar_cliente(clave, cliente)
            if ((color == self.COLOR_VERDE and categoria == "verde") or
                (color == self.COLOR_AMARILLO and categoria == "amarillo") or
                (color == self.COLOR_ROJO and categoria == "rojo")):
                
                fecha_antigua = self.obtener_fecha_venta_antigua(cliente)
                
                tree.insert('', 'end', values=(
                    clave,
                    cliente['nombre'],
                    f"${cliente['saldo']:,.2f}",
                    fecha_antigua.strftime("%Y-%m-%d")
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
        tree = event.widget
        selected_item = tree.selection()[0]
        client_clave = tree.item(selected_item)['values'][0]  # Obtenemos el ID
        client = self.clientes_data[client_clave]
        print(f"ID del cliente seleccionado: {client_clave}")
        # Pass both client data and ID to DetalleClienteWindow
        DetalleClienteWindow(self.root, client, client_clave)

if __name__ == "__main__":
    root = tk.Tk()
    app = CobranzaApp(root)
    root.mainloop()
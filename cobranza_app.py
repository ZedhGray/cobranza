import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json
from datetime import datetime

class DetalleClienteWindow:
    def __init__(self, parent, cliente_data):
        self.top = tk.Toplevel(parent)
        self.top.title("Detalle de Cliente")
        self.top.geometry("1000x800")
        
        # Store cliente_data as instance variable
        self.cliente_data = cliente_data
        
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
        self.create_cliente_frame(cliente_data)
        self.create_timeline_frame()
        self.create_adeudo_frame(cliente_data)
        
        
    def create_cliente_frame(self, cliente):
        # Frame principal del cliente
        cliente_frame = tk.LabelFrame(self.top, text="CLIENTE", 
                                    font=("Arial", 16, "bold"),
                                    bg=self.COLOR_BLANCO)
        cliente_frame.pack(fill='x', padx=20, pady=(20,10))
        
        # Contenedor para la información del cliente
        info_container = tk.Frame(cliente_frame, bg=self.COLOR_BLANCO)
        info_container.pack(fill='x', padx=20, pady=10)
        
        # Información del cliente
        self.create_info_field(info_container, "Número de Cliente:", cliente.get('clave', 'N/A'))
        self.create_info_field(info_container, "Nombre:", cliente.get('nombre', 'N/A'))
        self.create_info_field(info_container, "Teléfono:", cliente.get('telefono1', 'N/A'))
        self.create_info_field(info_container, "Correo:", cliente.get('email', 'N/A'))
        
        # Dirección completa
        self.create_info_field(info_container, "Direccion:", cliente.get('direccion', 'N/A'))

        # Estado (punto rojo y "Activo")
        estado_frame = tk.Frame(cliente_frame, bg=self.COLOR_BLANCO)
        estado_frame.place(relx=1.0, x=-20, y=10, anchor='ne')
        
        estado_label = tk.Label(estado_frame,
                            text="●",
                            font=("Arial", 12),
                            fg=self.COLOR_ROJO,
                            bg=self.COLOR_BLANCO)
        estado_label.pack(side='left')
        
        estado_texto = tk.Label(estado_frame,
                            text=cliente.get('estado', 'ACTIVO'),
                            font=("Arial", 12),
                            fg=self.COLOR_ROJO,
                            bg=self.COLOR_BLANCO)
        estado_texto.pack(side='left', padx=5)
        
    def create_info_field(self, parent, label, value, use_grid=False, row=None, col=None, columnspan=1):
        """
        Crea un campo de información con etiqueta y valor.
        
        Args:
            parent: Widget padre donde se creará el campo
            label: Texto de la etiqueta
            value: Valor a mostrar
            use_grid: Si es True usa grid, si es False usa pack
            row: Fila para grid (solo si use_grid es True)
            col: Columna para grid (solo si use_grid es True)
            columnspan: Número de columnas a ocupar en grid (solo si use_grid es True)
        """
        frame = tk.Frame(parent, bg=self.COLOR_BLANCO)
        
        if use_grid:
            frame.grid(row=row, column=col, columnspan=columnspan, sticky='w', pady=2)
        else:
            frame.pack(fill='x', pady=5)
        
        # Etiqueta
        label_widget = tk.Label(frame,
                            text=label,
                            font=("Arial", 10, "bold"),
                            bg=self.COLOR_BLANCO)
        label_widget.pack(side='left', padx=(0,5))
        
        # Valor
        value_widget = tk.Label(frame,
                            text=value,
                            font=("Arial", 10),
                            bg=self.COLOR_BLANCO)
        value_widget.pack(side='left', padx=(0,10))
        
        return frame
        
    # Actualización de la clase DetalleClienteWindow
    def create_timeline_frame(self):
        timeline_frame = tk.LabelFrame(self.top, text="LINEA DE TIEMPO",
                                    font=("Arial", 16, "bold"),
                                    bg=self.COLOR_BLANCO)
        timeline_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Contenedor para la línea vertical y eventos
        self.timeline_container = tk.Frame(timeline_frame, bg=self.COLOR_BLANCO)
        self.timeline_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Línea vertical roja
        line = tk.Frame(self.timeline_container, width=2, bg=self.COLOR_ROJO)
        line.pack(side='left', fill='y', padx=(10, 20))
        
        # Contenedor de eventos
        events_container = tk.Frame(self.timeline_container, bg=self.COLOR_BLANCO)
        events_container.pack(fill='both', expand=True)
        
        # Obtener el ID del cliente
        cliente_id = str(self.cliente_data.get('nc', ''))
        
        # Cargar o crear la línea del tiempo del cliente
        timeline_data = self.cargar_o_crear_timeline(cliente_id)
        
        # Mostrar eventos
        self.mostrar_eventos_timeline(events_container, timeline_data['eventos'])

    def cargar_o_crear_timeline(self, cliente_id):
        """
        Carga la línea del tiempo existente del cliente o crea una nueva si no existe.
        """
        # Convertir cliente_id a string para usarlo como clave
        cliente_id = str(cliente_id)
        
        try:
            # Intentar cargar el archivo de líneas de tiempo
            with open('timeline_data.json', 'r', encoding='utf-8') as file:
                timeline_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            # Si el archivo no existe o está corrupto, inicializar como diccionario vacío
            timeline_data = {}
        
        # Si no existe línea del tiempo para este cliente, crearla
        if cliente_id not in timeline_data:
            # Crear eventos iniciales basados en las ventas
            eventos_iniciales = self.crear_eventos_desde_ventas(self.cliente_data)
            
            # Crear nueva entrada para el cliente
            timeline_data[cliente_id] = {
                "eventos": eventos_iniciales,
                "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Guardar el archivo actualizado
            self.guardar_timeline_data(timeline_data)
            return timeline_data[cliente_id]
        else:
            # Si ya existe, retornar la timeline existente
            return timeline_data[cliente_id]
        
    def cargar_timeline_data(self):
        """
        Carga los datos de la línea del tiempo desde el archivo JSON.
        Si el archivo no existe o está corrupto, retorna un diccionario vacío.
        
        Returns:
            dict: Datos de la línea del tiempo de todos los clientes
        """
        try:
            with open('timeline_data.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print("Error: El archivo de línea del tiempo está corrupto")
            return {}
        except Exception as e:
            print(f"Error al cargar timeline: {e}")
            return {}
    
    def guardar_timeline_data(self, timeline_data):
        """
        Guarda los datos de la línea del tiempo en el archivo JSON.
        Asegura que los datos existentes no se pierdan.
        """
        try:
            # Intentar cargar datos existentes
            try:
                with open('timeline_data.json', 'r', encoding='utf-8') as file:
                    existing_data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {}
            
            # Actualizar solo los datos nuevos/modificados
            if isinstance(timeline_data, dict):
                existing_data.update(timeline_data)
            
            # Guardar todos los datos
            with open('timeline_data.json', 'w', encoding='utf-8') as file:
                json.dump(existing_data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar timeline: {e}")
            
    def agregar_evento_timeline(self, cliente_id, evento):
        """
        Agrega un nuevo evento a la línea del tiempo de un cliente específico.
        """
        # Convertir cliente_id a string
        cliente_id = str(cliente_id)
        
        # Cargar todas las timelines existentes
        try:
            with open('timeline_data.json', 'r', encoding='utf-8') as file:
                all_timelines = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            all_timelines = {}
        
        # Obtener o crear la timeline del cliente
        if cliente_id not in all_timelines:
            timeline_data = {
                "eventos": [],
                "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            timeline_data = all_timelines[cliente_id]
        
        # Agregar el nuevo evento
        nuevo_evento = {
            **evento,
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M:%S")
        }
        
        timeline_data['eventos'].insert(0, nuevo_evento)
        timeline_data['ultima_actualizacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Actualizar en el diccionario principal
        all_timelines[cliente_id] = timeline_data
        
        # Guardar todos los cambios
        self.guardar_timeline_data(all_timelines)
        
        # Actualizar la visualización si el contenedor existe
        if hasattr(self, 'timeline_container') and self.timeline_container:
            for widget in self.timeline_container.winfo_children():
                widget.destroy()
            self.mostrar_eventos_timeline(self.timeline_container, timeline_data['eventos'])

    def crear_eventos_desde_ventas(self, cliente):
        """
        Crea eventos iniciales basados en las ventas del cliente.
        """
        eventos = []
        if 'ventas' in cliente:
            for venta in cliente['ventas']:
                fecha_vencimiento = datetime.strptime(venta['fechaProg'], "%Y-%m-%d")
                
                # Evento de nuevo ticket
                eventos.append({
                    "tipo": "TICKET_NUEVO",
                    "fecha": venta['fecha'],
                    "hora": venta['hora'],
                    "folio": venta['folio'],
                    "monto": venta['total'],
                    "descripcion": f"Ticket #{venta['folio']} generado",
                    "detalles": {
                        "estado": venta['estado'],
                        "fechaProgramada": venta['fechaProg'],
                        "condiciones": venta['condiciones']
                    }
                })
                
                # Si hay anticipo, crear evento de pago
                if venta.get('anticipo', 0) > 0:
                    eventos.append({
                        "tipo": "PAGO",
                        "fecha": venta['fecha'],
                        "hora": venta['hora'],
                        "monto": venta['anticipo'],
                        "descripcion": f"Anticipo recibido para ticket #{venta['folio']}",
                        "detalles": {
                            "metodoPago": "ANTICIPO",
                            "folioTicket": venta['folio'],
                            "restante": venta['total'] - venta['anticipo']
                        }
                    })
        
        # Ordenar eventos por fecha y hora
        eventos.sort(key=lambda x: (x['fecha'], x['hora']), reverse=True)
        return eventos


    def mostrar_eventos_timeline(self, container, eventos):
        for evento in eventos:
            # Frame para el evento
            event_frame = tk.Frame(container, bg=self.COLOR_BLANCO)
            event_frame.pack(fill='x', pady=5)
            
            # Icono según el tipo de evento
            icon_text = self.get_event_icon(evento['tipo'])
            icon_color = self.get_event_color(evento['tipo'])
            
            icon_label = tk.Label(event_frame,
                                text=icon_text,
                                font=("Arial", 14),
                                fg=icon_color,
                                bg=self.COLOR_BLANCO)
            icon_label.pack(side='left', padx=5)
            
            # Contenedor para texto del evento
            text_container = tk.Frame(event_frame, bg=self.COLOR_BLANCO)
            text_container.pack(side='left', fill='x', expand=True)
            
            # Fecha y hora
            fecha_hora = tk.Label(text_container,
                                text=f"{evento['fecha']} {evento.get('hora', '')}",
                                font=("Arial", 8),
                                fg=self.COLOR_NEGRO,
                                bg=self.COLOR_BLANCO)
            fecha_hora.pack(anchor='w')
            
            # Descripción
            descripcion = tk.Label(text_container,
                                text=evento['descripcion'],
                                font=("Arial", 10, "bold"),
                                fg=self.COLOR_NEGRO,
                                bg=self.COLOR_BLANCO)
            descripcion.pack(anchor='w')
            
            # Detalles adicionales
            if 'monto' in evento:
                monto = tk.Label(text_container,
                            text=f"${evento['monto']:,.2f}",
                            font=("Arial", 10),
                            fg=self.COLOR_ROJO,
                            bg=self.COLOR_BLANCO)
                monto.pack(anchor='w')
            
            # Mostrar detalles específicos según el tipo de evento
            self.mostrar_detalles_evento(text_container, evento)

    def get_event_icon(self, tipo):
        icons = {
            "TICKET_NUEVO": "🎫",
            "PROMESA_PAGO": "🤝",
            "CONTACTO": "📞",
            "PAGO": "💰",
            "RETRASO": "⚠️",
            "VISITA": "🏪",
            "NOTIFICACION": "📱"  # Nuevo icono para notificaciones
        }
        return icons.get(tipo, "●")

    def get_event_color(self, tipo):
        colors = {
            "TICKET_NUEVO": self.COLOR_NEGRO,
            "PROMESA_PAGO": "#4CAF50",  # Verde
            "CONTACTO": "#2196F3",      # Azul
            "PAGO": "#4CAF50",          # Verde
            "RETRASO": self.COLOR_ROJO,
            "VISITA": "#9C27B0",        # Púrpura
            "NOTIFICACION": "#FF9800"    # Naranja para notificaciones
        }
        return colors.get(tipo, self.COLOR_NEGRO)

    def mostrar_detalles_evento(self, container, evento):
        detalles = evento.get('detalles', {})
        
        for key, value in detalles.items():
            if value and str(value) != "1900-01-01":  # Excluir fechas vacías
                detalle_text = f"{key}: {value}"
                detalle_label = tk.Label(container,
                                    text=detalle_text,
                                    font=("Arial", 9),
                                    fg="#666666",
                                    bg=self.COLOR_BLANCO)
                detalle_label.pack(anchor='w')

    def guardar_eventos_timeline(self, cliente_id, eventos):
        timeline_data = self.cargar_timeline_data()
        timeline_data[cliente_id] = {"eventos": eventos}
        
        try:
            with open('timeline_data.json', 'w', encoding='utf-8') as file:
                json.dump(timeline_data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar timeline: {e}")
            
    def create_adeudo_frame(self, cliente):
        adeudo_frame = tk.LabelFrame(self.top, text="ADEUDO",
                                font=("Arial", 16, "bold"),
                                bg=self.COLOR_BLANCO)
        adeudo_frame.pack(fill='x', padx=20, pady=10)
        
        # Contenedor para los tickets y montos
        amounts_container = tk.Frame(adeudo_frame, bg=self.COLOR_BLANCO)
        amounts_container.pack(fill='x', padx=20, pady=20)
        
        # Mostrar cada ticket pendiente
        total_adeudo = 0
        if 'ventas' in cliente:
            ventas_pendientes = [venta for venta in cliente['ventas'] 
                            if venta['estado'] == "X COBRAR"]
            
            for venta in ventas_pendientes:
                # Frame para cada ticket
                ticket_frame = tk.Frame(amounts_container, bg=self.COLOR_BLANCO)
                ticket_frame.pack(fill='x', pady=2)
                
                # Etiqueta del ticket
                ticket_label = tk.Label(ticket_frame,
                                    text=f"Ticket #{venta['folio']} ({venta['fecha']})",
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
            
    def create_amount_row(self, parent, label, amount, is_total=False):
        frame = tk.Frame(parent, bg=self.COLOR_BLANCO)
        frame.pack(fill='x', pady=5)
        
        # Etiqueta
        label = tk.Label(frame,
                        text=label,
                        font=("Arial", 10),
                        bg=self.COLOR_BLANCO)
        label.pack(side='left')
        
        # Contenedor derecho para flecha y monto
        right_container = tk.Frame(frame, bg=self.COLOR_BLANCO)
        right_container.pack(side='right')
        
        if not is_total:
            # Flecha
            arrow = "↓" if amount > 0 else "↑"
            arrow_label = tk.Label(right_container,
                                 text=arrow,
                                 font=("Arial", 10),
                                 bg=self.COLOR_BLANCO)
            arrow_label.pack(side='right', padx=(0,5))
        
        # Monto
        amount_label = tk.Label(right_container,
                              text=f"${abs(amount):,.2f}",
                              font=("Arial", 10, "bold"),
                              fg=self.COLOR_ROJO if is_total else self.COLOR_NEGRO,
                              bg=self.COLOR_BLANCO)
        amount_label.pack(side='right')
       
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
        
        # Configurar la ventana principal
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = 1200
        window_height = 800
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg=self.COLOR_BLANCO)
        
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
        
        back_button = tk.Button(header_frame, 
                              text="← Atrás",
                              font=("Arial", 10),
                              bg=self.COLOR_ROJO,
                              fg=self.COLOR_BLANCO,
                              bd=0,
                              cursor="hand2")
        back_button.pack(side='right', padx=20)
        
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

    def categorizar_cliente(self, cliente):
        try:
            fecha_venta_antigua = self.obtener_fecha_venta_antigua(cliente)
            fecha_actual = datetime.now()
            diferencia = fecha_actual - fecha_venta_antigua
            
            # Verde: Solo ventas del día actual
            if fecha_venta_antigua.date() == fecha_actual.date():
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
        main_frame = tk.Frame(self.root, bg=self.COLOR_BLANCO)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Lista de clientes (izquierda - 2/3 del ancho)
        clientes_frame = tk.LabelFrame(main_frame, text="CLIENTES", 
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
        self.detalles_frame = tk.LabelFrame(main_frame,
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
            categoria = self.categorizar_cliente(cliente)
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
        columns = ('Folio', 'Fecha', 'Total')
        ventas_tree = ttk.Treeview(ventas_container, columns=columns, show='headings', height=10)
        
        # Configurar columnas
        ventas_tree.column('Folio', width=80, minwidth=80)
        ventas_tree.column('Fecha', width=100, minwidth=100)
        ventas_tree.column('Total', width=100, minwidth=100)
        
        for col in columns:
            ventas_tree.heading(col, text=col)
        
        # Obtener y ordenar ventas
        if 'ventas' in cliente:
            ventas = sorted(
                [venta for venta in cliente['ventas'] if venta['estado'] == "X COBRAR"],
                key=lambda x: datetime.strptime(x['fecha'], "%Y-%m-%d"),
                reverse=True  # Ordenar de más reciente a más antigua
            )
            
            # Insertar ventas ordenadas
            for venta in ventas:
                ventas_tree.insert('', 'end', values=(
                    venta['folio'],
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
        # Obtener el Treeview que generó el evento
        tree = event.widget
        selected_item = tree.selection()[0]
        cliente_clave = tree.item(selected_item)['values'][0]
        cliente = self.clientes_data[cliente_clave]
        DetalleClienteWindow(self.root, cliente)

if __name__ == "__main__":
    root = tk.Tk()
    app = CobranzaApp(root)
    root.mainloop()
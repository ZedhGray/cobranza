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
        
        # Colores
        self.COLOR_ROJO = "#E31837"
        self.COLOR_NEGRO = "#333333"
        self.COLOR_BLANCO = "#FFFFFF"
        self.COLOR_GRIS = "#F5F5F5"
        self.COLOR_GRIS_CLARO = "#EFEFEF"
        
        # Configurar la ventana
        self.top.configure(bg=self.COLOR_GRIS_CLARO)
        
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
        
        # Estado (punto rojo y "Activo")
        estado_frame = tk.Frame(cliente_frame, bg=self.COLOR_BLANCO)
        estado_frame.pack(fill='x', padx=20, pady=10)
        
        estado_label = tk.Label(estado_frame,
                              text="●",
                              font=("Arial", 12),
                              fg=self.COLOR_ROJO,
                              bg=self.COLOR_BLANCO)
        estado_label.pack(side='left')
        
        estado_texto = tk.Label(estado_frame,
                              text=cliente['estado'],
                              font=("Arial", 12),
                              fg=self.COLOR_ROJO,
                              bg=self.COLOR_BLANCO)
        estado_texto.pack(side='left', padx=5)
        
        # Datos del cliente en grid
        info_frame = tk.Frame(cliente_frame, bg=self.COLOR_BLANCO)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        # Primera columna
        col1_frame = tk.Frame(info_frame, bg=self.COLOR_BLANCO)
        col1_frame.pack(side='left', fill='x', expand=True)
        
        self.create_info_field(col1_frame, "Dirección:", cliente.get('direccion', 'N/A'))
        self.create_info_field(col1_frame, "Teléfono 1:", cliente.get('telefono1', 'N/A'))
        
        # Segunda columna
        col2_frame = tk.Frame(info_frame, bg=self.COLOR_BLANCO)
        col2_frame.pack(side='left', fill='x', expand=True)
        
        self.create_info_field(col2_frame, "Correo:", cliente.get('email', 'N/A'))
        self.create_info_field(col2_frame, "Teléfono 2:", cliente.get('telefono2', 'N/A'))
        
        # Observaciones
        obs_label = tk.Label(cliente_frame,
                           text="Observaciones:",
                           font=("Arial", 10),
                           bg=self.COLOR_BLANCO)
        obs_label.pack(fill='x', padx=20, pady=(10,0), anchor='w')
        
        obs_text = tk.Label(cliente_frame,
                          text=cliente.get('obs', 'Sin observaciones'),
                          font=("Arial", 10),
                          bg=self.COLOR_BLANCO,
                          wraplength=900)
        obs_text.pack(fill='x', padx=20, pady=(0,10), anchor='w')

    def create_timeline_frame(self):
        timeline_frame = tk.LabelFrame(self.top, text="LINEA DE TIEMPO",
                                     font=("Arial", 16, "bold"),
                                     bg=self.COLOR_BLANCO)
        timeline_frame.pack(fill='x', padx=20, pady=10)
        
        # Título "Detalles"
        detalles_label = tk.Label(timeline_frame,
                                text="Detalles",
                                font=("Arial", 12, "bold"),
                                bg=self.COLOR_BLANCO)
        detalles_label.pack(anchor='w', padx=20, pady=(10,5))
        
        # Datos de ejemplo para la línea de tiempo
        timeline_data = [
            {"tipo": "Abonos", "eventos": [
                "17 sep. 09:55 - Transferencia de $150.00",
                "21 sep. 12:50 - Abono efectivo de $50.00"
            ]},
            {"tipo": "Retraso de pago", "eventos": [
                "02 nov. 15:25 - Falta de pago"
            ]}
        ]
        
        for item in timeline_data:
            # Tipo de evento (con punto rojo si es retraso)
            tipo_frame = tk.Frame(timeline_frame, bg=self.COLOR_BLANCO)
            tipo_frame.pack(fill='x', padx=20, pady=5)
            
            if "Retraso" in item["tipo"]:
                color = self.COLOR_ROJO
            else:
                color = self.COLOR_NEGRO
                
            tipo_label = tk.Label(tipo_frame,
                                text=item["tipo"],
                                font=("Arial", 10, "bold"),
                                fg=color,
                                bg=self.COLOR_BLANCO)
            tipo_label.pack(side='left')
            
            # Eventos
            for evento in item["eventos"]:
                evento_label = tk.Label(timeline_frame,
                                      text=evento,
                                      font=("Arial", 10),
                                      bg=self.COLOR_BLANCO)
                evento_label.pack(anchor='w', padx=40)

    def create_adeudo_frame(self, cliente):
        adeudo_frame = tk.LabelFrame(self.top, text="ADEUDO",
                                   font=("Arial", 16, "bold"),
                                   bg=self.COLOR_BLANCO)
        adeudo_frame.pack(side='right', fill='y', padx=20, pady=10)
        
        # Precio de productos
        self.create_amount_field(adeudo_frame, "Precio de productos", 
                               cliente.get('montoCredito', 0), True)
        
        # Abono (como número negativo)
        self.create_amount_field(adeudo_frame, "Abono", 
                               -cliente.get('saldo', 0), True)
        
        # Total
        total = cliente.get('montoCredito', 0) - cliente.get('saldo', 0)
        self.create_amount_field(adeudo_frame, "Total", total, False)
        
    def create_info_field(self, parent, label, value):
        frame = tk.Frame(parent, bg=self.COLOR_BLANCO)
        frame.pack(fill='x', pady=5)
        
        label = tk.Label(frame,
                        text=label,
                        font=("Arial", 10),
                        bg=self.COLOR_BLANCO)
        label.pack(side='left')
        
        value = tk.Label(frame,
                        text=value,
                        font=("Arial", 10),
                        bg=self.COLOR_BLANCO)
        value.pack(side='left', padx=10)
        
    def create_amount_field(self, parent, label, amount, show_arrow=True):
        frame = tk.Frame(parent, bg=self.COLOR_BLANCO)
        frame.pack(fill='x', padx=20, pady=10)
        
        label = tk.Label(frame,
                        text=label,
                        font=("Arial", 10),
                        bg=self.COLOR_BLANCO)
        label.pack(side='left')
        
        if show_arrow:
            arrow = "↓" if amount > 0 else "↑"
            arrow_label = tk.Label(frame,
                                 text=arrow,
                                 font=("Arial", 10),
                                 bg=self.COLOR_BLANCO)
            arrow_label.pack(side='right', padx=(0,5))
            
        amount_label = tk.Label(frame,
                              text=f"${abs(amount):,.2f}",
                              font=("Arial", 10, "bold"),
                              fg=self.COLOR_ROJO if "Total" in label else self.COLOR_NEGRO,
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
        
        # Cargar datos
        self.clientes_data = self.cargar_datos()
        
        # Configurar la ventana principal
        self.root.geometry("1200x800")
        self.root.configure(bg=self.COLOR_BLANCO)
        
        self.create_header()
        self.create_main_content()
        
    def cargar_datos(self):
        try:
            with open('clientes_data.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print("Error: No se encontró el archivo clientes_data.json")
            return {}
        except json.JSONDecodeError:
            print("Error: El archivo JSON no tiene un formato válido")
            return {}
        
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
        
    def create_main_content(self):
        main_frame = tk.Frame(self.root, bg=self.COLOR_BLANCO)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Lista de clientes (izquierda - 2/3 del ancho)
        clientes_frame = tk.LabelFrame(main_frame, text="CLIENTES", 
                                     font=("Arial", 16, "bold"),
                                     bg=self.COLOR_BLANCO)
        clientes_frame.pack(side='left', fill='both', expand=True, padx=(0,10))
        clientes_frame.pack_propagate(False)  # Evita que el frame se encoja
        # Establecer el ancho como 2/3 del total
        window_width = self.root.winfo_screenwidth()
        clientes_frame.configure(width=(window_width * 2) // 3)
        
        # Crear Treeview para la lista de clientes
        columns = ('Clave', 'Nombre', 'Monto', 'Fecha')
        self.tree = ttk.Treeview(clientes_frame, columns=columns, show='headings')
        
        # Configurar las columnas
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.tree.column('Nombre', width=250)
        
        # Estilo para el Treeview
        style = ttk.Style()
        style.configure("Treeview", 
                       background=self.COLOR_BLANCO,
                       foreground=self.COLOR_NEGRO,
                       fieldbackground=self.COLOR_BLANCO)
        
        # Insertar datos
        for clave, cliente in self.clientes_data.items():
            self.tree.insert('', 'end', values=(
                clave,
                cliente['nombre'],
                f"${cliente['saldo']:,.2f}",
                cliente['fecha']
            ))
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(clientes_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar Treeview y scrollbar
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Vincular evento de clic
        self.tree.bind('<<TreeviewSelect>>', self.mostrar_detalles_cliente)
        
        # Frame para detalles del cliente (derecha - 1/3 del ancho)
        self.detalles_frame = tk.LabelFrame(main_frame,
                                          text="ADEUDO",
                                          font=("Arial", 16, "bold"),
                                          bg=self.COLOR_BLANCO)
        self.detalles_frame.pack(side='right', fill='both', padx=(10,0))
        self.detalles_frame.pack_propagate(False)  # Evita que el frame se encoja
        # Establecer el ancho como 1/3 del total
        self.detalles_frame.configure(width=window_width // 3)
        # Modificar el binding para incluir doble clic
        self.tree.bind('<Double-1>', self.abrir_detalle_cliente)
        
    def abrir_detalle_cliente(self, event):
        selected_item = self.tree.selection()[0]
        cliente_clave = self.tree.item(selected_item)['values'][0]
        cliente = self.clientes_data[cliente_clave]
        DetalleClienteWindow(self.root, cliente)
        
    def mostrar_detalles_cliente(self, event):
        # Limpiar frame de detalles
        for widget in self.detalles_frame.winfo_children():
            widget.destroy()
            
        # Obtener el cliente seleccionado
        selected_item = self.tree.selection()[0]
        cliente_clave = self.tree.item(selected_item)['values'][0]
        cliente = self.clientes_data[cliente_clave]
        
        # Mostrar detalles
        detalles = [
            ("Saldo Total", f"${cliente['saldo']:,.2f}"),
            ("Estado", cliente['estado']),
            ("Fecha de Alta", cliente['fecha'])
        ]
        
        for label_text, value in detalles:
            detail_frame = tk.Frame(self.detalles_frame, bg=self.COLOR_BLANCO)
            detail_frame.pack(fill='x', padx=10, pady=10)
            
            label = tk.Label(detail_frame,
                           text=label_text,
                           font=("Arial", 10),
                           bg=self.COLOR_BLANCO)
            label.pack(side='left')
            
            value_label = tk.Label(detail_frame,
                                 text=value,
                                 font=("Arial", 10, "bold") if "Saldo" in label_text else ("Arial", 10),
                                 fg=self.COLOR_ROJO if "Saldo" in label_text else self.COLOR_NEGRO,
                                 bg=self.COLOR_BLANCO)
            value_label.pack(side='right')

if __name__ == "__main__":
    root = tk.Tk()
    app = CobranzaApp(root)
    root.mainloop()
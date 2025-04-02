import tkinter as tk
import webbrowser
import re

class ClienteManager:
    def __init__(self):
        self.clientes = []

    def agregar_cliente(self, nombre, telefono):
        # Limpiamos el número de teléfono para estandarizar
        telefono_limpio = self.limpiar_numero(telefono)
        cliente = {
            "nombre": nombre,
            "telefono": telefono_limpio
        }
        self.clientes.append(cliente)

    def limpiar_numero(self, telefono):
        # Eliminar caracteres no numéricos
        numero_limpio = re.sub(r'\D', '', telefono)
        
        # Asegurar que el número tenga código de país (asumiendo México +52)
        if not numero_limpio.startswith('52'):
            # Si el número empieza con 0, lo quitamos
            if numero_limpio.startswith('0'):
                numero_limpio = numero_limpio[1:]
            
            # Agregar prefijo de México si no lo tiene
            numero_limpio = '52' + numero_limpio

        return numero_limpio

    def abrir_whatsapp(self, telefono):
        # Limpiar el número
        numero_limpio = self.limpiar_numero(telefono)
        
        # Construir URL de WhatsApp Web
        url = f"https://wa.me/{numero_limpio}"
        
        # Abrir en el navegador predeterminado
        webbrowser.open(url)

class InterfazClientes:
    def __init__(self, master):
        self.master = master
        self.master.title("Gestor de Clientes")
        
        # Instancia del gestor de clientes
        self.cliente_manager = ClienteManager()
        
        # Campos de entrada
        tk.Label(master, text="Nombre:").grid(row=0, column=0)
        self.nombre_entry = tk.Entry(master, width=30)
        self.nombre_entry.grid(row=0, column=1)
        
        tk.Label(master, text="Teléfono:").grid(row=1, column=0)
        self.telefono_entry = tk.Entry(master, width=30)
        self.telefono_entry.grid(row=1, column=1)
        
        # Botón para agregar cliente
        tk.Button(master, text="Agregar Cliente", command=self.agregar_cliente).grid(row=2, column=0, columnspan=2)
        
        # Lista de clientes
        self.lista_clientes = tk.Listbox(master, width=50)
        self.lista_clientes.grid(row=3, column=0, columnspan=2)
        
        # Botón para abrir WhatsApp
        tk.Button(master, text="Abrir WhatsApp", command=self.abrir_chat_whatsapp).grid(row=4, column=0, columnspan=2)

    def agregar_cliente(self):
        nombre = self.nombre_entry.get()
        telefono = self.telefono_entry.get()
        
        if nombre and telefono:
            self.cliente_manager.agregar_cliente(nombre, telefono)
            # Limpiar campos de entrada
            self.nombre_entry.delete(0, tk.END)
            self.telefono_entry.delete(0, tk.END)
            
            # Actualizar lista de clientes
            self.actualizar_lista_clientes()

    def actualizar_lista_clientes(self):
        # Limpiar lista actual
        self.lista_clientes.delete(0, tk.END)
        
        # Agregar clientes a la lista
        for cliente in self.cliente_manager.clientes:
            self.lista_clientes.insert(tk.END, f"{cliente['nombre']} - {cliente['telefono']}")

    def abrir_chat_whatsapp(self):
        # Obtener el índice del cliente seleccionado
        seleccion = self.lista_clientes.curselection()
        
        if seleccion:
            # Obtener el número de teléfono del cliente seleccionado
            indice = seleccion[0]
            cliente = self.cliente_manager.clientes[indice]
            
            # Abrir WhatsApp
            self.cliente_manager.abrir_whatsapp(cliente['telefono'])

# Iniciar la aplicación
def main():
    root = tk.Tk()
    app = InterfazClientes(root)
    root.mainloop()

if __name__ == "__main__":
    main()
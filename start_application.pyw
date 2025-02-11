import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
from database import get_db_connection
import threading
import time
import logging

class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Login")
        
        # Configurar ventana
        window_width = 300
        window_height = 150
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Quitar opción de redimensionar
        self.root.resizable(False, False)
        
        # Frame principal
        self.frame = ttk.Frame(self.root)
        self.frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Componentes
        login_label = ttk.Label(
            self.frame,
            text="Login",
            font=('Helvetica', 12, 'bold')
        )
        login_label.pack(pady=10)
        
        self.login_entry = ttk.Entry(self.frame, width=30)
        self.login_entry.pack(pady=10)
        
        # Bindings
        self.login_entry.bind('<Return>', lambda e: self.validate_login())
        self.login_entry.bind('<KeyRelease>', self.convert_to_uppercase)
        
        # Dar foco al entry
        self.login_entry.focus()
        
    def convert_to_uppercase(self, event):
        """Convertir texto a mayúsculas en tiempo real"""
        current_text = self.login_entry.get()
        self.login_entry.delete(0, tk.END)
        self.login_entry.insert(0, current_text.upper())
        
    def validate_login(self):
        """Validar credenciales"""
        login_text = self.login_entry.get().strip()
        
        # Verificar formato
        if ' ' not in login_text:
            messagebox.showerror("Error", "Formato incorrecto. Use: USUARIO CONTRASEÑA")
            return False
            
        # Separar usuario y contraseña
        username, password = login_text.split(' ', 1)
        
        # Validar contra base de datos
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")
            return False
            
        try:
            cursor = conn.cursor()
            query = """
                SELECT COUNT(*) 
                FROM Usuarios 
                WHERE Usuario = ? AND Password = ?
            """
            cursor.execute(query, (username, password))
            result = cursor.fetchone()[0]
            
            if result > 0:
                self.root.destroy()  # Cerrar ventana de login
                iniciar_aplicacion()  # Iniciar el proceso de carga y la aplicación
                return True
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos")
                self.login_entry.delete(0, tk.END)
                return False
                
        except pyodbc.Error as e:
            messagebox.showerror("Error", f"Error de base de datos: {str(e)}")
            return False
        finally:
            conn.close()

def start_application():
    """Función principal para iniciar la aplicación"""
    login = LoginWindow()
    login.root.mainloop()


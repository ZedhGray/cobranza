@echo off

rem Activar el entorno virtual
call venv\Scripts\activate

rem Ejecutar la aplicación en modo oculto
start /min python cobranza_app.py

rem Salir sin esperar a que se cierre la ventana
exit
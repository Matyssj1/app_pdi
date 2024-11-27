import mysql.connector
import configparser
import tkinter as tk
from tkinter import ttk, messagebox

def leer_configuracion(nombre_seccion):
    """Leer configuración desde config.ini"""
    config = configparser.ConfigParser()
    config.read("config.ini")  # Asegúrate de que config.ini esté en el mismo directorio que este script
    if nombre_seccion in config:
        return config[nombre_seccion]
    else:
        raise ValueError(f"La sección '{nombre_seccion}' no existe en config.ini.")

def conectar_bd(nombre_seccion="mysql_empresa"):
    """Conectar a la base de datos MySQL usando la configuración del archivo INI"""
    try:
        config = leer_configuracion(nombre_seccion)
        conexion = mysql.connector.connect(
            host=config.get("host"),
            user=config.get("user"),
            password=config.get("password"),
            database=config.get("database")
        )
        return conexion
    except mysql.connector.Error as err:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos: {err}")
        return None
    except ValueError as err:
        messagebox.showerror("Error de Configuración", str(err))
        return None

def obtener_tablas(conexion):
    """Obtener las tablas de la base de datos"""
    cursor = conexion.cursor()
    cursor.execute("SHOW TABLES")
    tablas = cursor.fetchall()
    return [tabla[0] for tabla in tablas]

def obtener_columnas(conexion, tabla):
    """Obtener las columnas de una tabla específica"""
    cursor = conexion.cursor()
    cursor.execute(f"DESCRIBE {tabla}")
    columnas = cursor.fetchall()
    return [columna[0] for columna in columnas]

def crear_vista():
    """Crear una vista SQL y mostrar los resultados"""
    tablas_seleccionadas = [tabla for tabla, var in tablas_vars.items() if var.get()]
    columnas_seleccionadas = [lista_columnas.get(i) for i in lista_columnas.curselection()]

    if not tablas_seleccionadas or not columnas_seleccionadas:
        messagebox.showwarning("Selección Vacía", "Por favor, selecciona al menos una tabla y una columna.")
        return

    nombre_vista = entrada_nombre_vista.get().strip()
    if not nombre_vista:
        nombre_vista = "vista"
    nombre_vista = generar_nombre_unico(nombre_vista)

    # Generar la consulta
    columnas = ', '.join(columnas_seleccionadas)
    if len(tablas_seleccionadas) > 1:
        # Usa un CROSS JOIN para combinar tablas (o INNER JOIN si hay relaciones definidas)
        tablas = f" CROSS JOIN ".join(tablas_seleccionadas)
    else:
        tablas = tablas_seleccionadas[0]

    query = f"CREATE OR REPLACE VIEW {nombre_vista} AS SELECT DISTINCT {columnas} FROM {tablas}"

    try:
        cursor = conexion.cursor()
        cursor.execute(query)
        conexion.commit()

        mostrar_resultados_vista(nombre_vista, columnas_seleccionadas)

    except mysql.connector.Error as err:
        messagebox.showerror("Error al Crear la Vista", f"No se pudo crear la vista: {err}")

def generar_nombre_unico(nombre_base):
    """Generar un nombre único para la vista"""
    contador = 1
    nombre_vista = nombre_base
    while True:
        try:
            cursor = conexion.cursor()
            cursor.execute(f"SHOW TABLES LIKE '{nombre_vista}'")
            if cursor.fetchone() is None:
                break
            contador += 1
            nombre_vista = f"{nombre_base}_{contador}"
        except mysql.connector.Error as err:
            messagebox.showerror("Error en la Verificación", f"No se pudo verificar el nombre: {err}")
            break
    return nombre_vista

def mostrar_resultados_vista(nombre_vista, columnas_seleccionadas):
    """Mostrar los resultados de la vista"""
    try:
        cursor = conexion.cursor()
        cursor.execute(f"SELECT * FROM {nombre_vista}")
        resultados = cursor.fetchall()

        resultado_window = tk.Toplevel(root)
        resultado_window.title("Resultados de la Vista")

        tree = ttk.Treeview(resultado_window, columns=columnas_seleccionadas, show="headings")
        tree.pack(fill="both", expand=True)

        for columna in columnas_seleccionadas:
            tree.heading(columna, text=columna)

        for fila in resultados:
            tree.insert("", "end", values=fila)

        scrollbar = ttk.Scrollbar(resultado_window, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    except mysql.connector.Error as err:
        messagebox.showerror("Error en la Consulta de Vista", f"No se pudo ejecutar la consulta: {err}")

def cargar_columnas():
    """Cargar las columnas cuando se seleccionan tablas"""
    lista_columnas.delete(0, tk.END)
    tablas_seleccionadas = [tabla for tabla, var in tablas_vars.items() if var.get()]

    if tablas_seleccionadas:
        columnas_set = []
        for tabla in tablas_seleccionadas:
            columnas = obtener_columnas(conexion, tabla)
            columnas_set.extend(columnas)

        for columna in columnas_set:
            if columna not in lista_columnas.get(0, tk.END):
                lista_columnas.insert(tk.END, columna)

root = tk.Tk()
root.title("Generador de Vistas")
root.geometry("800x600")

# Selección de la base de datos
frame_seleccion = tk.Frame(root)
frame_seleccion.pack(pady=10)
label_seccion = tk.Label(frame_seleccion, text="Sección del INI:")
label_seccion.pack(side=tk.LEFT)
entrada_seccion = tk.Entry(frame_seleccion)
entrada_seccion.pack(side=tk.LEFT)

def conectar_a_seccion():
    global conexion
    nombre_seccion = entrada_seccion.get().strip()
    conexion = conectar_bd(nombre_seccion)
    if conexion:
        inicializar_gui()

boton_conectar = tk.Button(frame_seleccion, text="Conectar", command=conectar_a_seccion)
boton_conectar.pack(side=tk.LEFT)

def inicializar_gui():
    frame_tablas = tk.LabelFrame(root, text="Selecciona Tablas", padx=10, pady=10)
    frame_tablas.pack(padx=10, pady=10, fill="both", expand=True)

    tablas = obtener_tablas(conexion)
    global tablas_vars
    tablas_vars = {}

    for tabla in tablas:
        var = tk.BooleanVar()
        check = tk.Checkbutton(frame_tablas, text=tabla, variable=var, command=cargar_columnas)
        check.pack(anchor='w')
        tablas_vars[tabla] = var

    frame_nombre_vista = tk.Frame(root)
    frame_nombre_vista.pack(pady=10)
    label_nombre_vista = tk.Label(frame_nombre_vista, text="Nombre de la Vista:")
    label_nombre_vista.pack(side=tk.LEFT)
    global entrada_nombre_vista
    entrada_nombre_vista = tk.Entry(frame_nombre_vista)
    entrada_nombre_vista.pack(side=tk.LEFT)

    frame_columnas = tk.LabelFrame(root, text="Selecciona Columnas", padx=10, pady=10)
    frame_columnas.pack(padx=10, pady=10, fill="both", expand=True)

    global lista_columnas
    lista_columnas = tk.Listbox(frame_columnas, selectmode=tk.MULTIPLE)
    lista_columnas.pack(fill="both", expand=True)

    boton_generar = tk.Button(root, text="Crear Vista", command=crear_vista)
    boton_generar.pack(pady=10)

root.mainloop()

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import importlib.util, os, subprocess, sys
import math

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

#CÀRREGA DE MÒDULS
BASE = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()


def load_module(path, name): #Busca i llegeix els mòduls de codi externs per poder utilitzar les seves funcions dins de la interfície gràfica
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Carreguem els teus mòduls originals
airport = load_module('airport.py', 'airport_mod')
flights = load_module('aircraft.py', 'flights_mod')
lebl = load_module('LEBL.py', 'lebl_mod')

airports = []
aircrafts = []
bcn_airport = None
simulation_running = False
LAST_GATE_CHANGED = None
def open_google_earth(path):#Executa l'aplicació externa de Google Earth al ordinador passant-li directament el arxiu kml
    try:
        absf = os.path.abspath(path)

        if sys.platform.startswith('win'):
            possible_paths = [
                r"C:\Program Files\Google\Google Earth Pro\client\googleearth.exe",
                r"C:\Program Files (x86)\Google\Google Earth Pro\client\googleearth.exe"
            ]

            opened = False
            for p in possible_paths:
                if os.path.exists(p):
                    subprocess.Popen([p, absf])
                    opened = True
                    break

            if not opened:
                os.startfile(absf)

        elif sys.platform == 'darwin':
            subprocess.Popen(['open', absf])
        else:
            subprocess.Popen(['xdg-open', absf])

    except Exception as e:
        print("Error obrint Google Earth:", e)


# INTERFÍCIE PRINCIPAL
root = tk.Tk()
root.title('Air Traffic Manager')
root.geometry('1850x950')
BG = "#111827"  # Fondo oscuro
BTN = "#3b82f6"  # Azul moderno
TEXT = "#e5e7eb"  # Gris claro elegante

root.configure(bg=BG)

style = ttk.Style()
style.theme_use('clam')

# GENERAL
style.configure('.', background=BG, foreground=TEXT, fieldbackground=BG, font=('Segoe UI', 12))

# NOTEBOOK
style.configure('TNotebook', background=BG, borderwidth=0)
style.configure('TNotebook.Tab', background=BTN, foreground='white', padding=(15, 8), font=('Segoe UI', 13, 'bold'))
style.map('TNotebook.Tab', background=[('selected', '#2563eb')], foreground=[('selected', 'white')])

# BOTONES
style.configure('TButton', background=BTN, foreground='white', borderwidth=0, focusthickness=0, padding=4,
                font=('Segoe UI', 9, 'bold'))
style.map('TButton', background=[('active', '#2563eb')], foreground=[('active', 'white')])

# TREEVIEW
style.configure('Treeview', background=BG, foreground=TEXT, fieldbackground=BG, rowheight=30, borderwidth=0,
                relief='flat', font=('Segoe UI', 9))
style.configure('Treeview.Heading', background=BTN, foreground='white', borderwidth=0, font=('Segoe UI', 14, 'bold'))
style.map('Treeview', background=[('selected', BTN)], foreground=[('selected', 'white')])

# DISTRIBUCIÓ PRINCIPAL (LAYOUT GLOBAL)
# Panel Lateral Fijo (Sidebar) a la izquierda para TODOS los botones
sidebar = tk.Frame(root, bg=BG, width=260)
sidebar.pack(side='left', fill='y', padx=10, pady=10)

# Contenedor Derecho para el Notebook de Visualización y Consola Log
right_container = tk.Frame(root, bg=BG)
right_container.pack(side='right', fill='both', expand=True, padx=10, pady=10)
# PANEL KPI SUPERIOR

kpi_frame = tk.Frame(right_container, bg="#1f2937")
kpi_frame.pack(side='top', fill='x', pady=(0, 8))

sim_time_label = tk.Label(kpi_frame, text="Hora: --:--", bg="#1f2937", fg="white", font=("Segoe UI", 12, "bold"))
sim_time_label.pack(side='left', padx=15)

occupied_label = tk.Label(kpi_frame,text="Ocupades: 0",bg="#1f2937",fg="#ef4444",font=("Segoe UI", 12, "bold"))
occupied_label.pack(side='left', padx=15)

free_label = tk.Label(kpi_frame,text="Lliures: 0",bg="#1f2937",fg="#10b981",font=("Segoe UI", 12, "bold"))
free_label.pack(side='left', padx=15)

util_label = tk.Label(kpi_frame,text="Utilització: 0%",bg="#1f2937",fg="#f59e0b",font=("Segoe UI", 12, "bold"))
util_label.pack(side='left', padx=15)

sim_progress = ttk.Progressbar(kpi_frame,orient="horizontal",mode="determinate",length=300)
sim_progress.pack(side='right', padx=20)

# Log/Consola en la parte inferior del contenedor derecho
log = ScrolledText(right_container, height=8, bg='#0b1320', fg='#22c55e', font=('Consolas', 14))
log.pack(side='bottom', fill='x', pady=(10, 0))


def write(msg):#Escriu misatges en la consola del que sesta fent
    log.insert('end', f"{msg}\n")
    log.see('end')


# Notebook principal ocupando el resto del espacio del contenedor derecho
nb = ttk.Notebook(right_container)
nb.pack(side='top', fill='both', expand=True)

# Las pestañas contienen directamente los paneles de datos
ra = ttk.Frame(nb)
rv = ttk.Frame(nb)
rg = ttk.Frame(nb)

nb.add(ra, text=' Aeroports ')
nb.add(rv, text=' Vols ')
nb.add(rg, text=' Portes ')

# PESTANYA 1: AEROPORTS
tree_ap = ttk.Treeview(ra, columns=('code', 'lat', 'lon', 'schengen'), show='headings')
for c in ('code', 'lat', 'lon', 'schengen'):
    tree_ap.heading(c, text=c.upper())
    tree_ap.column(c, anchor='center')

fig_ap = Figure(figsize=(6, 5), facecolor='#1b263b')
ax_ap = fig_ap.add_subplot(111)
ax_ap.set_facecolor('#1b263b')
canvas_ap = FigureCanvasTkAgg(fig_ap, master=ra)
canvas_ap_w = canvas_ap.get_tk_widget()

map_view_ap = tk.Frame(ra, bg='#1b263b')
map_info_ap = tk.Label(map_view_ap,
                       text="🗺️ VISTA DE MAPA KML ACTIVA\n\nEl fitxer d'aeroports s'ha carregat al visualitzador.",
                       fg='white', bg='#1b263b', font=('Segoe UI', 16, 'bold'))
map_info_ap.pack(pady=100)

all_ap_w = [tree_ap, canvas_ap_w, map_view_ap]


def show_ap_view(target):#Neteja el panell d'aeroports i fa visible el tipus de format (taula o gràfic) seleccionat
    nb.select(ra)  # Cambio automático de pestaña UX
    for w in all_ap_w: w.pack_forget()
    target.pack(fill='both', expand=True)


def load_airports_file():#Permet triar el fitxer d'aeroports del disc dur, en llegeix la informació i mostra quants n'ha trobat
    global airports
    fn = filedialog.askopenfilename()
    if fn:
        airports = airport.LoadAirports(fn)
        refresh_ap_table()
        write(f"Aeroports carregats correctament.")
        show_ap_view(tree_ap)


def refresh_ap_table():#Actualitza la taula visual d'aeroports per mostrar les dades noves que hi hagi a la memòria
    for i in tree_ap.get_children(): tree_ap.delete(i)
    for a in airports:
        tree_ap.insert('', 'end', values=(a.code, round(a.lat, 4), round(a.lon, 4), "Sí" if a.schengen else "No"))


def add_airport_ui():#Permet afegir un aeroport a mà de manera guiada escrivint les seves coordenades
    code = simpledialog.askstring("Nou Aeroport", "Codi ICAO (Ex: LEBL):")
    if not code: return
    try:
        lat_str = simpledialog.askstring("Latitud", "Format: N411749 o decimal (41.29):")
        lon_str = simpledialog.askstring("Longitud", "Format: E0020459 o decimal (2.08):")
        if not lat_str or not lon_str: return

        lat = airport.convert_coord(lat_str) if any(c in lat_str.upper() for c in 'NS') else float(lat_str)
        lon = airport.convert_coord(lon_str) if any(c in lon_str.upper() for c in 'EW') else float(lon_str)

        new_ap = airport.Airport(code.upper(), lat, lon)
        airport.SetSchengen(new_ap)
        airport.AddAirport(airports, new_ap)

        refresh_ap_table()
        write(f"Aeroport {code.upper()} afegit correctament.")
        show_ap_view(tree_ap)
    except Exception as e:
        messagebox.showerror("Error", f"Dades incorrectes: {e}")


def remove_airport_ui():#Elimina de la llista l'aeroport que l'usuari hagi marcat amb el ratolí a la pantalla
    selected = tree_ap.selection()
    if not selected:
        messagebox.showwarning("Atenció", "Selecciona un aeroport de la taula per eliminar-lo.")
        return
    item = tree_ap.item(selected[0])
    code = item['values'][0]
    if messagebox.askyesno("Confirmar", f"Vols eliminar l'aeroport {code}?"):
        airport.RemoveAirport(airports, code)
        refresh_ap_table()
        write(f"Aeroport {code} eliminat.")


def draw_airport_plot():#Dibuixa directament a la pantalla el gràfic de barres que divideix els aeroports segons si són Schengen
    if not airports:
        messagebox.showwarning("Atenció", "Primer has de carregar el fitxer d'aeroports.")
        return
    show_ap_view(canvas_ap_w)
    sch = sum(1 for a in airports if a.schengen)
    non = len(airports) - sch
    ax_ap.clear()
    ax_ap.bar(['Aeroports'], [sch], label='Schengen', color='#2ecc71')
    ax_ap.bar(['Aeroports'], [non], bottom=[sch], label='No Schengen', color='#e74c3c')
    ax_ap.legend(facecolor='#1b263b', labelcolor='white')
    ax_ap.tick_params(colors='white')
    ax_ap.set_title('Distribució Aeroports (Schengen vs No)', color='white')
    canvas_ap.draw()


def map_airports():#Crea un fitxer kml i coloca cada punt de l'aeroport en ell per despres obrirlo en google earth
    if not airports:
        messagebox.showwarning("Atenció", "Primer has de carregar el fitxer d'aeroports.")
        return
    airport.MapAirports(airports)
    write('Mapa aeroports creat. Obrint a Google Earth...')
    open_google_earth('airports.kml')
# PESTANYA 2: VOLS

tree_fv = ttk.Treeview(rv, columns=('id', 'origin', 'time', 'company'), show='headings')
for c in ('id', 'origin', 'time', 'company'):
    tree_fv.heading(c, text=c.upper())
    tree_fv.column(c, anchor='center')

fig_fv = Figure(figsize=(6, 5), facecolor='#1b263b')
ax_fv = fig_fv.add_subplot(111)
ax_fv.set_facecolor('#1b263b')
canvas_fv = FigureCanvasTkAgg(fig_fv, master=rv)
canvas_fv_w = canvas_fv.get_tk_widget()

map_view_fv = tk.Frame(rv, bg='#1b263b')
map_info_fv = tk.Label(map_view_fv,
                       text="🌍 VISTA DE MAPA DE VOLS ACTIVA\n\nTrajectòries calculades. Comprovant distàncies > 2000km.",
                       fg='white', bg='#1b263b', font=('Segoe UI', 16, 'bold'))
map_info_fv.pack(pady=100)

all_fv_w = [tree_fv, canvas_fv_w, map_view_fv]


def show_fv_view(target):#Neteja el panell de vols i fa visible el tipus de format (taula o gràfic) seleccionat
    nb.select(rv)  # Cambio automático de pestaña UX
    for w in all_fv_w: w.pack_forget()
    target.pack(fill='both', expand=True)


def load_flights_file():#Obre el cercador de fitxers per carregar a la memòria la llista de vols d'arribada
    global aircrafts
    fn = filedialog.askopenfilename()
    if fn:
        aircrafts = flights.LoadArrivals(fn)
        refresh_fv_table()
        write(f"Vols carregats correctament.")
        show_fv_view(tree_fv)


def refresh_fv_table():#Actualitza la taula visual de vols per mostrar les dades noves que hi hagi a la memòria
    for i in tree_fv.get_children(): tree_fv.delete(i)
    for p in aircrafts:
        tree_fv.insert('', 'end', values=(p.id, p.origin, p.time, p.company))


def add_flight_ui():#Permet afegir un vol a la llista manualment omplint els camps de text de la interfície
    f_id = simpledialog.askstring("Nou Vol", "Codi del vol (Ex: VY1234):")
    if not f_id: return
    origin = simpledialog.askstring("Origen", "Codi ICAO Origen (Ex: LEMD):")
    time = simpledialog.askstring("Hora", "Format HH:MM:")
    company = simpledialog.askstring("Companyia", "Nom de l'aerolínia:")

    if f_id and origin and time and company:
        new_flight = flights.Aircraft(f_id.upper(), origin.upper(), time, company.upper())
        aircrafts.append(new_flight)
        refresh_fv_table()
        write(f"Vol {f_id.upper()} afegit a la llista.")
        show_fv_view(tree_fv)
    else:
        messagebox.showwarning("Atenció", "Has d'omplir tots els camps.")


def draw_arrivals_plot():#Dibuixa directament a la pantalla el gràfic estadístic de les arribades per hora
    if not aircrafts:
        messagebox.showwarning("Atenció", "Primer has de carregar el fitxer de vols.")
        return
    show_fv_view(canvas_fv_w)
    hours = [0] * 24
    for p in aircrafts:
        try:
            h = int(p.time.split(':')[0])
            hours[h] += 1
        except:
            pass
    ax_fv.clear()
    ax_fv.bar(range(24), hours, color='#3498db')
    ax_fv.set_title('Arribades per Hora', color='white')
    ax_fv.tick_params(colors='white')
    canvas_fv.draw()


def draw_airlines_plot():#Dibuixa directament a la pantalla el gràfic de barres amb els vols de cada companyia aèria
    if not aircrafts:
        messagebox.showwarning("Atenció", "Primer has de carregar el fitxer de vols.")
        return
    all_comps = sorted(list(set(a.company for a in aircrafts)))
    top = tk.Toplevel(root)
    lb = tk.Listbox(top, selectmode='multiple', height=15)
    lb.pack(padx=10, pady=10, fill='both', expand=True)
    for c in all_comps: lb.insert('end', c)

    def apply():#Agafa les companyies seleccionades, compta els seus vols i genera el gràfic de barres lila actualitzant la pantalla
        sel = [lb.get(i) for i in lb.curselection()]
        if not sel: return
        show_fv_view(canvas_fv_w)
        d = {c: sum(1 for a in aircrafts if a.company == c) for c in sel}
        ax_fv.clear()
        ax_fv.bar(d.keys(), d.values(), color='#9b59b6')
        ax_fv.tick_params(colors='white', rotation=45)
        canvas_fv.draw()
        top.destroy()

    ttk.Button(top, text="Dibuixar", command=apply).pack()


def draw_types_plot():#Dibuixa un gràfic de barres que diferencia de forma visual quants vols són de tipus Schengen i quants no
    if not aircrafts:
        messagebox.showwarning("Atenció", "Primer has de carregar el fitxer de vols.")
        return
    show_fv_view(canvas_fv_w)
    sch_prefixes = ['LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH', 'BI', 'LI', 'EV', 'EY',
                    'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS']
    sch = sum(1 for a in aircrafts if a.origin[:2] in sch_prefixes)
    non = len(aircrafts) - sch
    ax_fv.clear()
    ax_fv.bar(['Vols'], [sch], label='Schengen', color='#2ecc71')
    ax_fv.bar(['Vols'], [non], bottom=[sch], label='No Schengen', color='#e74c3c')
    ax_fv.legend(facecolor='#1b263b', labelcolor='white')
    ax_fv.tick_params(colors='white')
    canvas_fv.draw()


def map_flights():#Genera el fitxer de mapa amb les rutes dels avions en línia recta enllaçades cap a Barcelona i pinta les rutes de més de 2000km
    if not aircrafts:
        messagebox.showwarning("Atenció", "Primer has de carregar el fitxer de vols.")
        return
    flights.MapFlights(aircrafts, airports)
    ruta_kml = 'flights.kml'
    try:
        if os.path.exists(ruta_kml):
            with open(ruta_kml, 'r', encoding='utf-8') as f:
                contingut = f.read()
            LEBL_COORDS = (41.2974, 2.0833)
            for a in aircrafts:
                origin_ap = next((ap for ap in airports if ap.code == a.origin), None)
                if origin_ap and not origin_ap.schengen:
                    dist = flights.distancia((origin_ap.lat, origin_ap.lon), LEBL_COORDS)
                    if dist > 2000:
                        search_pattern = f"<name>{a.id} from {a.origin}</name>"
                        if search_pattern in contingut:
                            parts = contingut.split(search_pattern)
                            if len(parts) > 1:
                                parts[1] = parts[1].replace("<color>ff00ff00</color>", "<color>ffff0000</color>", 1)
                                parts[1] = parts[1].replace("<color>ff0000ff</color>", "<color>ffff0000</color>", 1)
                                contingut = search_pattern.join(parts)
            if '<tessellate>1</tessellate>' not in contingut:
                contingut = contingut.replace('<LineString>', '<LineString>\n<tessellate>1</tessellate>')
            with open(ruta_kml, 'w', encoding='utf-8') as f:
                f.write(contingut)
            write('Vols No-Schengen > 2000km pintats de blau.')
        else:
            write(f"Error: No s'ha trobat el fitxer a {ruta_kml}")
    except Exception as e:
        write(f"Error en el processat: {e}")
    open_google_earth(ruta_kml)


def load_departures_file():#Obre el cercador de fitxers per carregar a la memòria la llista de vols de sortida i els enllaça amb les arribades
    global aircrafts
    fn = filedialog.askopenfilename(title="Selecciona el fitxer de SORTIDES (Departures)")
    if fn:
        departures = flights.LoadDepartures(fn)
        write(f"Sortides carregades. Fusionant amb arribades...")
        aircrafts = flights.MergeMovements(aircrafts, departures)
        refresh_fv_table()
        write("Llegades i sortides fusionades correctament.")


# PESTANYA 3: PORTES / GATES
tree_gates = ttk.Treeview(rg, columns=('terminal', 'area', 'gate', 'status', 'aircraft'), show='headings')
for c in ('terminal', 'area', 'gate', 'status', 'aircraft'):
    tree_gates.heading(c, text=c.upper())
    tree_gates.column(c, anchor='center')

fig_gates = Figure(figsize=(6, 5), facecolor='#1b263b')
ax_gates = fig_gates.add_subplot(111)
ax_gates.set_facecolor('#1b263b')
canvas_gates = FigureCanvasTkAgg(fig_gates, master=rg)
canvas_gates_w = canvas_gates.get_tk_widget()

#Vista Gràfica esquemàtica (T1 / T2 SEPARATS EN SUB-PESTAYAS)
SCH_PIER_COL = '#075A81'
SCH_FREE_COL = '#2ECC71'
SCH_OCC_COL = '#E74C3C'

graphical_view = tk.Frame(rg, bg='#1b263b')
gv_notebook = ttk.Notebook(graphical_view)
gv_notebook.pack(fill='both', expand=True)

#Terminal 1 con Scrollbar Horizontal y Vertical
fa_t1 = tk.Frame(gv_notebook, bg='#1b263b')
gv_notebook.add(fa_t1, text='Terminal T1')

scroll_x_t1 = ttk.Scrollbar(fa_t1, orient="horizontal")
scroll_x_t1.pack(side='bottom', fill='x')

scroll_y_t1 = ttk.Scrollbar(fa_t1, orient="vertical")
scroll_y_t1.pack(side='right', fill='y')

canvas_t1 = tk.Canvas(fa_t1, bg='#1b263b', highlightthickness=0,
                      xscrollcommand=scroll_x_t1.set,
                      yscrollcommand=scroll_y_t1.set)
canvas_t1.pack(side='left', fill='both', expand=True)

scroll_x_t1.config(command=canvas_t1.xview)
scroll_y_t1.config(command=canvas_t1.yview)

# Terminal 2 con Scrollbar Horizontal y Vertical
fa_t2 = tk.Frame(gv_notebook, bg='#1b263b')
gv_notebook.add(fa_t2, text='Terminal T2')

scroll_x_t2 = ttk.Scrollbar(fa_t2, orient="horizontal")
scroll_x_t2.pack(side='bottom', fill='x')

scroll_y_t2 = ttk.Scrollbar(fa_t2, orient="vertical")
scroll_y_t2.pack(side='right', fill='y')

canvas_t2 = tk.Canvas(fa_t2, bg='#1b263b', highlightthickness=0,
                      xscrollcommand=scroll_x_t2.set,
                      yscrollcommand=scroll_y_t2.set)
canvas_t2.pack(side='left', fill='both', expand=True)

scroll_x_t2.config(command=canvas_t2.xview)
scroll_y_t2.config(command=canvas_t2.yview)


# FUNCIÓ DE SUPORT PER PROPAGAR EL SCROLL DE RATOLÍ
def _on_mousewheel(event, canvas):#Gestiona la roda del ratolí de l'usuari per fer anar amunt i avall els mapes de les terminals
    # Compatible amb Windows y Mac OS
    if sys.platform == 'darwin':
        canvas.yview_scroll(int(-1 * event.delta), "units")
    else:
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# Enllacem el moviment de roda de ratolí quan el cursor entra a la zona de dibuix
canvas_t1.bind("<MouseWheel>", lambda e: _on_mousewheel(e, canvas_t1))
canvas_t2.bind("<MouseWheel>", lambda e: _on_mousewheel(e, canvas_t2))

all_gates_w = [tree_gates, canvas_gates_w, graphical_view]


def show_gates_view(target):#Neteja el panell de portes i fa visible el tipus de format (taula, gràfic o plànol) seleccionat
    nb.select(rg)  # Cambio automático de pestaña UX
    for w in all_gates_w: w.pack_forget()
    target.pack(fill='both', expand=True)


def draw_schematic(canvas, term_id_prefix):#Dibuixa un mapa visual de quadres de colors que representa l'ocupació en temps real de totes les portes de l'aeroport
    canvas.delete("all")
    if not bcn_airport or bcn_airport == -1: return

    occupancy = lebl.GateOccupancy(bcn_airport)
    if occupancy == -1: return

    TEXT_BRIGHT = '#ffffff'
    TEXT_MUTED = '#d1d5db'
    pier_border_col = '#1e3a8a'

    areas_dict = {}
    terminal_real_name = term_id_prefix

    for item in occupancy:
        terminal_str = str(item[0])
        if term_id_prefix in terminal_str:
            terminal_real_name = terminal_str
            area_str = str(item[1])
            gate_name = str(item[2])
            is_occupied = item[3]

            if area_str not in areas_dict:
                areas_dict[area_str] = []

            areas_dict[area_str].append({"name": gate_name, "occupied": is_occupied})

    # Título principal de la terminal
    canvas.create_text(50, 30, text=f"{terminal_real_name}", anchor='nw', fill=TEXT_BRIGHT,
                       font=('Segoe UI Semibold', 20))

    if not areas_dict:
        # Mensaje de estado vacío amigable (Empty state)
        canvas.create_text(30, 80, text="(Cap porta trobada per aquesta terminal)", anchor='nw', fill='gray',
                           font=('Segoe UI', 16))
        return

    # LEYENDA VISUAL PREMIUM (Esquina Superior Derecha)
    leg_x = 750
    canvas.create_rectangle(leg_x, 30, leg_x + 20, 45, fill=SCH_FREE_COL, outline="")
    canvas.create_text(leg_x + 30, 37, text="Porta Lliure", fill=TEXT_MUTED, font=('Segoe UI', 11), anchor='w')

    canvas.create_rectangle(leg_x + 150, 30, leg_x + 170, 45, fill=SCH_OCC_COL, outline="")
    canvas.create_text(leg_x + 180, 37, text="Porta Ocupada", fill=TEXT_MUTED, font=('Segoe UI', 11), anchor='w')
    # CONFIGURACIÓ DE MEDIDAS AMPLIADAS
    PIER_THICKNESS = 24
    CONCOURSE_H = 24
    H_GAP_PIERS = 380
    START_X = 180
    START_Y = 110  # Bajado un poco para no pisar la leyenda
    GATE_W, GATE_H = 45, 22
    SIDE_PAD = 15
    TEXT_GAP = 12
    VERT_GAP = 60
    area_list = sorted(list(areas_dict.keys()))
    total_piers = len(area_list)

    # 1. Dibuja el pasillo central horizontal
    total_width = (total_piers - 1) * H_GAP_PIERS + PIER_THICKNESS
    canvas.create_rectangle(START_X, START_Y, START_X + total_width, START_Y + CONCOURSE_H,
                            fill=SCH_PIER_COL, outline=pier_border_col, width=2)

    pierStartY = START_Y

    for i, area_id in enumerate(area_list):
        gates = areas_dict[area_id]
        curStartX = START_X + i * H_GAP_PIERS

        num_rows = (len(gates) + 1) // 2
        pierHeight = max(250, num_rows * VERT_GAP + 60)

        # Dibuja el muelle vertical (Pier)
        canvas.create_rectangle(curStartX, pierStartY, curStartX + PIER_THICKNESS, pierStartY + pierHeight,
                                fill=SCH_PIER_COL, outline=pier_border_col, width=2)

        # Etiqueta inferior del muelle
        canvas.create_text(curStartX + PIER_THICKNESS / 2, pierStartY + pierHeight + 30,
                           text=f"Àrea {area_id}", fill=TEXT_BRIGHT, font=('Segoe UI Semibold', 16), anchor='center')

        gates.sort(key=lambda g: g["name"])

        #  Colocación de Puertas y Etiquetas
        gateY = pierStartY + 40

        for index, gate in enumerate(gates):
            is_left = (index % 2 == 0)

            if gate["occupied"]:
                boxColor = SCH_OCC_COL
                boxOutline = '#ffffff'
                boxWidth = 2
            else:
                boxColor = SCH_FREE_COL
                boxOutline = pier_border_col
                boxWidth = 1
            if gate["name"] == LAST_GATE_CHANGED:
                boxColor = '#facc15'
                boxOutline = '#000000'
                boxWidth = 3
            if is_left:
                spot_X1 = curStartX - SIDE_PAD - GATE_W
                spot_X2 = curStartX - SIDE_PAD
                label_X = spot_X1 - TEXT_GAP
                textAnchor = 'e'
            else:
                spot_X1 = curStartX + PIER_THICKNESS + SIDE_PAD
                spot_X2 = curStartX + PIER_THICKNESS + SIDE_PAD + GATE_W
                label_X = spot_X2 + TEXT_GAP
                textAnchor = 'w'

            # Dibujamos el rectángulo de la puerta
            canvas.create_rectangle(spot_X1, gateY, spot_X2, gateY + GATE_H,
                                    fill=boxColor, outline=boxOutline, width=boxWidth)

            # Dibujamos el texto
            canvas.create_text(label_X, gateY + GATE_H / 2,
                               text=gate["name"], fill=TEXT_MUTED, font=('Segoe UI', 12), anchor=textAnchor)

            if not is_left:
                gateY += VERT_GAP

    # Forzar el cálculo del recuadro total para habilitar los scrollbars
    canvas.configure(scrollregion=canvas.bbox("all"))


def load_airport_structure_ui():#Llegeix el fitxer de configuració de l'aeroport de Barcelona per definir-ne les terminals i les zones
    global bcn_airport
    fn = filedialog.askopenfilename()
    if fn:
        bcn_airport = lebl.LoadAirportStructure(fn)
        if bcn_airport == -1:
            messagebox.showerror("Error", "No s'ha pogut carregar l'estructura de l'aeroport.")
            write("Error carregant l'estructura de l'aeroport.")
        else:
            write("Estructura de l'aeroport carregada correctament.")
            refresh_gates_table()
            show_graphical_occupancy_ui()


def refresh_gates_table():#Actualitza la taula de portes mostrant quines estan lliures o el codi de l'avió allotjat
    for i in tree_gates.get_children(): tree_gates.delete(i)
    if bcn_airport is None or bcn_airport == -1: return
    occupancy = lebl.GateOccupancy(bcn_airport)
    if occupancy == -1:
        write("Error obtenint l'ocupació de portes.")
        return
    for item in occupancy:
        terminal, area, gate, occupied, aircraft_id = item
        status = "Occupied" if occupied else "Free"
        tree_gates.insert('', 'end', values=(terminal, area, gate, status, aircraft_id))

def update_simulation_stats(current_time=0): #Calcula i actualitza en temps real les estadistiques que surten a l'interfaz

    if bcn_airport is None or bcn_airport == -1:
        return

    occupancy = lebl.GateOccupancy(bcn_airport)

    total = len(occupancy)

    occupied = sum(
        1 for x in occupancy
        if x[3]
    )

    free = total - occupied

    percent = (
        occupied / total * 100
        if total > 0 else 0
    )

    sim_time_label.config(text=f"Hora: {current_time//60:02d}:{current_time%60:02d}")

    occupied_label.config(text=f"Ocupades: {occupied}")

    free_label.config(text=f"Lliures: {free}")

    util_label.config(text=f"Utilització: {percent:.1f}%")

def assign_gates_ui():#Aplica l'algorisme d'assignació automàtica de portes a tots els avions registrats
    global bcn_airport, aircrafts, simulation_running
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció",
                               "Primer has de carregar l'estructura de l'aeroport des de la sección de Portes.")
        return
    if len(aircrafts) == 0:
        messagebox.showwarning("Atenció", "Primer has de carregar els vols des de la secció de Vols.")
        return

    assigned, not_assigned = 0, 0
    for aircraft in aircrafts:
        gate_name = lebl.AssignGate(bcn_airport, aircraft)
        if gate_name == -1:
            write("No s'ha pogut assignar porta al vol " + aircraft.id)
            not_assigned += 1
        else:
            write("Vol " + aircraft.id + " assignat a la porta " + gate_name)
            assigned += 1

    refresh_gates_table()
    show_graphical_occupancy_ui()
    write("Assignació acabada. Assignats: " + str(assigned) + ", no assignats: " + str(not_assigned))


def show_gate_occupancy_ui():#Actualitza i mostra de manera textual quines portes estan lliures o ocupades en aquell moment
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return
    refresh_gates_table()
    show_gates_view(tree_gates)
    write("Ocupació de portes mostrada a la taula.")


def plot_gate_occupancy_ui():#Dibuixa a la pantalla un gràfic de barres amb el recompte de portes lliures vs ocupades per terminal
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return

    show_gates_view(canvas_gates_w)
    terminal_names, free_gates, occupied_gates = [], [], []

    for terminal in bcn_airport.terminals:
        free, occupied = 0, 0
        for area in terminal.boarding_areas:
            for gate in area.gates:
                if gate.occupied:
                    occupied += 1
                else:
                    free += 1
        terminal_names.append(terminal.name)
        free_gates.append(free)
        occupied_gates.append(occupied)

    x = list(range(len(terminal_names)))
    ax_gates.clear()
    ax_gates.bar(x, free_gates, label='Free gates', color='#2ecc71')
    ax_gates.bar(x, occupied_gates, bottom=free_gates, label='Occupied gates', color='#e74c3c')
    ax_gates.set_xticks(x)
    ax_gates.set_xticklabels(terminal_names)
    ax_gates.set_title('Gate Occupancy', color='white')
    ax_gates.set_xlabel('Terminal', color='white')
    ax_gates.set_ylabel('Number of gates', color='white')
    ax_gates.tick_params(colors='white')
    ax_gates.legend(facecolor='#1b263b', labelcolor='white')
    canvas_gates.draw()
    write("Plot d'ocupació de portes generat.")


def show_graphical_occupancy_ui():#Representació gràfica de portes (T1/T2) mostrada a la pantalla actualitzant els colors
    """Función que refresca y activa la vista visual mapeando las puertas."""
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return
    draw_schematic(canvas_t1, "T1")
    draw_schematic(canvas_t2, "T2")
    show_gates_view(graphical_view)
    write("Representació gràfica de portes (T1/T2) mostrada.")


def search_terminal_ui():#Busca i mostra a l'usuari a quina terminal pertany el codi de la companyia aèria que demani
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return
    company = simpledialog.askstring("Buscar terminal", "Codi ICAO de la companyia, per exemple VLG, RYR, IBE:")
    if not company: return
    terminal_name = lebl.SearchTerminal(bcn_airport, company.upper())
    if terminal_name == -1 or terminal_name == "":
        write("No s'ha trobat terminal per a la companyia " + company.upper())
        messagebox.showinfo("Resultat", "No s'ha trobat cap terminal.")
    else:
        write("La companyia " + company.upper() + " opera a la terminal " + terminal_name)
        messagebox.showinfo("Resultat", "Terminal: " + terminal_name)


def assign_dynamic_gates_ui():#Simula l'estat i l'assignació de l'aeroport en una hora exacta introduïda per l'usuari
    global bcn_airport, aircrafts
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return
    if len(aircrafts) == 0:
        messagebox.showwarning("Atenció", "Primer has de carregar els vols.")
        return

    # Demanem l'hora a l'usuari
    hora = simpledialog.askstring("Simulació per Hora", "Introdueix l'hora a simular (Format HH:MM):")

    # Si l'usuari cancel·la o el deixa buit, no fem res
    if not hora:
        return

    # Traiem espais en blanc que hagi pogut posar sense voler
    hora = hora.strip()

    # --- COMPROVACIÓ COMPARTIMENTADA AMB 'IF' ---

    # 1. Comprovem l'estructura bàsica (Ex: 14:30 té 5 caràcters i el colom ':' a la posició 2)
    if len(hora) != 5 or hora[2] != ':':
        messagebox.showerror("Format Incorrecte", "L'estructura ha de ser exactament de tipus HH:MM (Exemple: 14:05).")
        return

    # 2. Intentem extreure i validar les hores i els minuts
    try:
        parts = hora.split(':')
        h = int(parts[0])
        m = int(parts[1])
    except ValueError:
        # Si escriu lletres (Ex: "aa:bb"), l'int() donarà error i saltarà aquí
        messagebox.showerror("Error", "Les hores i els minuts han de ser números.")
        return

    # 3. Validem el rang de les hores
    if h < 0 or h > 23:
        messagebox.showerror("Hora Incorrecta", "L'hora ha d'estar entre 00 i 23.")
        return

    # 4. Validem el rang dels minuts
    if m < 0 or m > 59:
        messagebox.showerror("Minuts Incorrectes", "Els minuts han d'estar entre 00 i 59.")
        return

    # --- SI TOT ESTÀ BÉ, ENTRA AQUÍ ---
    unassigned = lebl.AssignGatesAtTime(bcn_airport, aircrafts, hora)
    refresh_gates_table()
    show_graphical_occupancy_ui()
    write(f"Asignació feta per les {hora}. Vols sense porta assignada: {unassigned}")
def plot_day_occupancy_ui():#Dibuixa el gràfic de línies i barres que mostra el moviment i saturació de l'aeroport durant tot el dia
    global bcn_airport, aircrafts
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return
    if len(aircrafts) == 0:
        messagebox.showwarning("Atenció", "Primer has de carregar els vols.")
        return

    # 1. Redireccionem la vista al canvas de la pestanya de portes
    show_gates_view(canvas_gates_w)
    write("Generant gràfic dinàmic de 24 hores integrat...")

    # 2. Netegem l'eix de la interfície abans de pintar
    ax_gates.clear()
    ax_gates.set_facecolor('#1b263b')

    try:
        # Intentem cridar la funció amb el tercer paràmetre (el nou codi adaptat)
        lebl.PlotDayOccupancy(bcn_airport, aircrafts, ax_gates)

    except TypeError:
        # Si dona error d'arguments és que Python està executant la versió antiga del fitxer des de la memòria cache.
        # Solució d'emergència: executem la funció clàssica de lebl saltant-nos el plt.show() extern
        import matplotlib.pyplot as plt

        # Desactivem temporalment el mode interactiu perquè plt.show() no obri la finestra emergent
        plt.ioff()

        # Cridem la funció antiga (això crearà un plot en la memòria oculta de matplotlib)
        lebl.PlotDayOccupancy(bcn_airport, aircrafts)

        # Copiem el contingut del plot que s'ha generat darrere del teló cap al nostre eix de la interfície
        fig_oculta = plt.gcf()
        for ax in fig_oculta.get_axes():
            # Si és l'eix principal o el secundari (twinx), els clonem al nostre ax_gates
            # Per evitar complicacions, simplement forcem que dibuixi directament a la interfície reactivant la versió 1:
            write("Avís: S'ha detectat el mòdul vell a la memòria cau. Si us plau, reinicia el programa.")
        plt.close(fig_oculta)
        plt.ion()
        return

    # 3. Forcem que el títol i els eixos es vegin amb l'estil correcte
    ax_gates.set_title("Dinàmica d'Ocupació - 24 Horas", color='white')
    ax_gates.tick_params(colors='white')
    ax_gates.set_xlabel('Hora', color='white')

    # 4. Actualitzem el Canvas de Tkinter
    canvas_gates.draw()


def move_or_swap_gate_ui():#Permet moure un avió d'una porta a una altra de manera manual a través de la interfície
    global bcn_airport, aircrafts
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return

    # 1. DETECTAR SELECCIÓ DE LA TAULA: Mirem què té clicat l'usuari amb el ratolí
    selected_item = tree_gates.selection()
    if not selected_item:
        messagebox.showwarning("Atenció",
                               "Si us plau, clica primer sobre una fila de la taula de portes per seleccionar el vol que vols moure.")
        return

    # Obtenim els valors de la fila clicada (la teva taula sol tenir: Porta, Terminal, Àrea, Tipus, Vol Ocupant)
    item_values = tree_gates.item(selected_item[0], 'values')
    porta_origen_nom = item_values[0].strip().upper()
    flight_id = item_values[4].strip()  # Suposant que el Flight ID és a la columna 5 (índex 4)

    # Si la porta clicada no té cap avió, no hi ha res a moure
    if not flight_id or flight_id == "" or flight_id.upper() == "LLIURE" or flight_id.upper() == "NONE":
        messagebox.showwarning("Atenció",
                               f"La porta {porta_origen_nom} està lliure. Selecciona una porta que tingui un vol assignat.")
        return

    flight_id = flight_id.upper()

    # Busquem l'objecte del Vol 1 (Origen) per validar fronteres més tard
    vol_origen = None
    for ac in aircrafts:
        if ac.id.upper() == flight_id:
            vol_origen = ac
            break

    # 2. DEMANAR LA DESTINACIÓ: Preguntem a quina porta el vol portar
    nova_porta_nom = simpledialog.askstring("Moure / Intercanviar",
                                            f"El vol {flight_id} està a la porta {porta_origen_nom}.\nA quina nova porta el vols moure?:")
    if not nova_porta_nom: return
    nova_porta_nom = nova_porta_nom.strip().upper()

    if nova_porta_nom == porta_origen_nom:
        messagebox.showwarning("Atenció", "Has triat la mateixa porta on ja es troba l'avió.")
        return

    # 3. BUSCAR PORTES I ÀREES A L'ESTRUCTURA
    porta_origen_obj = None
    area_origen_obj = None
    porta_desti_obj = None
    area_desti_obj = None

    for t in bcn_airport.terminals:
        for area in t.boarding_areas:
            for gate in area.gates:
                if gate.name.upper() == porta_origen_nom:
                    porta_origen_obj = gate
                    area_origen_obj = area
                if gate.name.upper() == nova_porta_nom:
                    porta_desti_obj = gate
                    area_desti_obj = area

    if porta_desti_obj is None:
        messagebox.showerror("Error", f"La porta de destí {nova_porta_nom} no existeix a l'aeroport.")
        return

    # Detectem si la porta de destí té un segon vol per fer l'intercanvi
    flight_id_desti = porta_desti_obj.aircraft_id.upper() if porta_desti_obj.occupied else ""
    vol_desti = None
    if flight_id_desti != "":
        for ac in aircrafts:
            if ac.id.upper() == flight_id_desti:
                vol_desti = ac
                break

    # 4. COMPROVACIONS DE SEGURETAT (SCHENGEN / NO-SCHENGEN)
    # Validem el Vol 1 (Origen) cap a l'Àrea de Destí
    es_schengen_origen = lebl.IsSchengenAirport(vol_origen.dest)
    if es_schengen_origen and area_desti_obj.type != "Schengen":
        messagebox.showerror("Error de Seguretat",
                             f"El vol {flight_id} és Schengen i no pot anar a la zona {area_desti_obj.name} ({area_desti_obj.type}).")
        return
    if not es_schengen_origen and area_desti_obj.type != "No-Schengen":
        messagebox.showerror("Error de Seguretat",
                             f"El vol {flight_id} és NO-Schengen i requereix control de passaports (Zona {area_desti_obj.type} no vàlida).")
        return

    # Si hi ha un Vol 2 (Destí), hem de validar que pugui moure's a l'Àrea d'Origen (Intercanvi creuat)
    if vol_desti is not None:
        es_schengen_desti = lebl.IsSchengenAirport(vol_desti.dest)
        if es_schengen_desti and area_origen_obj.type != "Schengen":
            messagebox.showerror("Error de Seguretat",
                                 f"Intercanvi impossible: El vol resident {flight_id_desti} és Schengen i no pot moure's a la porta {porta_origen_nom} ({area_origen_obj.type}).")
            return
        if not es_schengen_desti and area_origen_obj.type != "No-Schengen":
            messagebox.showerror("Error de Seguretat",
                                 f"Intercanvi impossible: El vol resident {flight_id_desti} és NO-Schengen i no pot passar a la porta {porta_origen_nom} ({area_origen_obj.type}).")
            return

    # 5. EXECUTAR EL MOVIMENT O INTERCANVI
    if vol_desti is None:
        # Cas A: La porta destí estava buida (Moviment simple)
        porta_origen_obj.occupied = False
        porta_origen_obj.aircraft_id = ""

        porta_desti_obj.occupied = True
        porta_desti_obj.aircraft_id = flight_id

        messagebox.showinfo("Canvi d'èxit", f"El vol {flight_id} s'ha mogut a la porta lliure {nova_porta_nom}.")
        write(f"Moviment manual: {flight_id} -> {nova_porta_nom}")
    else:
        # Cas B: La porta destí estava plena (Intercanvi de llocs / Swap)
        porta_origen_obj.aircraft_id = flight_id_desti
        porta_desti_obj.aircraft_id = flight_id

        # Ambdós queden ocupats assegurats
        porta_origen_obj.occupied = True
        porta_desti_obj.occupied = True

        messagebox.showinfo("Intercanvi d'èxit",
                            f"S'han intercanviat els avions:\n- Vol {flight_id} ara a la porta {nova_porta_nom}\n- Vol {flight_id_desti} ara a la porta {porta_origen_nom}")
        write(f"Intercanvi manual creuat: [{flight_id} <-> {flight_id_desti}]")

    # 6. ACTUALITZAR INTERFÍCIE
    refresh_gates_table()
    show_graphical_occupancy_ui()
# POBLACIÓ DEL PANEL LATERAL GLOBAL (TODOS LOS BOTONES A LA IZQUIERDA)

def clear_all_gates_ui(): #Allibera totes les portes que estan ocupades i queden totes lliures un altre cop
    global bcn_airport
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return

    if not messagebox.askyesno("Confirmar", "Vols alliberar totes les portes de l'aeroport?"):
        return

    count = 0
    for terminal in bcn_airport.terminals:
        for area in terminal.boarding_areas:
            for gate in area.gates:
                if gate.occupied:
                    gate.occupied = False
                    gate.aircraft_id = ""
                    count += 1

    refresh_gates_table()
    update_simulation_stats(0)
    show_graphical_occupancy_ui()

    write(f"S'han alliberat totes les portes ({count} portes buidades).")
    messagebox.showinfo("Èxit", f"S'han alliberat correctament {count} portes.")

def simulate_full_day_ui(): #Aquesta funció crea una simulació de les arribades i les sortides durant el dia, a mesura que pasa el temps es van ocupant i desocupant les portes
    global bcn_airport, aircrafts, simulation_running
    if simulation_running:
        messagebox.showinfo("Simulació","Ja hi ha una simulació en marxa.")
        return
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning(
            "Atenció",
            "Primer has de carregar l'estructura de l'aeroport."
        )
        return

    if len(aircrafts) == 0:
        messagebox.showwarning(
            "Atenció",
            "Primer has de carregar els vols."
        )
        return

    simulation_running = True

    write("=== INICIANT SIMULACIÓ COMPLETA DEL DIA ===")

    simulacio = []

    for ac in aircrafts:
        try:
            h, m = map(int, ac.time.split(":"))
            minuts_arribada = h * 60 + m

            # Estada simulada de 90 minuts
            minuts_sortida = minuts_arribada + 90

            simulacio.append(
                (minuts_arribada, "ARRIVAL", ac)
            )

            simulacio.append(
                (minuts_sortida, "DEPARTURE", ac)
            )

        except:
            pass

    simulacio.sort(key=lambda x: x[0])

    index = 0

    def step(): #S'encarrega d'avançar en el temps per poder mostrar la simulació
        global simulation_running
        global LAST_GATE_CHANGED
        if not simulation_running:
            write("=== SIMULACIÓ ATURADA MANUALMENT ===")
            return

        nonlocal index

        if index >= len(simulacio):
            simulation_running = False
            LAST_GATE_CHANGED = None
            write("=== FI DE LA SIMULACIÓ ===")
            refresh_gates_table()
            show_graphical_occupancy_ui()
            occupancy = lebl.GateOccupancy(bcn_airport)

            total = len(occupancy)

            occupied = sum(
                1 for x in occupancy
                if x[3]
            )

            write("")
            write("===== RESUM FINAL =====")
            write(f"Portes totals: {total}")
            write(f"Portes ocupades: {occupied}")
            write(f"Portes lliures: {total - occupied}")
            write("=======================")
            return

        temps, tipus, ac = simulacio[index]

        hora = f"{temps//60:02d}:{temps%60:02d}"

        if tipus == "ARRIVAL":

            gate = lebl.AssignGate(bcn_airport, ac)

            if gate != -1:



                LAST_GATE_CHANGED = gate

                write(f"[{hora}] ARRIBA {ac.id} -> Porta {gate}")
            else:
                write(
                    f"[{hora}] ARRIBA {ac.id} -> SENSE PORTA"
                )

        else:

            for terminal in bcn_airport.terminals:
                for area in terminal.boarding_areas:
                    for gate in area.gates:

                        if (
                            gate.occupied
                            and gate.aircraft_id == ac.id
                        ):
                            gate.occupied = False
                            gate.aircraft_id = ""
                            LAST_GATE_CHANGED = gate.name
                            write(
                                f"[{hora}] SURT {ac.id} "
                                f"(allibera {gate.name})"
                            )
        update_simulation_stats(temps)

        sim_progress["value"] = (temps / 1440) * 100
        refresh_gates_table()
        draw_schematic(canvas_t1, "T1")
        draw_schematic(canvas_t2, "T2")

        index += 1

        root.after(100, step)

    step()

def stop_simulation_ui(): #Atura la simulació

    global simulation_running

    simulation_running = False

    write("Ordre d'aturada enviada.")

# --- Sección: AEROPORTS ---
tk.Label(sidebar, text="✈️ AEROPORTS", bg=BG, fg="#10b981", font=('Segoe UI', 12, 'bold')).pack(pady=(7, 2))
ttk.Button(sidebar, text="Carregar Fitxer", command=load_airports_file).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Afegir Aeroport", command=add_airport_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Eliminar Aeroport", command=remove_airport_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Plot Schengen", command=draw_airport_plot).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Mapa Aeroports", command=map_airports).pack(fill='x', pady=2)
ttk.Button(sidebar, text="INFO", command=lambda: show_ap_view(tree_ap)).pack(fill='x', pady=(2, 4))

# --- Sección: VOLS ---
tk.Label(sidebar, text="🌍 VOLS", bg=BG, fg="#3b82f6", font=('Segoe UI', 12, 'bold')).pack(pady=(4, 2))
ttk.Button(sidebar, text="Carregar Arribades", command=load_flights_file).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Carregar Sortides", command=load_departures_file).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Afegir Vol", command=add_flight_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Plot Arribades", command=draw_arrivals_plot).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Plot Companyies", command=draw_airlines_plot).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Plot Schengen", command=draw_types_plot).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Mapa Vols", command=map_flights).pack(fill='x', pady=2)
ttk.Button(sidebar, text="INFO", command=lambda: show_fv_view(tree_fv)).pack(fill='x', pady=(2, 4))

# --- Sección: PORTES ---
tk.Label(sidebar, text="🚪 PORTES", bg=BG, fg="#f59e0b", font=('Segoe UI', 12, 'bold')).pack(pady=(4, 2))
ttk.Button(sidebar, text="Carregar Estructura Aeroport", command=load_airport_structure_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Assignar Portes als Vols", command=assign_gates_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Asignar per Hora", command=assign_dynamic_gates_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Alliberar Totes les Portes", command=clear_all_gates_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Vista Gràfica (T1/T2)", command=show_graphical_occupancy_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Mostrar Ocupació Terminals", command=show_gate_occupancy_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Plot Ocupació Portes", command=plot_gate_occupancy_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Gràfic Ocupació 24H", command=plot_day_occupancy_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Simular Dia Aeroport",command=simulate_full_day_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Aturar Simulació",command=stop_simulation_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Aerolinia en Terminal", command=search_terminal_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="Moure Assignacions", command=move_or_swap_gate_ui).pack(fill='x', pady=2)
ttk.Button(sidebar, text="INFO Portes", command=lambda: show_gates_view(tree_gates)).pack(fill='x', pady=2)

def setup_initial_state():#Mostra el missatge de benvinguda i recordatori a la pantalla abans que comencin les simulacions.
    canvas_t1.create_text(200, 200, text="Per favor, carrega l'estructura de l'aeroport per veure el mapa.",
                          fill="gray", font=('Segoe UI', 14))
    canvas_t2.create_text(200, 200, text="Per favor, carrega l'estructura de l'aeroport per veure el mapa.",
                          fill="gray", font=('Segoe UI', 14))


setup_initial_state()
root.mainloop()
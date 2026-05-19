import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import importlib.util, os, subprocess, sys
import math

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ===== CÀRREGA DE MÒDULS =====
BASE = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Carreguem els teus mòduls originals
airport = load_module('versio1.py', 'airport_mod')
flights = load_module('versio2.py', 'flights_mod')
lebl = load_module('LEBL.py', 'lebl_mod')

airports = []
aircrafts = []
bcn_airport = None


# ===== FUNCIONS DE SUPORT =====
def open_google_earth(path):
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
                # fallback (com abans)
                os.startfile(absf)

        elif sys.platform == 'darwin':
            subprocess.Popen(['open', absf])
        else:
            subprocess.Popen(['xdg-open', absf])

    except Exception as e:
        print("Error obrint Google Earth:", e)


# ===== INTERFÍCIE PRINCIPAL =====
root = tk.Tk()
root.title('Air Traffic Manager Pro - Versió Final Integrada')
root.geometry('1400x900')
root.configure(bg='#101826')

style = ttk.Style()
style.theme_use('clam')
style.configure('.', background='#101826', foreground='white', fieldbackground='#1b263b')
style.configure('Treeview', background='#1b263b', foreground='white', rowheight=30)
style.configure('TButton', font=('Helvetica', 9, 'bold'))

nb = ttk.Notebook(root)
nb.pack(fill='both', expand=True, padx=10, pady=10)

fa = ttk.Frame(nb)
fv = ttk.Frame(nb)
fg = ttk.Frame(nb)

nb.add(fa, text=' Aeroports ')
nb.add(fv, text=' Vols ')
nb.add(fg, text=' Portes ')

log = ScrolledText(root, height=8, bg='#0b1320', fg='#00ff00', font=('Consolas', 10))
log.pack(fill='x', padx=10, pady=(0, 10))


def write(msg):
    log.insert('end', f">>> {msg}\n")
    log.see('end')


# =========================================================================
# PESTANYA 1: AEROPORTS
# =========================================================================
la = ttk.Frame(fa);
la.pack(side='left', fill='y', padx=10, pady=10)
ra = ttk.Frame(fa);
ra.pack(side='right', fill='both', expand=True, padx=10, pady=10)

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
                       fg='white', bg='#1b263b', font=('Arial', 14))
map_info_ap.pack(pady=100)

all_ap_w = [tree_ap, canvas_ap_w, map_view_ap]


def show_ap_view(target):
    for w in all_ap_w: w.pack_forget()
    target.pack(fill='both', expand=True)


def load_airports_file():
    global airports
    fn = filedialog.askopenfilename()
    if fn:
        airports = airport.LoadAirports(fn)
        refresh_ap_table()
        write(f"Aeroports carregats correctament.")
        show_ap_view(tree_ap)


def refresh_ap_table():
    for i in tree_ap.get_children(): tree_ap.delete(i)
    for a in airports:
        tree_ap.insert('', 'end', values=(a.code, round(a.lat, 4), round(a.lon, 4), "Sí" if a.schengen else "No"))


# NOVES FUNCIONS D'EDICIÓ D'AEROPORTS
def add_airport_ui():
    code = simpledialog.askstring("Nou Aeroport", "Codi ICAO (Ex: LEBL):")
    if not code: return
    try:
        lat_str = simpledialog.askstring("Latitud", "Format: N411749 o decimal (41.29):")
        lon_str = simpledialog.askstring("Longitud", "Format: E0020459 o decimal (2.08):")
        if not lat_str or not lon_str: return

        # Si conté lletres de direcció, usem convert_coord de la versió 1
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


def remove_airport_ui():
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


def draw_airport_plot():
    if not airports: return
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


def map_airports():
    airport.MapAirports(airports)
    write('Mapa aeroports creat. Obrint a Google Earth...')
    open_google_earth('airports.kml')


# Botons Esquerra Aeroports (ACTUALITZATS)
ttk.Button(la, text="Carregar Fitxer", command=load_airports_file).pack(fill='x', pady=3)
ttk.Button(la, text="Afegir Aeroport", command=add_airport_ui).pack(fill='x', pady=3)
ttk.Button(la, text="Eliminar Aeroport", command=remove_airport_ui).pack(fill='x', pady=3)
ttk.Button(la, text="Plot Aeroports", command=draw_airport_plot).pack(fill='x', pady=3)
ttk.Button(la, text="Mapa KML", command=map_airports).pack(fill='x', pady=3)
ttk.Button(la, text="INFO (Dades)", command=lambda: show_ap_view(tree_ap)).pack(fill='x', pady=20)

# =========================================================================
# PESTANYA 2: VOLS
# =========================================================================
lv = ttk.Frame(fv);
lv.pack(side='left', fill='y', padx=10, pady=10)
rv = ttk.Frame(fv);
rv.pack(side='right', fill='both', expand=True, padx=10, pady=10)

tree_fv = ttk.Treeview(rv, columns=('id', 'origin', 'time', 'company'), show='headings')
for c in ('id', 'origin', 'time', 'company'):
    tree_fv.heading(c, text=c.upper())
    tree_fv.column(c, anchor='center')

fig_fv = Figure(figsize=(6, 5), facecolor='#1b263b')
ax_fv = fig_fv.add_subplot(111);
ax_fv.set_facecolor('#1b263b')
canvas_fv = FigureCanvasTkAgg(fig_fv, master=rv)
canvas_fv_w = canvas_fv.get_tk_widget()

map_view_fv = tk.Frame(rv, bg='#1b263b')
map_info_fv = tk.Label(map_view_fv,
                       text="🌍 VISTA DE MAPA DE VOLS ACTIVA\n\nTrajectòries calculades. Comprovant distàncies > 2000km.",
                       fg='white', bg='#1b263b', font=('Arial', 14))
map_info_fv.pack(pady=100)

all_fv_w = [tree_fv, canvas_fv_w, map_view_fv]


def show_fv_view(target):
    for w in all_fv_w: w.pack_forget()
    target.pack(fill='both', expand=True)


def load_flights_file():
    global aircrafts
    fn = filedialog.askopenfilename()
    if fn:
        aircrafts = flights.LoadArrivals(fn)
        refresh_fv_table()
        write(f"Vols carregats correctament.")
        show_fv_view(tree_fv)


def refresh_fv_table():
    for i in tree_fv.get_children(): tree_fv.delete(i)
    for p in aircrafts:
        tree_fv.insert('', 'end', values=(p.id, p.origin, p.time, p.company))


# NOVA FUNCIÓ D'AFEGIR VOL
def add_flight_ui():
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


def draw_arrivals_plot():
    if not aircrafts: return
    show_fv_view(canvas_fv_w)
    hours = [0] * 24
    for p in aircrafts:
        try:
            h = int(p.time.split(':')[0]); hours[h] += 1
        except:
            pass
    ax_fv.clear()
    ax_fv.bar(range(24), hours, color='#3498db')
    ax_fv.set_title('Arribades per Hora', color='white')
    ax_fv.tick_params(colors='white')
    canvas_fv.draw()


def draw_airlines_plot():
    if not aircrafts: return
    all_comps = sorted(list(set(a.company for a in aircrafts)))
    top = tk.Toplevel(root)
    lb = tk.Listbox(top, selectmode='multiple', height=15)
    lb.pack(padx=10, pady=10, fill='both', expand=True)
    for c in all_comps: lb.insert('end', c)

    def apply():
        sel = [lb.get(i) for i in lb.curselection()]
        if not sel: return
        show_fv_view(canvas_fv_w)
        d = {c: sum(1 for a in aircrafts if a.company == c) for c in sel}
        ax_fv.clear();
        ax_fv.bar(d.keys(), d.values(), color='#9b59b6')
        ax_fv.tick_params(colors='white', rotation=45)
        canvas_fv.draw();
        top.destroy()

    ttk.Button(top, text="Dibuixar", command=apply).pack()


def draw_types_plot():
    if not aircrafts: return
    show_fv_view(canvas_fv_w)
    # Useu la lògica de prefixes de la versio2
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


def map_flights():
    # 1. Generem el KML base usant el teu mòdul
    flights.MapFlights(aircrafts, airports)

    # Ruta on el teu versio2.py realment guarda el fitxer
    ruta_kml = '../projecte/flights.kml'

    try:
        if os.path.exists(ruta_kml):
            with open(ruta_kml, 'r', encoding='utf-8') as f:
                contingut = f.read()

            LEBL_COORDS = (41.2974, 2.0833)

            for a in aircrafts:
                # Busquem si l'aeroport d'origen és a la nostra llista
                origin_ap = next((ap for ap in airports if ap.code == a.origin), None)

                # CONDICIÓ: No-Schengen I distància > 2000km
                if origin_ap and not origin_ap.schengen:
                    dist = flights.distancia((origin_ap.lat, origin_ap.lon), LEBL_COORDS)

                    if dist > 2000:
                        search_pattern = f"<name>{a.id} from {a.origin}</name>"
                        if search_pattern in contingut:
                            # Tallem el fitxer per trobar el bloc d'aquest vol
                            parts = contingut.split(search_pattern)
                            if len(parts) > 1:
                                # El codi ffff0000 és el BLAU pur en format KML (ABGR)
                                parts[1] = parts[1].replace("<color>ff00ff00</color>", "<color>ffff0000</color>", 1)
                                parts[1] = parts[1].replace("<color>ff0000ff</color>", "<color>ffff0000</color>", 1)
                                contingut = search_pattern.join(parts)

            # Forcem que la línia segueixi la corba de la terra
            if '<tessellate>1</tessellate>' not in contingut:
                contingut = contingut.replace('<LineString>', '<LineString>\n<tessellate>1</tessellate>')

            with open(ruta_kml, 'w', encoding='utf-8') as f:
                f.write(contingut)

            write('Vols No-Schengen > 2000km pintats de blau.')
        else:
            write(f"Error: No s'ha trobat el fitxer a {ruta_kml}")

    except Exception as e:
        write(f"Error en el processat: {e}")

    # 2. Cridem a la teva funció d'obrir Google Earth
    open_google_earth(ruta_kml)


# Botons Esquerra Vols (ACTUALITZATS)
ttk.Button(lv, text="Carregar Arribades", command=load_flights_file).pack(fill='x', pady=3)
ttk.Button(lv, text="Afegir Vol", command=add_flight_ui).pack(fill='x', pady=3)
ttk.Button(lv, text="Plot Arribades", command=draw_arrivals_plot).pack(fill='x', pady=3)
ttk.Button(lv, text="Plot Companyies", command=draw_airlines_plot).pack(fill='x', pady=3)
ttk.Button(lv, text="Plot Tipus", command=draw_types_plot).pack(fill='x', pady=3)
ttk.Button(lv, text="Mapa Vols", command=map_flights).pack(fill='x', pady=3)
ttk.Button(lv, text="INFO (Dades)", command=lambda: show_fv_view(tree_fv)).pack(fill='x', pady=20)

# =========================================================================
# PESTANYA 3: PORTES / GATES
# =========================================================================

lg = ttk.Frame(fg)
lg.pack(side='left', fill='y', padx=10, pady=10)

rg = ttk.Frame(fg)
rg.pack(side='right', fill='both', expand=True, padx=10, pady=10)

tree_gates = ttk.Treeview(
    rg,
    columns=('terminal', 'area', 'gate', 'status', 'aircraft'),
    show='headings'
)

for c in ('terminal', 'area', 'gate', 'status', 'aircraft'):
    tree_gates.heading(c, text=c.upper())
    tree_gates.column(c, anchor='center')

fig_gates = Figure(figsize=(6, 5), facecolor='#1b263b')
ax_gates = fig_gates.add_subplot(111)
ax_gates.set_facecolor('#1b263b')

canvas_gates = FigureCanvasTkAgg(fig_gates, master=rg)
canvas_gates_w = canvas_gates.get_tk_widget()

all_gates_w = [tree_gates, canvas_gates_w]


def show_gates_view(target):
    for w in all_gates_w:
        w.pack_forget()

    target.pack(fill='both', expand=True)


def load_airport_structure_ui():
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
            show_gates_view(tree_gates)


def refresh_gates_table():
    for i in tree_gates.get_children():
        tree_gates.delete(i)

    if bcn_airport is None or bcn_airport == -1:
        return

    occupancy = lebl.GateOccupancy(bcn_airport)

    if occupancy == -1:
        write("Error obtenint l'ocupació de portes.")
        return

    for item in occupancy:
        terminal = item[0]
        area = item[1]
        gate = item[2]
        occupied = item[3]
        aircraft_id = item[4]

        if occupied:
            status = "Occupied"
        else:
            status = "Free"

        tree_gates.insert(
            '',
            'end',
            values=(terminal, area, gate, status, aircraft_id)
        )


def assign_gates_ui():
    global bcn_airport
    global aircrafts

    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return

    if len(aircrafts) == 0:
        messagebox.showwarning("Atenció", "Primer has de carregar els vols.")
        return

    assigned = 0
    not_assigned = 0

    for aircraft in aircrafts:
        gate_name = lebl.AssignGate(bcn_airport, aircraft)

        if gate_name == -1:
            write("No s'ha pogut assignar porta al vol " + aircraft.id)
            not_assigned = not_assigned + 1
        else:
            write("Vol " + aircraft.id + " assignat a la porta " + gate_name)
            assigned = assigned + 1

    refresh_gates_table()
    show_gates_view(tree_gates)

    write("Assignació acabada. Assignats: " + str(assigned) + ", no assignats: " + str(not_assigned))


def show_gate_occupancy_ui():
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return

    refresh_gates_table()
    show_gates_view(tree_gates)
    write("Ocupació de portes mostrada a la taula.")


def plot_gate_occupancy_ui():
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return

    show_gates_view(canvas_gates_w)

    terminal_names = []
    free_gates = []
    occupied_gates = []

    for terminal in bcn_airport.terminals:
        free = 0
        occupied = 0

        for area in terminal.boarding_areas:
            for gate in area.gates:
                if gate.occupied:
                    occupied = occupied + 1
                else:
                    free = free + 1

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


def search_terminal_ui():
    if bcn_airport is None or bcn_airport == -1:
        messagebox.showwarning("Atenció", "Primer has de carregar l'estructura de l'aeroport.")
        return

    company = simpledialog.askstring("Buscar terminal", "Codi ICAO de la companyia, per exemple VLG, RYR, IBE:")

    if not company:
        return

    terminal_name = lebl.SearchTerminal(bcn_airport, company.upper())

    if terminal_name == -1 or terminal_name == "":
        write("No s'ha trobat terminal per a la companyia " + company.upper())
        messagebox.showinfo("Resultat", "No s'ha trobat cap terminal.")
    else:
        write("La companyia " + company.upper() + " opera a la terminal " + terminal_name)
        messagebox.showinfo("Resultat", "Terminal: " + terminal_name)


ttk.Button(lg, text="Carregar Estructura LEBL", command=load_airport_structure_ui).pack(fill='x', pady=3)
ttk.Button(lg, text="Assignar Portes als Vols", command=assign_gates_ui).pack(fill='x', pady=3)
ttk.Button(lg, text="Mostrar Ocupació", command=show_gate_occupancy_ui).pack(fill='x', pady=3)
ttk.Button(lg, text="Plot Ocupació Portes", command=plot_gate_occupancy_ui).pack(fill='x', pady=3)
ttk.Button(lg, text="Buscar Terminal Companyia", command=search_terminal_ui).pack(fill='x', pady=3)
ttk.Button(lg, text="INFO Portes", command=lambda: show_gates_view(tree_gates)).pack(fill='x', pady=20)


root.mainloop()
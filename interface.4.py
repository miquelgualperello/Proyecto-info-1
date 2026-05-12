import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import importlib.util, os, subprocess, sys

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ===== Load modules =====
BASE = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()

def load_module(path,name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE,path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

airport = load_module('versio1.py', 'airport_mod')
flights = load_module('versio2.py', 'flights_mod')

airports=[]
aircrafts=[]

# ===== Google Earth  =====
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

# ===== UI =====
root=tk.Tk()
root.title('Air Traffic Manager Pro')
root.geometry('1280x780')
root.configure(bg='#101826')

style=ttk.Style(); style.theme_use('clam')
style.configure('.', background='#101826', foreground='white', fieldbackground='#1b263b')
style.configure('Treeview', background='#1b263b', foreground='white', rowheight=28)

nb=ttk.Notebook(root); nb.pack(fill='both', expand=True, padx=10,pady=10)
fa=ttk.Frame(nb); fv=ttk.Frame(nb)
nb.add(fa,text='Aeroports'); nb.add(fv,text='Vols')

log=ScrolledText(root,height=6,bg='#0b1320',fg='white'); log.pack(fill='x',padx=10,pady=(0,10))
def write(msg): log.insert('end',msg+'\n'); log.see('end')

# ===== AEROPORTS =====
la=ttk.Frame(fa); la.pack(side='left',fill='y',padx=8,pady=8)
ra=ttk.Frame(fa); ra.pack(side='right',fill='both',expand=True,padx=8,pady=8)

cols=('code','lat','lon','schengen')
tree=ttk.Treeview(ra,columns=cols,show='headings')
for c in cols: tree.heading(c,text=c.upper()); tree.column(c,width=120)
tree.pack(side='top',fill='x')

# Plot area airports
fig_ap = Figure(figsize=(5,4))
ax_ap = fig_ap.add_subplot(111)
canvas_ap = FigureCanvasTkAgg(fig_ap, master=ra)
canvas_ap.get_tk_widget().pack(fill='both', expand=True)

def draw_airport_plot():
    if not airports: return
    sch=0
    for a in airports:
        if a.schengen: sch+=1
    non=len(airports)-sch
    ax_ap.clear()
    ax_ap.bar(['Aeroports'], [sch], label='Schengen')
    ax_ap.bar(['Aeroports'], [non], bottom=[sch], label='No Schengen')
    ax_ap.legend()
    ax_ap.set_title('Distribució Aeroports')
    canvas_ap.draw()

# Logic functions

def refresh_airports():
    for i in tree.get_children(): tree.delete(i)
    for idx,a in enumerate(airports):
        tree.insert('', 'end', iid=str(idx), values=(a.code, round(a.lat,3), round(a.lon,3), 'Sí' if a.schengen else 'No'))

def load_airports_file():
    global airports
    fn=filedialog.askopenfilename()
    if fn:
        airports=airport.LoadAirports(fn)
        refresh_airports(); write(f'Aeroports: {len(airports)}')

def add_airport_manual():
    code=simpledialog.askstring('Codi','ICAO:')
    lat=simpledialog.askfloat('Lat','Lat:')
    lon=simpledialog.askfloat('Lon','Lon:')
    if code and lat!=None and lon!=None:
        a=airport.Airport(code,lat,lon)
        airport.SetSchengen(a)
        airport.AddAirport(airports,a)
        refresh_airports(); write('Afegit')
def remove_airport_ui():
    code = simpledialog.askstring('Eliminar', 'Codi ICAO de l\'aeroport a eliminar:')
    if code:
        res = airport.RemoveAirport(airports, code.upper())
        if res != -1:
            refresh_airports()
            write(f'Aeroport {code} eliminat.')
        else:
            messagebox.showwarning("Error", "No s'ha trobat l'aeroport.")
def map_airports():
    airport.MapAirports(airports)
    write('Mapa aeroports creat. Obrint a Google Earth...')
    open_google_earth('airports.kml')

for t,cmd in [
    ('Carregar Fitxer', load_airports_file),
    ('Afegir Aeroport', add_airport_manual),
    ('Eliminar Aeroport', remove_airport_ui),
    ('Plot Aeroports', draw_airport_plot),
    ('Mapa KML', map_airports)
]:
    ttk.Button(la, text=t, command=cmd).pack(fill='x', pady=4)

# ===== VOLS =====
lv=ttk.Frame(fv); lv.pack(side='left',fill='y',padx=8,pady=8)
rv=ttk.Frame(fv); rv.pack(side='right',fill='both',expand=True,padx=8,pady=8)

cols2=('id','origin','time','company')
tree2=ttk.Treeview(rv,columns=cols2,show='headings')
for c in cols2: tree2.heading(c,text=c.upper()); tree2.column(c,width=120)
tree2.pack(side='top',fill='x')

# Plot area flights
fig_fl = Figure(figsize=(5,4))
ax_fl = fig_fl.add_subplot(111)
canvas_fl = FigureCanvasTkAgg(fig_fl, master=rv)
canvas_fl.get_tk_widget().pack(fill='both', expand=True)

# Plot functions

def draw_arrivals():
    hours=[0]*24
    for p in aircrafts:
        try: h=int(p.time.split(':')[0]); hours[h]+=1
        except: pass
    ax_fl.clear()
    ax_fl.bar(range(24),hours)
    ax_fl.set_title('Arribades per hora')
    canvas_fl.draw()


def draw_airlines():
    if not aircrafts: return
    all_companies = sorted(list(set(a.company for a in aircrafts)))

    top = tk.Toplevel(root)
    top.title("Selecciona Companyies")
    lb = tk.Listbox(top, selectmode='multiple', exportselection=0, height=15)
    lb.pack(padx=10, pady=10, fill='both', expand=True)
    for c in all_companies: lb.insert('end', c)

    def apply_filter():
        selected_indices = lb.curselection()
        if not selected_indices: return
        selected_companies = [lb.get(i) for i in selected_indices]
        d = {}
        for a in aircrafts:
            if a.company in selected_companies:
                d[a.company] = d.get(a.company, 0) + 1

        ax_fl.clear()
        ax_fl.bar(d.keys(), d.values(), color='#3498db')
        ax_fl.set_title('Vols per Companyia (Filtrat)')
        canvas_fl.draw()
        top.destroy()

    ttk.Button(top, text="Dibuixar Plot", command=apply_filter).pack(pady=5)

def draw_types():
    sch=0; non=0
    for a in aircrafts:
        if a.origin[:2] in ['LE','LF','ED','EH','LS']: sch+=1
        else: non+=1
    ax_fl.clear()
    ax_fl.bar(['Vols'],[sch],label='Schengen')
    ax_fl.bar(['Vols'],[non],bottom=[sch],label='No')
    ax_fl.legend()
    canvas_fl.draw()

# Logic

def refresh_flights():
    for i in tree2.get_children(): tree2.delete(i)
    for idx,p in enumerate(aircrafts):
        tree2.insert('', 'end', iid=str(idx), values=(p.id,p.origin,p.time,p.company))

def load_flights_file():
    global aircrafts
    fn=filedialog.askopenfilename()
    if fn:
        aircrafts=flights.LoadArrivals(fn)
        refresh_flights(); write(f'Vols: {len(aircrafts)}')

def add_flight_manual():
    fid=simpledialog.askstring('ID','ID:')
    org=simpledialog.askstring('Origen','Origen:')
    tm=simpledialog.askstring('Hora','HH:MM:')
    comp=simpledialog.askstring('Companyia','Airline:')
    if fid and org and tm and comp:
        aircrafts.append(flights.Aircraft(fid,org,tm,comp))
        refresh_flights(); write('Vol afegit')


def map_flights():
    flights.MapFlights(aircrafts, airports)

    try:
        if os.path.exists('flights.kml'):
            with open('flights.kml', 'r', encoding='utf-8') as f:
                contingut = f.read()

            LEBL_COORDS = (41.2974, 2.0833)

            for a in aircrafts:
                origin_ap = next((ap for ap in airports if ap.code == a.origin), None)

                if origin_ap:
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

            with open('flights.kml', 'w', encoding='utf-8') as f:
                f.write(contingut)

            write('Aplicant color blau a vols de llarga distància (>2000km)...')

    except Exception as e:
        write(f"Avís: error en el processat del color: {e}")

    write('Mapa vols creat. Obrint a Google Earth...')
    open_google_earth('flights.kml')


for t,cmd in [
('Carregar Arribades',load_flights_file),
('Afegir Vol individual',add_flight_manual),
('Plot Arribades',draw_arrivals),
('Plot Companyies',draw_airlines),
('Plot Tipus',draw_types),
('Mapa Vols',map_flights)
]:
    ttk.Button(lv,text=t,command=cmd).pack(fill='x',pady=4)

root.mainloop()

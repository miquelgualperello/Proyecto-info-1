import os
import matplotlib.pyplot as plt

class Gate:
    def __init__(self, name):
        self.name = name
        self.occupied = False
        self.aircraft_id = ""

class BoardingArea:
    def __init__(self, name, area_type):
        self.name = name
        self.type = area_type
        self.gates = []

class Terminal:
    def __init__(self, name):
        self.name = name
        self.boarding_areas = []
        self.airlines = []

class BarcelonaAP:
    def __init__(self, code):
        self.code = code
        self.terminals = []

def IsSchengenAirport(code): #Comprova si el prefix del codi de l'aeroport passat pertany a un país de l'espai Schengen
    if code == "":
        return False
    schengen_prefixes = [
        'LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG',
        'EH', 'LH', 'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP',
        'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS'
    ]
    if len(code) < 2: return False
    if code[0:2] in schengen_prefixes: return True
    return False

def SetGates(area, init_gate, end_gate, prefix): # Crea i afegeix un rang de portes d'embarcament consecutives amb un prefix a una zona determinada
    if end_gate < init_gate:
        return -1
    area.gates = []
    i = init_gate
    while i <= end_gate:
        gate_name = prefix + str(i)
        gate = Gate(gate_name)
        area.gates.append(gate)
        i = i + 1
    return 0

def LoadAirlines(terminal, terminal_name, base_folder): #Obre el fitxer de text de les aerolínies d'una terminal i en carrega els codis a la seva llista
    filename = terminal_name + "_Airlines.txt"
    path = os.path.join(base_folder, filename)
    try:
        f = open(path, "r", encoding="utf-8")
    except:
        return -1
    terminal.airlines = []
    for line in f:
        line = line.strip()
        if line != "":
            parts = line.split()
            if len(parts) >= 2:
                icao = parts[-1]
                terminal.airlines.append(icao.upper())
    f.close()
    return 0

def LoadAirportStructure(filename):#Llegeix un fitxer de configuració de text per construir tota l'estructura de terminals, zones, portes i companyies de l'aeroport
    try:
        f = open(filename, "r", encoding="utf-8")
    except:
        return -1
    lines = f.readlines()
    f.close()
    if len(lines) == 0: return -1

    base_folder = os.path.dirname(filename)
    first_line = lines[0].split()
    if len(first_line) < 2: return -1

    airport_code = first_line[0]
    num_terminals = int(first_line[1])
    airport = BarcelonaAP(airport_code)

    i = 1
    t = 0
    while t < num_terminals:
        while i < len(lines) and lines[i].strip() == "": i = i + 1
        if i >= len(lines): return -1
        terminal_line = lines[i].split()
        if len(terminal_line) < 3: return -1
        terminal_name = terminal_line[1]
        num_areas = int(terminal_line[2])
        terminal = Terminal(terminal_name)

        i = i + 1
        a = 0
        while a < num_areas:
            while i < len(lines) and lines[i].strip() == "": i = i + 1
            if i >= len(lines): return -1
            area_line = lines[i].split()
            if len(area_line) < 7: return -1
            
            area_letter = area_line[1]
            area_type = area_line[2]
            init_gate = int(area_line[4])
            end_gate = int(area_line[6])

            area_name = terminal_name + "BA" + area_letter.lower()
            area = BoardingArea(area_name, area_type)
            prefix = area_name + "G"
            result = SetGates(area, init_gate, end_gate, prefix)
            if result == -1: return -1
            terminal.boarding_areas.append(area)

            i = i + 1
            a = a + 1

        result = LoadAirlines(terminal, terminal_name, base_folder)
        if result == -1: return -1
        airport.terminals.append(terminal)
        t = t + 1
    return airport

def GateOccupancy(bcn):#Genera una llista matriu amb l'estat d'ocupació, codi d'avió i ubicació de totes les portes de l'aeroport
    if bcn is None: return -1
    occupancy_list = []
    for terminal in bcn.terminals:
        for area in terminal.boarding_areas:
            for gate in area.gates:
                info = [terminal.name, area.name, gate.name, gate.occupied, gate.aircraft_id]
                occupancy_list.append(info)
    return occupancy_list

def IsAirlineInTerminal(terminal, airline_code):#Verifica de forma lògica si una companyia aèria concreta opera dins d'una terminal determinada
    if airline_code == "": return False
    if airline_code.upper() in terminal.airlines: return True
    return False

def SearchTerminal(bcn, airline_code):#Recorre l'aeroport per trobar el nom de la terminal que té assignada una aerolínia específica
    if bcn is None: return ""
    airline_code = airline_code.upper()
    for terminal in bcn.terminals:
        if IsAirlineInTerminal(terminal, airline_code):
            return terminal.name
    return ""

def AssignGate(bcn, aircraft):#Reserva una porta lliure en la zona adequada de la terminal assignada a la companyia de l'avió.
    if bcn is None: return -1
    terminal_name = SearchTerminal(bcn, aircraft.company)
    if terminal_name == "": return -1

    # els avions de nit tenen desti els avions normal tenen origen.
    if aircraft.origin and aircraft.origin != "":
        origin_is_schengen = IsSchengenAirport(aircraft.origin)
    else:
        origin_is_schengen = IsSchengenAirport(aircraft.destination)

    for terminal in bcn.terminals:
        if terminal.name == terminal_name:
            for area in terminal.boarding_areas:
                correct_area = False
                if origin_is_schengen == True and area.type == "Schengen": correct_area = True
                if origin_is_schengen == False and area.type == "non-Schengen": correct_area = True

                if correct_area == True:
                    for gate in area.gates:
                        if gate.occupied == False:
                            gate.occupied = True
                            gate.aircraft_id = aircraft.id
                            return gate.name
    return -1

def AssignNightGates(bcn, aircrafts):#Identifica i assigna portes des de l'inici de la simulació als avions nocturns que inicien el dia aparcats
    if bcn is None or not aircrafts: return -1
    for a in aircrafts:
        # Night aircrafts: no arrival time, only departure time
        if (a.time == "" or a.time is None) and a.time_departure != "":
            AssignGate(bcn, a)
    return 0

def FreeGate(bcn, id):#Busca un avió pel seu codi identificador a les portes de l'aeroport i la torna a deixar buida i disponible
    if bcn is None: return -1
    for t in bcn.terminals:
        for a in t.boarding_areas:
            for g in a.gates:
                if g.occupied and g.aircraft_id == id:
                    g.occupied = False
                    g.aircraft_id = ""
                    return 0
    return -1

def AssignGatesAtTime(bcn, aircrafts, time_str):# Allibera les portes dels vols que ja han enlairat i assigna lloc als nous vols que arriben a una hora concreta
    if bcn is None or not aircrafts: return -1
    try:
        current_hour = int(time_str.split(':')[0])
    except:
        return -1

    # 1. Free gates for aircrafts departing at or before this hour
    for terminal in bcn.terminals:
        for area in terminal.boarding_areas:
            for gate in area.gates:
                if gate.occupied:
                    ac = next((x for x in aircrafts if x.id == gate.aircraft_id), None)
                    if ac and ac.time_departure:
                        try:
                            dep_hour = int(ac.time_departure.split(':')[0])
                            if dep_hour < current_hour:
                                gate.occupied = False
                                gate.aircraft_id = ""
                        except:
                            pass

    # 2. Assign gates to aircraft arriving at this hour
    unassigned = 0
    for ac in aircrafts:
        if ac.time:
            try:
                arr_hour = int(ac.time.split(':')[0])
                if arr_hour == current_hour:
                    res = AssignGate(bcn, ac)
                    if res == -1 or res == "":
                        unassigned += 1
            except:
                pass
    return unassigned

def PlotDayOccupancy(bcn, aircrafts, ax1=None): #Reinicia l'aeroport, simula les 24 hores del dia pas a pas i genera un gràfic de l'evolució de l'ocupació i de vols desatesos
    if bcn is None or not aircrafts: return -1

    # Reset occupancy
    for t in bcn.terminals:
        for area in t.boarding_areas:
            for gate in area.gates:
                gate.occupied = False
                gate.aircraft_id = ""

    AssignNightGates(bcn, aircrafts)

    terminals = [t.name for t in bcn.terminals]
    occupancy_data = {t: [] for t in terminals}
    unassigned_data = []

    for h in range(24):
        unassigned = AssignGatesAtTime(bcn, aircrafts, f"{h:02d}:00")
        unassigned_data.append(unassigned)
        
        for t in bcn.terminals:
            occ = 0
            for area in t.boarding_areas:
                for gate in area.gates:
                    if gate.occupied: occ += 1
            occupancy_data[t.name].append(occ)

    if ax1 is None:
        # Si es crida des de fora sense la interfície, obre una finestra normal
        fig, ax1 = plt.subplots(figsize=(10, 6), facecolor='#1b263b')
        ax1.set_facecolor('#1b263b')
        is_embedded = False
    else:
        # Si li passem l'eix de la interfície, el netegem primer
        ax1.clear()
        ax1.set_facecolor('#1b263b')
        is_embedded = True

    bottom = [0] * 24
    colors = ['#3498db', '#2ecc71', '#9b59b6']

    for idx, t_name in enumerate(terminals):
        ax1.bar(range(24), occupancy_data[t_name], bottom=bottom, label=f'Terminal {t_name}',
                color=colors[idx % len(colors)])
        bottom = [bottom[i] + occupancy_data[t_name][i] for i in range(24)]

    ax1.set_xlabel('Hora', color='white')
    ax1.set_ylabel('Puertas Ocupadas', color='white')
    ax1.tick_params(colors='white')
    ax1.set_xticks(range(24))

    # Creem el segon eix vertical compartint el mateix eix X
    ax2 = ax1.twinx()
    ax2.plot(range(24), unassigned_data, color='#e74c3c', marker='o', linewidth=2, label='No asignados')
    ax2.set_ylabel('Vuelos sin Asignar', color='#e74c3c')
    ax2.tick_params(axis='y', labelcolor='#e74c3c')

    # Si està incrustat, gestionem les llegendes i el títol a la UI, si no, fem el comportament clàssic
    if not is_embedded:
        fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9), facecolor='#1b263b', labelcolor='white')
        plt.title('Dinámica de Ocupación - 24 Horas', color='white')
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.show()
    else:
        # Configuració òptima de la llegenda dins de la mateixa finestra d'interfície
        ax1.legend(loc='upper left', facecolor='#1b263b', labelcolor='white')
        ax2.legend(loc='upper right', facecolor='#1b263b', labelcolor='white')
        ax1.grid(True, linestyle='--', alpha=0.1)
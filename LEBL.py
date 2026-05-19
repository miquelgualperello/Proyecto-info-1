import versio1
class Gate:
    def __init__(self, name):
        self.name = name
        self.occupancy = False
        self.id = None
class BordingArea:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.gate=[]
class Terminal:
    def __init__(self, name, ICAO):
        self.name = name
        self.ICAO =ICAO
        self.bordingArea=[]
class BarcelonaAP:
    def __init__(self, code):
        self.code = code
        self.terminal = []

def SetGates(area, init_gate, end_gate, prefix):
    if end_gate <= init_gate:
        return -1
    area.gates = []
    i = init_gate
    while i <= end_gate:
        nombre = prefix + str(i)
        gate = Gate(nombre)
        area.gates.append(gate)
        i += 1

def LoadAirlines(terminal, t_name):
    filename = t_name + "_Airlines.txt"
    try:
        f = open(filename, "r")
    except:
        return -1
    airlines = []
    for line in f:
        line = line.strip()
        if line != "":
            parts = line.split()
            if len(parts) >= 2:
                icao = parts[-1]
                airlines.append(icao)
    f.close()
    terminal.airlines = airlines
    return 0

def LoadAirportStructure(filename):
    try:
        f = open(filename, "r")
    except:
        return -1
    lines = f.readlines()
    f.close()
    if len(lines) == 0:
        return -1
    first_line = lines[0].split()
    if len(first_line) < 2:
        return -1
    airport_code = first_line[0]
    num_terminals = int(first_line[1])
    airport = BarcelonaAP(airport_code)
    i = 1
    for t in range(num_terminals):
        while i < len(lines) and lines[i].strip() == "":
            i = i + 1
        if i >= len(lines):
            return -1
        terminal_line = lines[i].split()
        if len(terminal_line) < 3:
            return -1
        terminal_name = terminal_line[1]
        num_areas = int(terminal_line[2])
        terminal = Terminal(terminal_name)
        i = i + 1
        for a in range(num_areas):
            while i < len(lines) and lines[i].strip() == "":
                i = i + 1
            if i >= len(lines):
                return -1
            area_line = lines[i].split()
            if len(area_line) < 7:
                return -1
            area_letter = area_line[1]
            area_type = area_line[2]
            init_gate = int(area_line[4])
            end_gate = int(area_line[6])
            area_name = terminal_name + "BA" + area_letter.lower()
            area = BordingArea(area_name, area_type)
            prefix = area_name + "G"
            result = SetGates(area, init_gate, end_gate, prefix)
            if result == -1:
                return -1
            terminal.boarding_areas.append(area)
            i = i + 1
        result = LoadAirlines(terminal, terminal_name)
        if result == -1:
            return -1
        airport.terminals.append(terminal)
    return airport

def GateOccupancy(bcn):
    llista_estat = []
    for terminal in bcn.terminals:
        for area in terminal.boarding_areas:
            for porta in area.gates:
                info = [porta.name, porta.occupied, porta.aircraft_id]
                llista_estat.append(info)
    return llista_estat

def IsAirlineInTerminal(terminal, name):
    if name == "":
        return False
    if name in terminal.airlines:
        return True
    else:
        return False
def SearchTerminal(bcn, name):
    i = 0
    while i < len(bcn.terminal):
        t = bcn.terminal[i]
        if IsAirlineInTerminal(t, name):
            return t.name
        i += 1
    return ""

def AssignGate(bcn, aircraft):
    terminal_name = SearchTerminal(bcn, aircraft.company)
    if terminal_name == "":
        return -1
    es_schengen = versio1.IsSchengenAirport(aircraft.origin)
    i = 0
    while i < len(bcn.terminal):
        t = bcn.terminal[i]
        if t.name == terminal_name:
            j = 0
            while j < len(t.bordingArea):
                area = t.bordingArea[j]
                correcto = False
                if es_schengen == True and area.type == "Schengen":
                    correcto = True
                if es_schengen == False and area.type == "non-Schengen":
                    correcto = True
                if correcto == True:
                    k = 0
                    while k < len(area.gates):
                        g = area.gates[k]
                        if g.occupancy == False:
                            g.occupancy = True
                            g.id = aircraft.id
                            return g.name
                        k += 1
                j += 1
        i += 1
    return -1

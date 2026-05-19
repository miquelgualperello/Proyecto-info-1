import os


# =========================
# CLASSES
# =========================

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


# =========================
# SCHENGEN
# =========================

def IsSchengenAirport(code):
    if code == "":
        return False

    schengen_prefixes = [
        'LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG',
        'EH', 'LH', 'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP',
        'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS'
    ]

    if len(code) < 2:
        return False

    prefix = code[0:2]

    if prefix in schengen_prefixes:
        return True
    else:
        return False


# =========================
# LOAD GATES
# =========================

def SetGates(area, init_gate, end_gate, prefix):
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


# =========================
# LOAD AIRLINES
# =========================

def LoadAirlines(terminal, terminal_name, base_folder):
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


# =========================
# LOAD AIRPORT STRUCTURE
# =========================

def LoadAirportStructure(filename):
    try:
        f = open(filename, "r", encoding="utf-8")
    except:
        return -1

    lines = f.readlines()
    f.close()

    if len(lines) == 0:
        return -1

    base_folder = os.path.dirname(filename)

    first_line = lines[0].split()

    if len(first_line) < 2:
        return -1

    airport_code = first_line[0]
    num_terminals = int(first_line[1])

    airport = BarcelonaAP(airport_code)

    i = 1
    t = 0

    while t < num_terminals:

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
        a = 0

        while a < num_areas:

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
            area = BoardingArea(area_name, area_type)

            prefix = area_name + "G"

            result = SetGates(area, init_gate, end_gate, prefix)

            if result == -1:
                return -1

            terminal.boarding_areas.append(area)

            i = i + 1
            a = a + 1

        result = LoadAirlines(terminal, terminal_name, base_folder)

        if result == -1:
            return -1

        airport.terminals.append(terminal)

        t = t + 1

    return airport


# =========================
# GATE OCCUPANCY
# =========================

def GateOccupancy(bcn):
    if bcn is None:
        return -1

    occupancy_list = []

    for terminal in bcn.terminals:
        for area in terminal.boarding_areas:
            for gate in area.gates:
                info = [
                    terminal.name,
                    area.name,
                    gate.name,
                    gate.occupied,
                    gate.aircraft_id
                ]

                occupancy_list.append(info)

    return occupancy_list


# =========================
# SEARCH TERMINAL
# =========================

def IsAirlineInTerminal(terminal, airline_code):
    if airline_code == "":
        return False

    airline_code = airline_code.upper()

    if airline_code in terminal.airlines:
        return True
    else:
        return False


def SearchTerminal(bcn, airline_code):
    if bcn is None:
        return ""

    airline_code = airline_code.upper()

    for terminal in bcn.terminals:
        if IsAirlineInTerminal(terminal, airline_code):
            return terminal.name

    return ""


# =========================
# ASSIGN GATE
# =========================

def AssignGate(bcn, aircraft):
    if bcn is None:
        return -1

    terminal_name = SearchTerminal(bcn, aircraft.company)

    if terminal_name == "":
        return -1

    origin_is_schengen = IsSchengenAirport(aircraft.origin)

    for terminal in bcn.terminals:

        if terminal.name == terminal_name:

            for area in terminal.boarding_areas:

                correct_area = False

                if origin_is_schengen == True and area.type == "Schengen":
                    correct_area = True

                if origin_is_schengen == False and area.type == "non-Schengen":
                    correct_area = True

                if correct_area == True:

                    for gate in area.gates:

                        if gate.occupied == False:
                            gate.occupied = True
                            gate.aircraft_id = aircraft.id
                            return gate.name

    return -1
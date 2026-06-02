import matplotlib.pyplot as plt
import math
import sys

class Aircraft:
    def __init__(self, id, origin, time, company, destination="", time_departure=""):
        self.id = id
        self.origin = origin
        self.time = time
        self.company = company
        self.destination = destination
        self.time_departure = time_departure

def LoadArrivals(filename): #obre un fitxer amb els vols de arrivada i comprova que elformat sigui correcte
    aircraft_list = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if "AIRCRAFT" in line or line.strip() == "":
                    continue
                try:
                    parts = line.split()
                    if len(parts) >= 4:
                        id_plane = parts[-4]
                        origin = parts[-3]
                        time = parts[-2]
                        company = parts[-1]

                        a = time.split(":")
                        if len(a) == 2 and "00" <= a[0] <= "23" and "00" <= a[1] <= "59":
                            aircraft_list.append(Aircraft(id_plane, origin, time, company))
                except Exception:
                    continue
    except Exception as e:
        print(f"Error general al cargar el archivo {filename}: {e}")
    return aircraft_list

def LoadDepartures(filename): #obre un fitxer amb els vols de sortida i comprova que elformat sigui correcte
    aircraft_list = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if "AIRCRAFT" in line or line.strip() == "":
                    continue
                try:
                    parts = line.split()
                    if len(parts) >= 4:
                        id_plane = parts[-4]
                        destination = parts[-3]
                        time_dep = parts[-2]
                        company = parts[-1]

                        a = time_dep.split(":")
                        if len(a) == 2 and "00" <= a[0] <= "23" and "00" <= a[1] <= "59":
                            aircraft_list.append(Aircraft(id_plane, "", "", company, destination, time_dep))
                except Exception:
                    continue
    except Exception as e:
        print(f"Error general al cargar salidas {filename}: {e}")
    return aircraft_list

def MergeMovements(arrivals, departures): #busca entre les llistes de arrivades i sortides si un mateix avio al arrivar torna asortir
    if len(arrivals) == 0 and len(departures) == 0:
        return -1
    
    def to_min(t_str):
        if not t_str: return 0
        try:
            h, m = map(int, t_str.split(':'))
            return h * 60 + m
        except:
            return 0

    merged = []
    used_deps = set()

    # Sort to match chronologically
    sorted_arrs = sorted(arrivals, key=lambda x: to_min(x.time))
    sorted_deps = sorted(departures, key=lambda x: to_min(x.time_departure))

    for arr in sorted_arrs:
        matched = None
        arr_m = to_min(arr.time)
        for dep in sorted_deps:
            if dep.id == arr.id and dep not in used_deps:
                if to_min(dep.time_departure) >= arr_m:
                    matched = dep
                    break
        if matched:
            ac = Aircraft(arr.id, arr.origin, arr.time, arr.company, matched.destination, matched.time_departure)
            merged.append(ac)
            used_deps.add(matched)
        else:
            ac = Aircraft(arr.id, arr.origin, arr.time, arr.company, "", "")
            merged.append(ac)

    for dep in sorted_deps:
        if dep not in used_deps:
            ac = Aircraft(dep.id, "", "", dep.company, dep.destination, dep.time_departure)
            merged.append(ac)

    return merged

def NightAircraft(aircrafts): #filtra els avions que nomes surten del aeroport i no tornen aquell dia pertant surten per la nit
    if len(aircrafts) == 0:
        return -1
    return [a for a in aircrafts if (a.time == "" or a.time is None) and a.time_departure != ""]

def SaveFlights(aircrafts, filename):#agafa la llista de avions i els posa en un fitxeer de sortida amb el format de columnes anterior
    if len(aircrafts) == 0:
        return 1
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("AIRCRAFT ORIGIN ARRIVAL AIRLINE")
            for plane in aircrafts:
                line = f"{plane.id or '-'} {plane.origin or '-'} {plane.time or '0'} {plane.company or '-'}"

                f.write(line)
        return 0
    except Exception:
        return 1

def PlotArrivals(aircraft):#plot que conta quants avions arriven cada hora del dia
    if len(aircraft) == 0:
        return
    hours = [0] * 24
    for plane in aircraft:
        try:
            if plane.time:
                hour = int(plane.time.split(":")[0])
                hours[hour] += 1
        except:
            pass
    plt.figure(figsize=(8, 5))
    plt.bar(range(24), hours, color='#3498db')
    plt.xlabel("Hora")
    plt.ylabel("Llegadas")
    plt.title("Llegadas por hora")
    plt.show()

def PlotAirlines(aircrafts): # plot que et deixa seleccionar airlines i et fa un plot ensenyant comparativament quants vols de cada un passen per el aeroport
    if len(aircrafts) == 0:
        return
    conteo = {}
    for a in aircrafts:
        conteo[a.company] = conteo.get(a.company, 0) + 1
    plt.figure(figsize=(8, 5))
    plt.bar(conteo.keys(), conteo.values(), color='#9b59b6')
    plt.xticks(rotation=45)
    plt.title("Vuelos por compañía")
    plt.show()

def PlotFlightsType(aircrafts):#plot que ensenya si els vols son schengen o no
    if not aircrafts:
        return
    schengen_prefixes = ['LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH',
                         'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS']
    schengen = 0
    no_schengen = 0
    for a in aircrafts:
        ref = a.origin if a.origin else a.destination
        if ref and len(ref) >= 2:
            if ref[:2] in schengen_prefixes:
                schengen += 1
            else:
                no_schengen += 1
    plt.bar(["Llegadas/Vuelos"], [schengen], label="Schengen", color='#2ecc71')
    plt.bar(["Llegadas/Vuelos"], [no_schengen], bottom=[schengen], label="No Schengen", color='#e74c3c')
    plt.legend()
    plt.show()

def distancia(coord1, coord2):# calcula la distancia entre dos aeroports tenint en compte la corvatura de la terra
    R = 6371
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def LongDistanceArrivals(aircrafts, airports):# fent serfir la funcio anterior filatra els vols que estan a mes de 2000km de disitancia
    resultado = []
    LEBL = (41.2974, 2.0833)
    for avion in aircrafts:
        if not avion.time: continue
        origen = None
        for ap in airports:
            if ap.code == avion.origin:
                origen = (ap.lat, ap.lon)
                break
        if origen:
            if distancia(origen, LEBL) > 2000:
                resultado.append(avion)
    return resultado

def SetSchengen(airport): #afegeix el atribut bolea de si es schengen o no a el vol
    schengen_prefixes = ['LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH',
                         'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS']
    airport.schengen = False
    if airport.code and len(airport.code) >= 2:
        if airport.code[:2] in schengen_prefixes:
            airport.schengen = True

def MapFlights(aircrafts, airports): #genera un fitxer kml per dibuixar lineas de vol entre aeroports en google earth
    if not aircrafts:
        return
    LEBL_LAT = 41.2974
    LEBL_LON = 2.0833
    try:
        with open("flights.kml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            f.write('<Document>\n')
            f.write('<name>Flights to Barcelona</name>\n')
            for a in aircrafts:
                ref_code = a.origin if a.origin else a.destination
                if not ref_code: continue
                origin_airport = None
                for ap in airports:
                    if ap.code == ref_code:
                        origin_airport = ap
                        break
                if origin_airport is not None:
                    SetSchengen(origin_airport)
                    color = "ff00ff00" if origin_airport.schengen else "ff0000ff"
                    f.write("<Placemark>\n")
                    f.write(f"<name>{a.id} ({ref_code})</name>\n")
                    f.write("<Style>\n<LineStyle>\n")
                    f.write(f"<color>{color}</color>\n<width>3</width>\n")
                    f.write("</LineStyle>\n</Style>\n")
                    f.write("<LineString>\n<tessellate>1</tessellate>\n<coordinates>\n")
                    f.write(f"{origin_airport.lon},{origin_airport.lat},0\n")
                    f.write(f"{LEBL_LON},{LEBL_LAT},0\n")
                    f.write("</coordinates>\n</LineString>\n")
                    f.write("</Placemark>\n")
            f.write("</Document>\n</kml>\n")
    except Exception as e:
        print("Error en MapFlights:", e)

import matplotlib.pyplot as plt
import math
import sys

class Aircraft:
    def __init__(self, id, origin, time, company):
        self.id = id
        self.origin = origin
        self.time = time
        self.company = company


class Airport:
    def __init__(self, code, lat, lon):
        self.code = code
        self.lat = lat
        self.lon = lon
        self.schengen = False

def LoadArrivals(filename):
    aircraft_list = []
    try:
        with open(filename, "r") as f:
            for line in f:
                if "AIRCRAFT" in line:
                    continue
                parts = line.split()
                if len(parts) == 4:
                    aircraft_list.append(
                        Aircraft(parts[0], parts[1], parts[2], parts[3])
                    )
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")
        return []
    return aircraft_list


def SaveFlights(aircrafts, filename):
    if len(aircrafts) == 0:
        print("Error: la lista de aviones está vacía.")
        return 1
    try:
        with open(filename, "w") as f:
            f.write("AIRCRAFT ORIGIN ARRIVAL AIRLINE\n")
            for plane in aircrafts:
                line = f"{plane.id or '-'} {plane.origin or '-'} {plane.time or '0'} {plane.company or '-'}\n"
                f.write(line)
        print(f"Archivo {filename} guardado correctamente.")
        return 0
    except Exception as e:
        print(f"Error escribiendo el archivo: {e}")
        return 1

def PlotArrivals(aircraft):
    if len(aircraft) == 0:
        print("Error: lista vacía")
        return

    hours = [0] * 24
    for plane in aircraft:
        try:
            hour = int(plane.time.split(":")[0])
            hours[hour] += 1
        except:
            pass

    plt.figure(figsize=(8, 5))
    plt.bar(range(24), hours)
    plt.xlabel("Hora")
    plt.ylabel("Llegadas")
    plt.title("Llegadas por hora")
    plt.show()


def PlotAirlines(aircrafts):
    if len(aircrafts) == 0:
        print("Error")
        return

    conteo = {}
    for a in aircrafts:
        conteo[a.company] = conteo.get(a.company, 0) + 1

    plt.figure(figsize=(8, 5))
    plt.bar(conteo.keys(), conteo.values())
    plt.xticks(rotation=45)
    plt.title("Vuelos por compañía")
    plt.show()


def PlotFlightsType(aircrafts):
    if not aircrafts:
        print("Error")
        return

    schengen_prefixes = ['LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH',
                         'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS']

    schengen = 0
    no_schengen = 0

    for a in aircrafts:
        if a.origin and len(a.origin) >= 2:
            if a.origin[:2] in schengen_prefixes:
                schengen += 1
            else:
                no_schengen += 1

    plt.bar(["Llegadas"], [schengen], label="Schengen")
    plt.bar(["Llegadas"], [no_schengen], bottom=[schengen], label="No Schengen")
    plt.legend()
    plt.show()

LEBL = (41.2974, 2.0833)


def distancia(coord1, coord2):
    R = 6371
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def LongDistanceArrivals(aircrafts, airports):
    resultado = []

    for avion in aircrafts:
        origen = None
        for ap in airports:
            if ap.code == avion.origin:
                origen = (ap.lat, ap.lon)
                break

        if origen:
            if distancia(origen, LEBL) > 2000:
                resultado.append(avion)

    return resultado


def SetSchengen(airport):
    schengen_prefixes = ['LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH',
                         'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS']

    airport.schengen = False
    if airport.code and len(airport.code) >= 2:
        if airport.code[:2] in schengen_prefixes:
            airport.schengen = True

def MapFlights(aircrafts, airports):
    if not aircrafts:
        print("Error: No hi ha vols per mapejar.")
        return
    LEBL_LAT = 41.2974
    LEBL_LON = 2.0833
    try:
        f = open("flights.kml", "w", encoding="utf-8")
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        f.write('<Document>\n')
        f.write('<name>Flights to Barcelona</name>\n')
        for a in aircrafts:
            origin_airport = None
            i = 0
            while i < len(airports):
                if airports[i].code == a.origin:
                    origin_airport = airports[i]
                    break
                i = i + 1
            if origin_airport is not None:
                SetSchengen(origin_airport)
                if origin_airport.schengen:
                    color = "ff00ff00"
                else:
                    color = "ff0000ff"
                f.write("<Placemark>\n")
                f.write("<name>" + a.id + " from " + a.origin + "</name>\n")
                f.write("<Style>\n")
                f.write("<LineStyle>\n")
                f.write("<color>" + color + "</color>\n")
                f.write("<width>3</width>\n")
                f.write("</LineStyle>\n")
                f.write("</Style>\n")
                f.write("<LineString>\n")
                f.write("<coordinates>\n")
                f.write(str(origin_airport.lon) + "," +
                        str(origin_airport.lat) + ",0\n")
                f.write(str(LEBL_LON) + "," +
                        str(LEBL_LAT) + ",0\n")
                f.write("</coordinates>\n")
                f.write("</LineString>\n")
                f.write("</Placemark>\n")
        f.write("</Document>\n")
        f.write("</kml>\n")
        f.close()
        print("Fitxer flights.kml generat correctament.")
    except Exception as e:
        print("Error:", e)


import os
import subprocess

# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    airports = [
        Airport("LEMD", 40.4983, -3.5676),
        Airport("LFPG", 49.0097, 2.5479),
        Airport("EGLL", 51.4700, -0.4543),
        Airport("OMDB", 25.2532, 55.3657),
        Airport("KJFK", 40.6413, -73.7781)
    ]

    data = LoadArrivals("arrivals.txt")

    print("Vuelos cargados:", len(data))

    long = LongDistanceArrivals(data, airports)

    print("Larga distancia:")
    for v in long:
        print(v.id, v.origin)

    PlotArrivals(data)
    PlotAirlines(data)
    PlotFlightsType(data)

    MapFlights(data, airports)

    path = os.path.abspath("flights.kml")

    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
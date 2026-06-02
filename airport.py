import matplotlib.pyplot as plt
class Airport:
    def __init__(self, code, lat, lon):
        self.code = code
        self.lat = lat
        self.lon = lon
        self.schengen = False
def IsSchengenAirport(code): #comprova si un aeroport es del espai schengen o no
    if code == "":
        return False
    schengen = ['LO', 'EB', 'LK', 'EK', 'EE', 'EF', 'LF', 'ED', 'ET', 'LG', 'EH', 'LH', 'BI', 'LI', 'EV', 'EY', 'EL','LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS']
    prefix = code[0] + code[1]
    i = 0
    while i < len(schengen):
        if prefix == schengen[i]:
            return True
        i = i + 1
    return False
def SetSchengen(airport): #crid la funcio anterior de is schengen airport i li posa el atribut de si o no al aeroport
    airport.schengen = IsSchengenAirport(airport.code)
def PrintAirport(airport): #mostra la informacio dels aeroports
    print("Code:", airport.code)
    print("Lat:", airport.lat)
    print("Lon:", airport.lon)
    print("Schengen:", airport.schengen)
def convert_coord(coord): #canvia les cordenades de texten numeros decimals i di son sud o west canvia el signe
    direction = coord[0]
    if len(coord) == 7:
        deg = int(coord[1:3])
        minutes = int(coord[3:5])
        seconds = int(coord[5:7])
    else:
        deg = int(coord[1:4])
        minutes = int(coord[4:6])
        seconds = int(coord[6:8])
    decimal = deg + minutes/60 + seconds/3600
    if direction == 'S' or direction == 'W':
        decimal = -decimal
    return decimal
def LoadAirports(filename):#obre un fitxer amb aeroports i converteix en una llista i determina si son schengen o no
    airports = []
    try:
        f = open(filename, "r")
        f.readline()
        while True:
            line = f.readline()
            if line == "":
                break
            parts = line.split()
            code = parts[0]
            lat = convert_coord(parts[1])
            lon = convert_coord(parts[2])
            a = Airport(code, lat, lon)
            SetSchengen(a)
            airports.append(a)
        f.close()
    except:
        return []
    return airports
def SaveSchengenAirports(airports, filename): #Filtra la llista d'aeroports i guarda en un fitxer de text només aquells que formen part de l'espai Schengen, emmagatzemant el seu codi, latitud i longitud
    if len(airports) == 0:
        return -1
    f = open(filename, "w")
    f.write("CODE LAT LON\n")
    i = 0
    while i < len(airports):
        if airports[i].schengen == True:
            line = str(airports[i].code) + " " + str(airports[i].lat) + " " + str(airports[i].lon) + "\n"
            f.write(line)
        i = i + 1
    f.close()
def AddAirport(airports, airport): #afegeix unnou aeroporten la llista pero tambe comprova si ja existeix
    i = 0
    while i < len(airports):
        if airports[i].code == airport.code:
            return
        i = i + 1
    airports.append(airport)
def RemoveAirport(airports, code): #busca un aeroport i si el troba el elimina si no retorna -1
    i = 0
    while i < len(airports):
        if airports[i].code == code:
            j = i
            while j<len(airports)-1:
                airports[j] = airports[j+1]
                j=j+1
            del airports[len(airports)-1]
            return
        i = i + 1
    return -1
def PlotAirports(airports): # mostra un plot amb els aeroports schengen i no schengen
    if not airports:
        print("No hay aeropuertos para mostrar")
        return
    schengen_count = 0
    for airport in airports:
        if airport.schengen:
            schengen_count += 1
    non_schengen_count = len(airports) - schengen_count
    plt.figure(figsize=(5, 4))
    plt.bar(["Aeropuertos"], [schengen_count], label="Schengen", color="green")
    plt.bar(
        ["Aeropuertos"],
        [non_schengen_count],
        bottom=[schengen_count],
        label="No Schengen",
        color="red",
    )
    plt.ylabel("Aeropuertos")
    plt.title("Aeropuertos Schengen vs No Schengen")
    plt.legend()
    plt.tight_layout()
    plt.show()
def MapAirports(airports): #crea un fitxer kml i coloca cada punt de el aeroport en ell per despres obrirlo en google earth
    f = open("airports.kml", "w")
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
    f.write('<Document>\n')
    i = 0
    while i < len(airports):
        a = airports[i]
        if a.schengen == True:
            color = "ff00ff00"
        else:
            color = "ff0000ff"
        f.write("<Placemark>\n")
        f.write("<name>" + a.code + "</name>\n")
        f.write("<Style>\n")
        f.write("<IconStyle>\n")
        f.write("<color>" + color + "</color>\n")
        f.write("</IconStyle>\n")
        f.write("</Style>\n")
        f.write("<Point>\n")
        f.write("<coordinates>" + str(a.lon) + "," + str(a.lat) + ",0</coordinates>\n")
        f.write("</Point>\n")
        f.write("</Placemark>\n")
        i = i + 1
    f.write('</Document>\n</kml>')
    f.close()

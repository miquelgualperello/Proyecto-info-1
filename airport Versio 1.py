# airport.py
class Airport:
    def __init__(self, code, lat, lon):
        self.code = code
        self.lat = lat
        self.lon = lon
        self.schengen = False
def IsSchengenAirport(code):
    if code == "":
        return False
    schengen = ['LO','EB','LK','LC','EK','EE','EF','LF','ED','LG','EH','LH',
                'BI','LI','EV','EY','EL','LM','EN','EP','LP','LZ','LJ','LE','ES','LS']
    prefix = code[0] + code[1]
    i = 0
    while i < len(schengen):
        if prefix == schengen[i]:
            return True
        i = i + 1
    return False
def SetSchengen(airport):
    airport.schengen = IsSchengenAirport(airport.code)
def PrintAirport(airport):
    print("Code:", airport.code)
    print("Lat:", airport.lat)
    print("Lon:", airport.lon)
    print("Schengen:", airport.schengen)
    print("-----------------")
def convert_coord(coord):
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
def LoadAirports(filename):
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
def SaveSchengenAirports(airports, filename):
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
def AddAirport(airports, airport):
    i = 0
    while i < len(airports):
        if airports[i].code == airport.code:
            return
        i = i + 1
    airports.append(airport)
def RemoveAirport(airports, code):
    i = 0
    while i < len(airports):
        if airports[i].code == code:
            airports.pop(i)
            return
        i = i + 1
    return -1

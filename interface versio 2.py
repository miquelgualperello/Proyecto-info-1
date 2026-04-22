import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from airport import IsSchengenAirport
import tkintermapview


# ================== MODELO ==================
class Aircraft:
    def __init__(self, id, airline, origin, arrival):
        self.id = id
        self.airline = airline
        self.origin = origin
        self.arrival = arrival


def LoadArrivals(filename):
    aircrafts = []

    try:
        with open(filename, "r") as f:
            for linia in f:
                parts = linia.split()
                if len(parts) == 4:
                    aircrafts.append(
                        Aircraft(parts[0], parts[3], parts[1], parts[2])
                    )
    except Exception as e:
        print("Error:", e)
        return []

    return aircrafts


# ================== INTERFAZ ==================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Vuelos ✈️")
        self.root.geometry("1200x700")

        self.aircrafts = []

        # ===== LEFT PANEL =====
        left_frame = tk.Frame(root, width=200, bg="#2c3e50")
        left_frame.pack(side="left", fill="y")

        tk.Button(left_frame, text="Cargar archivo", command=self.load_file).pack(pady=10)
        tk.Button(left_frame, text="Llegadas por hora", command=self.plot_arrivals).pack(pady=10)
        tk.Button(left_frame, text="Por aerolínea", command=self.plot_airlines).pack(pady=10)
        tk.Button(left_frame, text="Tipo vuelo", command=self.plot_type).pack(pady=10)
        tk.Button(left_frame, text="Mostrar mapa", command=self.show_map).pack(pady=10)

        # ===== MAIN AREA =====
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(side="right", fill="both", expand=True)

        self.canvas = None
        self.map_widget = None

    # ================== FUNCIONES ==================

    def clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def load_file(self):
        file = filedialog.askopenfilename()
        if file:
            self.aircrafts = LoadArrivals(file)
            print("Cargados:", len(self.aircrafts))

    # ===== GRÁFICAS =====

    def draw_plot(self, fig):
        self.clear_main()
        self.canvas = FigureCanvasTkAgg(fig, master=self.main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def plot_arrivals(self):
        if not self.aircrafts:
            return

        horas = [0] * 24

        for a in self.aircrafts:
            if ":" in a.arrival:
                h = int(a.arrival.split(":")[0])
                horas[h] += 1

        fig = plt.Figure()
        ax = fig.add_subplot(111)
        ax.bar(range(24), horas)
        ax.set_title("Llegadas por hora")

        self.draw_plot(fig)

    def plot_airlines(self):
        if not self.aircrafts:
            return

        conteo = {}

        for a in self.aircrafts:
            conteo[a.airline] = conteo.get(a.airline, 0) + 1

        fig = plt.Figure()
        ax = fig.add_subplot(111)
        ax.bar(conteo.keys(), conteo.values())
        ax.set_title("Vuelos por compañía")

        self.draw_plot(fig)

    def plot_type(self):
        sch, no_sch = 0, 0

        for a in self.aircrafts:
            if IsSchengenAirport(a.origin):
                sch += 1
            else:
                no_sch += 1

        fig = plt.Figure()
        ax = fig.add_subplot(111)
        ax.bar(["Schengen", "No Schengen"], [sch, no_sch])
        ax.set_title("Tipo de vuelos")

        self.draw_plot(fig)

    # ===== MAPA CON TRAYECTORIAS =====

    def show_map(self):
        self.clear_main()

        self.map_widget = tkintermapview.TkinterMapView(self.main_frame, width=800, height=600)
        self.map_widget.pack(fill="both", expand=True)

        # Centrar en Barcelona
        self.map_widget.set_position(41.297, 2.083)
        self.map_widget.set_zoom(5)

        # Coordenadas de aeropuertos
        airports_coords = {
            "BCN": (41.297, 2.083),
            "MAD": (40.472, -3.561),
            "CDG": (49.009, 2.547),
            "FRA": (50.037, 8.562),
            "LHR": (51.470, -0.454),
            "AMS": (52.310, 4.768),
            "FCO": (41.800, 12.238),
        }

        # Marcar Barcelona
        bcn_lat, bcn_lon = airports_coords["BCN"]
        self.map_widget.set_marker(bcn_lat, bcn_lon, text="BCN")

        for a in self.aircrafts:
            if a.origin == "BCN" and a.arrival in airports_coords:

                dest_lat, dest_lon = airports_coords[a.arrival]

                self.map_widget.set_marker(dest_lat, dest_lon, text=a.arrival)

                self.map_widget.set_path([
                    (bcn_lat, bcn_lon),
                    (dest_lat, dest_lon)
                ])

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
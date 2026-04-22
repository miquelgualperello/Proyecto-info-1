import tkinter as tk
from tkinter import messagebox

from Projecte.airport import *
airports = []
def cargar():
    global airports
    airports = LoadAirports("airports.txt")
    label.config(text="Loaded: " + str(len(airports)))
def añadir():
    code = entry_code.get().strip()
    lat = float(entry_lat.get())
    lon = float(entry_lon.get())
    a = Airport(code, lat, lon)
    SetSchengen(a)
    AddAirport(airports, a)
    label.config(text="Added: " + code)
def eliminar():
    code = entry_code.get().strip()
    RemoveAirport(airports, code)
    label.config(text="Removed: " + code)
def mostrar():
    i = 0
    while i < len(airports):
        PrintAirport(airports[i])
        i = i + 1
    label.config(text="Printed in console")
def plot_airports():
    if not airports:
        messagebox.showinfo("Info", "Carga aeropuertos primero")
        return
    PlotAirports(airports)
def guardar():
    SaveSchengenAirports(airports, "../Exercicis/output.txt")
    label.config(text="Saved file")
def mapa():
    MapAirports(airports)
    label.config(text="KML created")
ventana = tk.Tk()
ventana.title("Airport Manager")
ventana.geometry("300x400")
titulo = tk.Label(ventana, text="Airport Manager", font=("Arial", 14))
titulo.pack(pady=10)
frame_form = tk.Frame(ventana)
frame_form.pack(pady=10)
tk.Label(frame_form, text="Code").grid(row=0, column=0)
entry_code = tk.Entry(frame_form)
entry_code.grid(row=0, column=1)
tk.Label(frame_form, text="Latitude").grid(row=1, column=0)
entry_lat = tk.Entry(frame_form)
entry_lat.grid(row=1, column=1)
tk.Label(frame_form, text="Longitude").grid(row=2, column=0)
entry_lon = tk.Entry(frame_form)
entry_lon.grid(row=2, column=1)
frame_buttons = tk.Frame(ventana)
frame_buttons.pack(pady=10)
tk.Button(frame_buttons, text="Load", width=15, command=cargar).pack(pady=2)
tk.Button(frame_buttons, text="Add Airport", width=15, command=añadir).pack(pady=2)
tk.Button(frame_buttons, text="Remove Airport", width=15, command=eliminar).pack(pady=2)
tk.Button(frame_buttons, text="Show Airports", width=15, command=mostrar).pack(pady=2)
tk.Button(frame_buttons, text="Save Schengen", width=15, command=guardar).pack(pady=2)
tk.Button(frame_buttons, text="Map (Google Earth)", width=15, command=mapa).pack(pady=2)
tk.Button(frame_buttons, text="Plot", width=15, command=plot_airports).pack(pady=2)
label = tk.Label(ventana, text="Ready", fg="blue")
label.pack(pady=10)

ventana.mainloop()
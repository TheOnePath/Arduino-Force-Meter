import serial
import re
import threading
import sys, os
import csv
import configparser
import tkinter as tk

from lib.graph_plotter import PlotGraph
from tkinter import messagebox, filedialog
from serial.tools import list_ports


config = configparser.ConfigParser()
config.read('setup.ini')

recording = False
records = []
dump_val = int(config['SETUP']['count'])
init_time = 0


def restart():
    if messagebox.askokcancel("Restart Program...", message="Restart works if the program is executed "\
                                                                    "from the command-line environment only. Any"\
                                                                    "any data genarated is not saved automatically.\n\n"\
                                                                    "Do you wish to continue?"):
        # This function restarts the program.
        # NOTE: All data will be lost of not saved!
        print(f"Restarting Arduino on {conn.port}:{conn.bps}...")
        os.system('cls')
        python = sys.executable
        os.execl(python, python, * sys.argv)             
    else:
        return


def record(menu):
    global recording, records, init_time

    if not recording:
        print("Recording Enabled...")
        menu.entryconfigure(1, label="Stop Recording")
        
        records.clear()
        init_time = 0
        recording = True
    else:
        print("Recording Disabled...")
        menu.entryconfigure(1, label="Record")
        
        dump_data()
        recording = False
        

def dump_data():
    global dump_val
    
    if len(records) > 0:
        print(f"Gathered recordings: {records}")
        print(f"Peak value: {max(records)[0]}")
        average_value = 0
        for i in records:
            average_value += int(i[0])

        average = round(float(average_value / len(records)), 2)
        print(f"Average value: {average}")

        print(f"\nDumping recordings into data_{dump_val}.csv")
        with open(f"results/data_{dump_val}.csv", 'w', newline='') as csvfile:
            fieldnames = ['force', 'newtons', 'time', 'peak', 'average']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for item in records:
                writer.writerow({'force': item[0], 'newtons': item[1], 'time': item[2]})
            
            writer.writerow({'peak': max(records)[0], 'average': average})
            dump_val += 1
    else:
        return


def open_dump():
    filename = filedialog.askopenfilename(initialdir="./", title="Open File...", filetypes=[("Text File","*.csv")])
    if not filename == '':
        os.popen(f'"{filename}"')
    else:
        return


def plot_graph():
    filename = filedialog.askopenfilename(initialdir="./", title="Open File...", filetypes=[("Text File","*.csv")])
    if not filename == '':
        graph = PlotGraph()
        graph.plot(filename)
    else:
        return


class Connect():
    def __init__(self):
        super().__init__()
        print("Firing up initialisation...")
        
        self.port = config['SETUP']['port']
        self.bps = int(config['SETUP']['bps'])

        self.app = Main()
        self.connect()

    def connect(self):
        list_of_ports = list_ports.comports()
        for _port in list_of_ports:
            self.port = list(_port)[0]

        try:
            self.arduino = serial.Serial(self.port, self.bps, timeout=.1)
        except serial.SerialException:
            print(f"\nArduino not found on {self.port}:{self.bps}!\nPlease change the port under Options when the application loads."\
                    "\nReconnecting in 10 seconds...")
            threading.Timer(10.0, self.connect).start()
        else:
            print(f"Arduino found on {self.port}:{self.bps}")


class PortsMenu(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__()
        
        frame = tk.Frame()
        frame.pack()

        button = tk.Button(self, text=conn.port)
        button.pack()


class Main(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Create variable labels
        self.force = tk.StringVar()
        self.newton = tk.StringVar()
        self.time = tk.StringVar()

        # Create Menu
        menubar = tk.Menu(self)
        
        # Enable right-click in Menu
        menu_win = tk.Menu(menubar, tearoff=0)
        # Quick select for recording
        menu_win.add_command(label="Record", command=lambda: record(menu_win))

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Save", command=dump_data)
        filemenu.add_command(label="Open", command=open_dump)

        optionmenu = tk.Menu(menubar, tearoff=0)
        # Call function to load PortsMenu
        optionmenu.add_command(label="Port", command=PortsMenu)
        optionmenu.add_separator()
        optionmenu.add_command(label="Restart", command=restart)
        optionmenu.add_command(label="Close Connection", command=self.quit)

        toolmenu = tk.Menu(menubar, tearoff=0)
        toolmenu.add_command(label="Record", command=lambda: record(toolmenu))
        toolmenu.add_command(label="Plot Graph", command=plot_graph)


        ### Create a port list to select whichever port is available
        ### TODO: script to list through current ports
        portlist = tk.Menu(optionmenu, tearoff=0)
        portlist.add_radiobutton(label="Test", command=None)

        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_cascade(label="Options", menu=optionmenu)
        menubar.add_cascade(label="Tools", menu=toolmenu)

        self.config(menu=menubar)

        # Title window
        tk.Tk.wm_title(self, "Arduino")
        #tk.Tk.wm_geometry(self, "500x250")
        # Populate window
        lbl1 = tk.Label(self, text="Force:")
        lbl2 = tk.Label(self, text="Newton:")
        lbl3 = tk.Label(self, text="Average Force:")
        force_lbl = tk.Label(self, textvariable=self.force)
        netwon_lbl = tk.Label(self, textvariable=self.newton)
        time_lbl = tk.Label(self, textvariable=self.time)

        lbl1.pack(side="left", pady=10, ipadx=5); force_lbl.pack(side="left",ipadx=5)
        lbl2.pack(side="left"); netwon_lbl.pack(side="left",ipadx=5)
        lbl3.pack(side="left"); time_lbl.pack(side="left",ipadx=5)

        self.force.set("0"); self.newton.set("0"); self.time.set("0")

        def popup(event):
            menu_win.post(event.x_root, event.y_root)

        self.bind("<Button-3>", popup)


def main():
    global init_time

    msglog = ''
    try:
        try:
            ard_msg = conn.arduino.readline().decode('utf-8')
        except (AttributeError, serial.SerialException) as e:
            if e:
                pass
            else:
                pass
    except UnicodeDecodeError:
        pass
    
    try:
        if ard_msg[:-4] != msglog: 
            msg = [str(s) for s in ard_msg.split() if not any(char.isalpha() for char in s)]
            if recording:
                if init_time == 0:
                    init_time = int(msg[2])
                    print(init_time)
                else:
                    records.append([float(msg[0]), float(msg[1]), int(msg[2]) - init_time])

            conn.app.force.set(msg[0]); conn.app.newton.set(msg[1]); conn.app.time.set(msg[2])
    except UnboundLocalError:
        pass
    else:
        msglog = ard_msg


    conn.app.after(5, main)


if __name__ == "__main__":
    conn = Connect()
    conn.app.after(256, main)
    conn.app.mainloop()

    print(f"Closing connection to {conn.port}:{conn.bps}...")
    print("Writing to file...")
    with open("setup.ini", 'w') as ini_file:
        config['SETUP'] = {
            'port':conn.port,
            'bps':conn.bps,
            'count':dump_val}

        config.write(ini_file)

print("Terminating process...")
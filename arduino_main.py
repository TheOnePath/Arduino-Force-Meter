"""This module provides a Real-Time serial data stream, read-only, from an Arduino that's connected via COMs port.
NOTE: This module is in beta stages and redevelopment will be necessary for improved efficiency later on.
CREDIT: Program created by Ethan Smith-Coss

    The baurate of the Arduino must be set at 9600 and if the COMs port stored does not match the Arduino then
    this module will reconnect to the correct port and store the new COM port. If the connection to Arduino is
    lost then the script will try and reconnect to the Arduino on the same port every 10 seconds. If this is
    unsuccessful then a new port is searched for, becoming the new COMs port and stored, however if the Arduino
    is found on the same port and baurate then the connection is re-established and the program starts over again.

    Some important classes and methods of this module.
        class Connect:
            This is the main class of the whole application and should be the primary reference point when
            calling the module externally. This class does not take any parameters and initialises some
            important global variables as followed:
                self.port           the main COMs port that is used to create a serial link to the Arduino.
                self.bps            the baurate of the Arduino that's used in conjunction with self.port.
                self.ports_list     a list of the currently available COMs ports
                self.app            an object variable of the class Main. To access variables and methods
                                    within Main, this variable should be referenced.
                
        function connect()      parameters | self       belongs to | Connect:
            This function is responsible for initialising the serial connection to the Arduino on the defined
            ports in class Connect. If the connection is not established then the program will search for another
            available port and reconnect on that port or re-establish the same connection - both occur after 10 seconds.

            If the connection to the Arduino is lost whilst reading the serial data stream, then this function is too
            responsible for reconnecting the serial data stream.
            Some notable global variables within this function accessed through class Connect():
                self.arduino            this is the main variable that holds a link to the arduino
                                        and is reads the serial data stream forever. If the connection
                                        to the Arduino is lost this variable loses its link and raises
                                        the exception serial.SerialException() in function main()
                self.connection_lost    responsible for determining when the connection to the Arduino
                                        is lost and re-established during conditional verification.
        
        class Main      parameter | tk.Tk:
            This is the main class that creates the tkinter framework window for the real-time serial data stream.
            Here, 3 variable labels are created, Force, Newtons and Time, each of which changes in-response to the
            incoming data stream. Some important variables are as followed:
                self.force      the variable label that changes depending on the level of force read from the incoming
                                serial data stream.
                self.newton     the variable label that changes depending on the calculated newton force read from the
                                incoming serial data stream.
                self.time       the variable label that changes according to the internal elapsed time of the Arduino
                                read from the incoming serial data stream.
"""

import csv
import sys, os
import threading
import configparser
import tkinter as tk

try:
    import serial
except ModuleNotFoundError as e:
    print("The following module could not be found:", e)
    quit()

from tkinter import ttk
from serial.tools import list_ports
from lib.graph_plotter import PlotGraph
from tkinter import messagebox, filedialog


config = configparser.ConfigParser()
config.read('setup.ini')

recording = False
records = []
dump_val = int(config['SETUP']['count'])

def restart():
    """Restart the program.\n
    NOTE: This function only works when application is executed from the CLI environment.\n
    A tkinter messagebox will ask to confirm whether a restart is to occur."""

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


def write_to_config():
    print("Writing to file...")
    with open("setup.ini", 'w') as ini_file:
        config['SETUP'] = {
            'port':conn.port,
            'bps':conn.bps,
            'count':dump_val}

        config.write(ini_file)


def record(menu):
    """Called from class Main() through 'Record' in Tools. Create a recording session where data is collected
    and allow for 'Record' to be toggled between starting and stoping.\n
    Data is automatically written to CSV on session end."""

    global recording, records

    if not recording:
        print("Recording Enabled...")
        menu.entryconfigure(0, label="Stop Recording")
        
        records.clear()
        conn.init_time = 0
        recording = True
    else:
        print("Recording Disabled...")
        menu.entryconfigure(0, label="Record")
        
        dump_data()
        recording = False
        

def dump_data():
    """Called after a recording session is completed.\n
    Collected data is written to CSV file."""

    global dump_val
    
    if len(records) > 0:
        print(f"Gathered recordings: {records}")
        print(f"Peak value: {max(records)[0]}")
        average_value = 0
        for i in records:
            average_value += float(i[1])

        average = round(float(average_value / len(records)), 2)
        print(f"Average value: {average}")

        print(f"\nDumping recordings into data_{dump_val}.csv")
        with open(f"results/data_{dump_val}.csv", 'w', newline='') as csvfile:
            fieldnames = ['force', 'newtons', 'time', 'peak', 'average']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for item in records:
                writer.writerow({'force': item[0], 'newtons': item[1], 'time': item[2]})
            
            writer.writerow({'peak': max(records)[1], 'average': average})
            dump_val += 1
    else:
        return


def open_dump():
    """Called from class Main() through 'Open' in File. 
    Select record file to open in default spreadsheet application."""

    filename = filedialog.askopenfilename(initialdir="./", title="Open File...", filetypes=[("Text File","*.csv")])
    if not filename == '':
        os.popen(f'"{filename}"')
    else:
        return


def plot_graph():
    """Called from class Main() through 'Plot Graph' in Tools. Select record to generate a graph from."""
    
    filename = filedialog.askopenfilename(initialdir="./results", title="Open File...", filetypes=[("Text File","*.csv")]).split('/')
    print(filename[-1])
    if not '' in filename:
        graph = PlotGraph()
        graph.plot(filename[-1])
        graph.show()

    else:
        return


class Connect():
    """Initialise the serial connection to the selected Arduino.
    This is the main class when calling externally."""

    def __init__(self, *args, **kwargs):
        '''Setup for the application'''
        
        super(Connect, self).__init__()
        global dump_val

        try:
            cmd_args = list(sys.argv[1]); cmd_args.remove('-')
        except:
            pass
        else:
            if 'f' in cmd_args or 'flush' in cmd_args:
                print("Removing all files in 'results'...")
                folder = f"{os.path.dirname(os.path.realpath(__file__))}/results"
                for filename in os.listdir(folder):
                    path_to_file = os.path.join(folder, filename)
                    os.unlink(path_to_file)

                print("All files have been deleted.", end="") if len(os.listdir(folder)) == 0 else print("Not all files could be removed.", end="")
            
            elif 'r' in cmd_args or 'reset' in cmd_args:
                print("Resetting 'setup.ini'...")
                dump_val = 0

            return

        print("Firing up initialisation...")
        
        self.port = config['SETUP']['port']
        self.bps = int(config['SETUP']['bps'])

        self.connection_lost = False
        self.ports_list = []
        self.init_time = 0

        self.app = Main()
        self.connect()

    def connect(self):
        self.get_ports = list_ports.comports()
        try:
            self.arduino = serial.Serial(self.port, self.bps, timeout=.1)
        except serial.SerialException:
            print(f"\nArduino not found on {self.port}:{self.bps}!\nPlease change the port under Options when the application loads."\
                    "\nReconnecting in 10 seconds...")
            self.app.after(10**4, self.connect)
            self.connection_lost = True
        else:
            print(f"Arduino found on {self.port}:{self.bps}")
            self.connection_lost = False

        for com_port in self.get_ports:
            if not list(com_port) in self.ports_list:
                self.ports_list.append(list(com_port)[0])


class Main(tk.Tk):
    """Main class to initialise the tkinter window called after Connect().\n
    To reference class, use link reference self.app in Connect()"""

    def __init__(self, *args, **kwargs):
        """Setup initialisation to create tkinter window"""

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
        # Call class to load PortsMenu
        optionmenu.add_command(label="Port", command=PortsMenu)
        optionmenu.add_separator()
        optionmenu.add_command(label="Restart", command=restart)
        optionmenu.add_command(label="Close Connection", command=self.quit)

        toolmenu = tk.Menu(menubar, tearoff=0)
        toolmenu.add_command(label="Record", command=lambda: record(toolmenu))
        toolmenu.add_command(label="Plot Graph", command=plot_graph)

        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_cascade(label="Options", menu=optionmenu)
        menubar.add_cascade(label="Tools", menu=toolmenu)

        self.config(menu=menubar)

        # Title window
        tk.Tk.wm_title(self, "Arduino")
        tk.Tk.wm_resizable(self, False, False)
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
            """Local function. Called on user right-click"""
            menu_win.post(event.x_root, event.y_root)

        self.bind("<Button-3>", popup)


class PortsMenu(tk.Tk):
    """Allow selection of a different Arduino.\n
        Not to be called externally and triggered through selecting 'Port' in Options.\n
        (WIP)"""
    
    def __init__(self, *args, **kwargs):
        """Setup initialisation."""

        super().__init__()
        ## NOTE:
        # incremental factor equals 6. When width isn't passed, 
        # the number of pixels equals 44px
        # ...
        # formaula - 'width = n' = (wm_width - px[width = 1]) / k, when k = 6
        #            (key px[...] means no. of pixels of width = 1)
        ## FUTHER NOTE:
        # Since the value of n cannot be a decimal value, rounding to the nearest
        # whole number will be an offset to the actually size.
        ## EXAMPLE:
        # button = ttk.Button(self, text="Hello World", width=round((int(wm_width)/2 - 16) / 6), command=self.callback)
        ##

        wm_width = '250'
        wm_height = '50'
        
        tk.Tk.wm_title(self, "Ports Menu")
        tk.Tk.wm_geometry(self, wm_width + "x" + wm_height)
        tk.Tk.wm_resizable(self, False, False)

        frame = ttk.Frame()
        frame.pack()

        self.port_options = []
        self.update_ports_list()

        self.selected_port = tk.StringVar(self)

        title_lbl = ttk.Label(self, text="Avaliable Ports")
        title_lbl.pack()

        port_lbl = ttk.Label(self, text="Ports:")
        port_lbl.pack(side="left", padx=20)

        if (conn.connection_lost and len(self.port_options) == 1 and conn.port in self.port_options) or (not conn.connection_lost and len(self.port_options) == 1 and conn.port in self.port_options):
            no_ports = ttk.Label(self, text=conn.port)
            no_ports.pack(side="left", padx=10)
        elif len(self.port_options) >= 1:
            option = ttk.OptionMenu(self, self.selected_port, conn.port, *self.port_options, command=self.optionmenu_onchange)
            option.pack(side="left")
        else:
            no_ports = ttk.Label(self, text="No Port Available...")
            no_ports.pack(side="left", padx=10)


    def update_ports_list(self):
        self.get_ports = list_ports.comports()
        if len(self.get_ports) == 0:
            self.port_options.clear()
            return

        for com_port in self.get_ports:
            if not list(com_port) in self.port_options:
                self.port_options.append(list(com_port)[0])
   

    def optionmenu_onchange(self, event):
        """Local callback - changes the serial port."""
        self.update_ports_list()

        conn.port = event
        if not conn.connection_lost:
            print(f"Reconnecting on {conn.port}:{conn.bps}...")
            conn.connect()


def main():
    """Main function to be called after the tkinter window has loaded.\n
    Real-Time data stream from Arduino and displayed to the tkinter window."""

    msglog = ''
    try:
        try:
            ard_msg = conn.arduino.readline().decode('utf-8')
        except (AttributeError, serial.SerialException):
            if not conn.connection_lost:
                print(f"\nConnection to Arduino was lost on {conn.port}:{conn.bps}!\nReconnecting to Arduino in 10 seconds...")
                conn.connection_lost = True
                conn.ports_list.clear()
                threading.Timer(10.0, conn.connect).start()
    except UnicodeDecodeError:
        pass
    
    try:
        if ard_msg[:-4] != msglog: 
            msg = [str(s) for s in ard_msg.split() if not any(char.isalpha() for char in s)]
            if recording:
                if conn.init_time == 0:
                    conn.init_time = int(msg[2])
                    print(conn.init_time)
                else:
                    records.append([float(msg[0]), float(msg[1]), int(msg[2]) - conn.init_time])

            conn.app.force.set(msg[0]); conn.app.newton.set(msg[1]); conn.app.time.set(msg[2])
    except UnboundLocalError:
        pass
    else:
        msglog = ard_msg


    conn.app.after(5, main)


if __name__ == "__main__":
    conn = Connect()
    try:
        conn.app.after(200, main)
        conn.app.mainloop()
    except:
        sys.exit()

    print(f"Closing connection to {conn.port}:{conn.bps}...")
    write_to_config()

print("Terminating process...")
quit()
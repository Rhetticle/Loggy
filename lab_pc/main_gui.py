"""
Team 3 Data Acquisition Device GUI Software
Version 1.5
- Text box

This program will be able to display input from the loggy.
It will be able to change settings in the loggy.
"""
import csv
import math
import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import numpy as np
from matplotlib import pyplot as plt, animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial as ser
import serial.tools.list_ports as stlp
import serial.threaded as st
from datetime import datetime
import sys
import time
import threading as th
import queue as qu

VRWIDG = 0
LOWATWIDG = 1
HIGHATWIDG = 2
ALARMMODEWIDG = 3
ALARMMODELABEL = 4
ALARMSTATUSLABEL = 5

STARTCONTMESSAGE = "START CONT#"
GUI_FONT = "Terminal"

ON = 1
OFF = 0
LOWER_SOS = 1
UPPER_SOS = 2

ONEV = 0
TENV = 1
DISABLED = 0
LIVE = 1
LATCHING = 2
THERMISTOR = 2
PT1000 = 3
LOWI = 4
HIGHI = 5
DIGIT = 1
FLOAT = 0
POSITIVE = 1
NEGATIVE = 2
BAUDRATE = 9600
READIN = 255
# Constants for the thermistor
A_THERM = 3.354016e-3
B_THERM = 2.909670e-4
C_THERM = 1.632136e-6
D_THERM = 7.192200e-8
# Rtemp related constants
CHANNELS_RTEMP = ("Channels", "CH1", "CH2", "CH3", "CH4")
CURRENTS_RTEMP = ("Currents", "200uA", "10uA")
SENSOR_RTEMP = ("Sensor", "Thermistor", "PT1000")
# Channels in the loggy
CHANNELS_LIST = (1, 2, 3, 4, 5, 6, 7, 8)
VOLT_CHANNELS = (1, 2, 3, 4)
ACCEL_CHANNELS = (5, 6, 7)
TEMP_CHANNEL = 8
# Plot related constants
TEXT_BOX_STRING = "Hover over the plot to see data\n"
LIVE_PLOT_INTERVAL = 250
PLOT_HEIGHT = 10  # The dimensions of the plot
PLOT_WIDTH = 15  # These values are best for 1920 x 1080 displays
LEGEND_LOC = "upper left"
VOLT_Y_LABEL = "Voltage (V)"
ACCEL_Y_LABEL = "Acceleration (m/s^2)"
TEMP_Y_LABEL = "Temperature (C)"
X_LABEL = "Time (s)"
V_TITLE = "Voltage Graph"
A_TITLE = "Acceleration Graph"
T_TITLE = "Temperature Graph"
V_GRAPH_IDX = 0
A_GRAPH_IDX = 1
T_GRAPH_IDX = 2
COLOURS = ("#e90000", "#ff6100", "#fff500", "#05fb00",
           "#31d5c8", "#33a7c8", "#001eba", "#a538c6")
MARKER = "."
# File related constants
FILE_TYPES = (('CSV files', '*.csv'),)
FILENAME_FORMAT = "%Y-%m-%d_%H-%M-%S"

# global variable semaphor for threading.
lock = th.Lock()
errors = qu.Queue()


def make_error_pannel(control_frame: tk.Frame | tk.Tk, message: str,
                      program_running: bool):
    """
    Function make an error pannel according to the specific error that has
    occured to the user.
    Parameters
    ----------
    control_frame: tk.Frame|tk.Tk
        Frame or window in which error message is being built from.
    message: str
        Error message to be displayed.
    program_running: bool
        Boolean indicates whether GUI is running.
    Returns nothing.
    """
    if program_running:
        lock.acquire()
        sys.stdout.write("Making top level: \n")
        error_pannel = tk.Toplevel(control_frame)
        sys.stdout.write("Made top level: \n")
        error_message = tk.Label(error_pannel, text=message, bg="red")
        error_message.grid()
        lock.release()
    return


class Data:
    """
    The place where all the data is stored.
    Readings from the loggy are stored in a list.
    (Time, ch1, ch2, ch3, ..., ch8)
    """

    def __init__(self, ready_to_plot):
        """
        Parameters
        ----------
        ready_to_plot : int
            1 for ready, 0 for not ready.
        """
        # Temporary place to store data from the loggy.
        # Has a maximum size of 1000.
        self._data_list = [[] for _ in range(9)]
        # The place where data is saved
        self._save_list = [[] for _ in range(9)]
        # Headers are changed when a voltage channel is switched to a rtemp.
        self.headers = ["Time",
                        "CH1 (V)", "CH2 (V)", "CH3 (V)", "CH4 (V)",
                        "CH5 (m/s^2)", "CH6 (m/s^2)", "CH7 (m/s^2)",
                        "CH8 (C)\n"]
        self._ready_to_plot = ready_to_plot
        # The time that the loggy connected to the GUI
        self._start_time = None
        self._is_data_recording = False  # Flag for recording

    def set_headers(self, headers: list) -> None:
        """Function is used to change the headers of Data.
        Only used in the replay graph.
        Returns nothing
        """
        self.headers = headers

    def record(self) -> None:
        """Function is called when user presses record button.
        The data class will begin to record data when this function is called.
        Returns nothing
        """
        self._is_data_recording = True

    def toggle_rtemp_mode(self, channel: int, current: str,
                          sensor: str) -> None:
        """Function is used to change the mode of a Voltage channel
        Channels 1 to 4 can be switched to temperature mode
        if current != "OFF" and sensor != "OFF"
        Channels 1 to 4 can be switched to voltage mode
        if current == "OFF" and sensor == "OFF"
        Returns nothing"""
        if channel in VOLT_CHANNELS:  # only accept voltage channels
            # Checks in case the main rtemp channel checkbutton was clicked
            # off.
            if current == "OFF" and sensor == "OFF":
                self.headers[channel] = f"CH{channel} (V)"
                return
            self.headers[channel] = f"CH{channel} (C) {current} {sensor}"

    def save_data(self) -> None:
        """Saves the recorded data to a csv file.
        Line format: YYYY-MM-DD_HH-MM-SS.sss,CH1,CH2,CH3,CH4,CH5,CH6,CH7,CH8
        file name format: YYYY-MM-DD_HH-MM-SS.csv
        The file will be saved to the usb drive.
        """
        if not self._save_list:
            return  # _save_list is empty
        start_time = datetime.fromtimestamp(self._save_list[0][0])
        # create the filename string
        filename = start_time.strftime(FILENAME_FORMAT) + ".csv"
        file_directory = os.getcwd()  # current working directory
        file_path = os.path.join(file_directory, filename)
        file = open(file_path, "w")
        print(f"Saved to {file_path}")
        # Write the headers on the first line
        file.write(self.headers[0])
        for header in self.headers[1:]:
            file.write(f",{header}")
        # Write the data that was recorded
        for i in range(len(self._save_list[0])):
            time_stamp = self._save_list[0][i]
            dt = datetime.fromtimestamp(time_stamp)
            dt_str = (dt.strftime(FILENAME_FORMAT)
                      + f".{dt.microsecond // 1000:03d}")
            line = f"{dt_str}"
            for channel in range(1, 9):
                line += f",{self._save_list[channel][i]}"
            line += "\n"
            file.write(line)
        file.close()  # close file resources.
        self._save_list = [[] for _ in range(9)]  # reset the _save_list.
        self._is_data_recording = False  # data has stopped recording.

    def append_data(self, data_str: str) -> None:
        """
        Converts a string from the loggy into a list of floats and
        appends it to the main list.
        If recording is enabled, the data will also be recorded.
        This function will calculate the resistive temperature if required.
        data_str: "D:CH1,CH2,CH3,CH4,CH5,CH6,CH7,CH8"
        """
        if data_str.count(',') != 7:
            return  # skip the line if it does not follow the protocol
        data_str = data_str[2:]  # Remove the "D:"
        data_str_list = data_str.split(',')
        now = time.time()
        self._data_list[0].append(now - self._start_time)
        self._data_list[0] = self._data_list[0][-1000:]

        for channel, dat_str in enumerate(data_str_list, start=1):
            val = float(dat_str)
            if channel in VOLT_CHANNELS:
                if "(C)" in self.headers[channel]:
                    if "200" in self.headers[channel]:
                        current = 0.000200  # 200uA
                    else:
                        current = 0.000010  # 10uA
                    if val < 0:
                        val *= -1
                    rt = val / current
                    if "PT1000" in self.headers[channel]:  # °C PT1000 200uA
                        # if this is negative GUI will fail
                        val = -0.287154 * math.sqrt(abs(159861899 - 21000 *
                                                        rt))
                        val += 3383.81
                    else:  # °C Thermistor 200uA
                        ln = math.log(rt / 1000)
                        val = (A_THERM
                               + B_THERM * ln
                               + C_THERM * ln ** 2
                               + D_THERM * ln ** 3) ** -1
                        val -= 273.15  # convert kelvins to celcius
            self._data_list[channel].append(val)
            self._data_list[channel] = self._data_list[channel][-1000:]

    def clear_data(self) -> None:
        """This function will remove all the data from the
         _data_list and the _save_list"""
        self._start_time = time.time()
        self._data_list = [[] for _ in range(9)]
        self._save_list = [[] for _ in range(9)]

    def get_data(self) -> list:
        """This function returns the entire _data_list.
        This function should be called every 200ms."""
        if self._is_data_recording:
            self._save_list[0].append(time.time())
            for i in CHANNELS_LIST:
                self._save_list[i].append(self._data_list[i][-1])
        return self._data_list

    def ready_to_plot(self) -> int:
        """This function returns 0 if not ready to plot and
        1 if ready to plot"""
        return self._ready_to_plot


class WriteLines(st.LineReader):
    """Class is used to handle a reader thread to read in lines sent from
    firmware to the GUI."""

    def __init__(self, callback, root: tk.Frame | tk.Tk):
        """
        Parameters
        ----------
        callback :
            A callback function used whenever the LineReader recieves a
            message.
        """
        super().__init__()
        self._callback = callback
        self._control_frame = root

    def connection_made(self, transport):
        """Function used to initialise the LineReader. Mostly inherited
        from the super class, with a message printed to the terminal indicating
        startup.
        Returns nothing.
        """
        super(WriteLines, self).connection_made(transport)

    def handle_line(self, data):
        """
        Function is called whenever the Line Reader reads in data sent from the
        port.
        Parameters
        ----------
        data:
            The recieved data from the firmware.
        """
        self._callback(data)

    def connection_lost(self, exc):
        """Function prints a message to the terminal when the connection with
        the Oirt ceases.
        """

        sys.stdout.write("error message\n")
        message = "port closed"
        errors.put(message)

        pass


def search_for_point(x_coordinate, xdata) -> int:
    """
    This function will iterate through all the points in xdata, and it will
    return the index of the point in xdata.
    that is closest to x_coordinate
    """
    difference = sys.maxsize  # Larges value of a integer
    idx = 0

    for i, num in enumerate(xdata):
        diff = abs(num - x_coordinate)
        if diff < difference:
            difference = diff
            idx = i
    return idx


class Graph:
    # Static variable that is shared by all the Graph instances
    num_data_points = 10

    def __init__(self, frame: tk.Frame, name: tuple[str, ...],
                 y_labels: tuple[str, ...]):
        """
        Parameters
        ----------
        frame : tk.Frame
            The frame where the graphs will be placed.
        name : str
            The name of the graph. e.g. Voltage
        y_labels : str
            The name of the y-axis. e.g. Volts (V)
            The x-axis is always time in seconds.
        """
        self._ani = None  # The animation needs to be saved for it to work
        # This variable will become an instance of a data class
        self._data = None
        self._frame = frame  # frame that the graph is in
        # Used in when calculating x-axis and for the text box
        self.temp_data = [[] for _ in range(9)]
        # Dictionary to store the lines.
        self._lines: dict[int, plt.Line2D] = {}
        self._name = name  # name of the graph e.g. voltage, accel, temperature
        self._fig, self._ax = plt.subplots(nrows=3, ncols=1,
                                           figsize=(PLOT_WIDTH, PLOT_HEIGHT))
        self._fig.tight_layout(pad=3.5)
        for i in range(3):  # Setting the axis labels
            self._ax[i].set_title(self._name[i])
            self._ax[i].set_xlabel(X_LABEL)
            self._ax[i].set_ylabel(y_labels[i])
        self._upper_limit = [10.0, 10.0, 30.0]  # Upper y limit
        self._lower_limit = [-10.0, -10.0, 0.0]  # lower y limit
        # The text box
        self._text_box = tk.Text(self._frame, font=(GUI_FONT, 10))
        self._text_box.insert(tk.END, TEXT_BOX_STRING)
        self._text_box.config(state=tk.DISABLED)
        self._text_box.grid(row=0, column=1)
        # Graph canvas, where the graphs are placed
        self._graphs_canvas = FigureCanvasTkAgg(self._fig, master=self._frame)
        self._graphs_canvas.mpl_connect('motion_notify_event',
                                        lambda event:
                                        self.is_mouse_on_axis(event))
        self._mouse_position = None
        self._canvas_widget = self._graphs_canvas.get_tk_widget()
        self._canvas_widget.grid(row=0, column=0)
        self._graphs_canvas.draw()
        # These values are edited by the check buttons on the GUI
        self.show_graph_volt = tk.BooleanVar(value=True)
        self.show_graph_accel = tk.BooleanVar(value=True)
        self.show_graph_temp = tk.BooleanVar(value=True)

    def is_mouse_on_axis(self, event) -> None:
        """Function is called when mouse is moved over the graphs.
        This function builds the text box when the mouse is hovered over the
        inside the axis"""
        self._mouse_position = event.xdata
        for ax in self._ax:
            if event.inaxes == ax:
                self.create_text_box()
                return

    def add_to_plot(self, temp_data: list, headers: list) -> None:
        """
        This function is used to plot the replay graphs.
        All the lines are plotted at once.
        This function creates temp_data for the text box.
        temp_data: [[Time, ...], [CH1, ...], [CH2, ...], ..., [CH8, ...]]
        headers: The header of the CSV file
        """
        for idx, data in enumerate(temp_data):
            self.temp_data[idx] = data[-Graph.num_data_points:]
        for channel in CHANNELS_LIST:
            if channel in VOLT_CHANNELS:
                if "(C)" in headers[channel]:
                    self._ax[T_GRAPH_IDX].plot(self.temp_data[0],
                                               self.temp_data[channel],
                                               label=f"channel {channel}",
                                               marker=MARKER,
                                               color=COLOURS[channel - 1])
                else:
                    self._ax[V_GRAPH_IDX].plot(self.temp_data[0],
                                               self.temp_data[channel],
                                               label=f"channel {channel}",
                                               marker=MARKER,
                                               color=COLOURS[channel - 1])
            elif channel in ACCEL_CHANNELS:
                self._ax[A_GRAPH_IDX].plot(self.temp_data[0],
                                           self.temp_data[channel],
                                           label=f"channel {channel}",
                                           marker=MARKER,
                                           color=COLOURS[channel - 1])
            else:
                self._ax[T_GRAPH_IDX].plot(self.temp_data[0],
                                           self.temp_data[channel],
                                           label=f"channel {channel}",
                                           marker=MARKER,
                                           color=COLOURS[channel - 1])
        # An instance of the data class is made for the text box
        self._data = Data(0)
        self._data.set_headers(headers)
        for g in range(3):
            self._ax[g].legend(loc=LEGEND_LOC)

    def create_text_box(self) -> None:
        """This function creates a text box. The text box displays information
        about the channels. self.temp_data is used to create calculate the
        point for the text box.
        Returns none"""
        # Resize the amount of temporary time values to be the same length as
        # number of points specified.
        if len(self.temp_data[0]) < 1:
            return

        xdata = self.temp_data[0]  # xdata is a list of all the times
        nearest_index = search_for_point(self._mouse_position, xdata)

        time_point = xdata[nearest_index]
        self._text_box.config(state=tk.NORMAL)  # enable writing
        # delete everything from the second row to the end
        self._text_box.delete(2.0, tk.END)
        self._text_box.insert(tk.END, f"\nData at {time_point:.3f} s")
        for channel in CHANNELS_LIST:
            ydata = self.temp_data[channel]
            text = f"\nCH{channel}: {ydata[nearest_index]}"
            if channel in VOLT_CHANNELS:
                if "(C)" in self._data.headers[channel]:
                    text += "C"
                else:
                    text += "V"
            elif channel in ACCEL_CHANNELS:
                text += "m/s^2"
            else:
                text += "C"
            self._text_box.insert(tk.END, text)
        self._text_box.config(state=tk.DISABLED)

    def add_live_plot(self, channels: tuple, data: Data) -> None:
        """ Function is used to create live plots. It should only be called
        once. 'channel' is a list of channels that will be plotted on the
        graph.'data' is used to get the x and y values of the graph.
        Returns none
        """
        # Initialise Live Plots
        self._data = data
        for ch in channels:
            if ch in VOLT_CHANNELS:
                line, = self._ax[V_GRAPH_IDX].plot(
                    [], [], label=f"channel {ch}", marker=MARKER,
                    color=COLOURS[ch - 1])
            elif ch in ACCEL_CHANNELS:
                line, = self._ax[A_GRAPH_IDX].plot(
                    [], [], label=f"channel {ch}", marker=MARKER,
                    color=COLOURS[ch - 1])
            else:
                line, = self._ax[T_GRAPH_IDX].plot(
                    [], [], label=f"channel {ch}", marker=MARKER,
                    color=COLOURS[ch - 1])
            self._lines[ch] = line
        for i in range(3):
            self._ax[i].legend(loc=LEGEND_LOC)

        # Function that does the animating
        def animate(_):
            if not self._data.ready_to_plot():
                return self._lines.values()

            rows = self._data.get_data()
            if len(rows[0]) < 4:
                return self._lines.values()
            time_latest_data_point = rows[0][-1]
            # temp_data can not exceed the specified points
            self.temp_data[0].append(time_latest_data_point)
            self.temp_data[0] = self.temp_data[0][-Graph.num_data_points:]
            # setting the lines
            for channel, line_on_graph in self._lines.items():
                latest_data_point = rows[channel][-1]
                self.temp_data[channel].append(latest_data_point)
                self.temp_data[channel] \
                    = self.temp_data[channel][-Graph.num_data_points:]
                xdata, ydata = line_on_graph.get_data()
                # Change the x-axis
                xdata = np.append(xdata, time_latest_data_point)
                xdata = xdata[-Graph.num_data_points:]
                # Change the y-axis
                ydata = np.append(ydata, latest_data_point)
                ydata = ydata[-Graph.num_data_points:]
                # Reset the points on each line
                line_on_graph.set_data(xdata, ydata)
            # Axis adjustments
            for g in (V_GRAPH_IDX, A_GRAPH_IDX, T_GRAPH_IDX):
                self._ax[g].set_ylim(self._lower_limit[g],
                                     self._upper_limit[g])
                low_x = self.temp_data[0][0]
                high_x = self.temp_data[0][-1]

                if high_x > low_x:
                    self._ax[g].set_xlim(low_x, high_x)

            return self._lines.values()

        # FuncAnimation will keep on calling animate
        self._ani = animation.FuncAnimation(
            self._fig, animate,
            interval=LIVE_PLOT_INTERVAL,
            cache_frame_data=False,  # If this is true we get a warning message
            blit=False  # We are rebuilding the legend every single time
        )

    def clear_graphs(self) -> None:
        """Deletes all the data in the graphs.
        Returns none"""
        self.temp_data = [[] for _ in range(9)]
        for line in self._lines.values():
            line.set_data([], [])
        self._data.clear_data()

    def move_line(self, channel: int, to_temp: bool) -> None:
        """Function is used to move a line from the volt graph to the
        temperature graph and vice versa
        channel: The channel that is to be relocated. Function ensures that
                 the channel is between 1 and 4
        to_temp: True for changing a temperature line to a voltage line,
                 otherwise it is false"""
        if channel not in VOLT_CHANNELS:
            return
        old_line = self._lines[channel]
        # Remove the old line
        old_line.remove()
        idx = V_GRAPH_IDX
        if to_temp:
            idx = T_GRAPH_IDX
            self._ax[V_GRAPH_IDX].legend(loc=LEGEND_LOC)
        else:
            self._ax[T_GRAPH_IDX].legend(loc=LEGEND_LOC)
        # Create a new line on the other plot
        new_line, = self._ax[idx].plot(
            [], [],
            label=f"channel {channel}",
            marker=MARKER,
            color=COLOURS[channel - 1],
        )
        self._ax[idx].legend(loc=LEGEND_LOC)
        self._lines[channel] = new_line

    def set_upper_limit(self, idx: int, upper_new: float) -> None:
        """Changes the upper limit of the y-axis
        idx: must be between 0 and 2 inclusive
        upper_new: the new upper limit"""
        if self._lower_limit[idx] < upper_new:
            self._upper_limit[idx] = upper_new

    def set_lower_limit(self, idx: int, lower_new: float) -> None:
        """Changes the lower limit of the x-axis
        idx: must be between 0 and 2 inclusive
        lower_new: the new lower limit"""
        if self._upper_limit[idx] > lower_new:
            self._lower_limit[idx] = lower_new

    def toggle_graph(self, graph_type: str) -> None:
        """
        Can hide the entire plot or show the entire plot.
        graph_type: "V" for volts, "A" for acceleration, or "T" for temperature
        """
        match graph_type:
            case "V":  # Voltage Graph
                toggle = self.show_graph_volt
                idx = V_GRAPH_IDX
            case "A":  # Acceleration Graph
                toggle = self.show_graph_accel
                idx = A_GRAPH_IDX
            case "T":  # Temperature Graph
                toggle = self.show_graph_temp
                idx = T_GRAPH_IDX
            case _:  # Anything else
                return
        if toggle.get():
            self._ax[idx].set_visible(True)
        else:
            self._ax[idx].set_visible(False)


class Port:
    """Class is used to handle the serial communication between firmware and
    the GUI. Class also initialises
    and handles reader thread and hearbeat thread.
    """

    def __init__(self, root: tk.Frame, live_graph: Graph,
                 port_list: ttk.Combobox | None, widget_vars: list,
                 data: Data | None):
        """
        Parameters
        ----------
        root : tk.Frame
            The frame in which port droplist is located.
        port_list : ttk.Combobox
            The port droplist widget. Can be initialised as none.
        widget_vars : list
            A list of various Tkinter widgets avaliable to the user
            (e.g. voltage scaling).
        data: Data
            Custom class where live results are sent to, to ensure graphing.
        """
        self._program_running = True
        self._live_graph = live_graph

        self._root = root
        self._data = data
        self._port = None
        self._port_list = port_list
        self._refresh_but = None

        # Reader thread protocal.
        self._protocol = None
        self._err_thread = th.Thread(target=self.handle_errors)
        self._err_thread.start()

        # Variables from GUI firmware communicates with.
        self._volt_range = widget_vars[VRWIDG]
        self._low_at = widget_vars[LOWATWIDG]
        self._high_at = widget_vars[HIGHATWIDG]
        self._alarm_modes = widget_vars[ALARMMODEWIDG]
        self._alarm_mode_label = widget_vars[ALARMMODELABEL]
        self._alarm_statuses = widget_vars[ALARMSTATUSLABEL]

        self._firm_message = None
        self._prev_message = None

        self._prev_error = False

        # Initalise ability for user to start connecting to GUI.
        self._port_list = self.init_port_list(self._root, self._port_list)
        self._receiving_start_cons = 0
        # Auto clear inital portlist.
        self.refresh_port_list(self._root, self._port_list)

    def handle_errors(self):
        """Error handling thread function used to print an error message on GUI
        for a user to see."""
        while self._program_running:
            while errors.empty():
                time.sleep(0.1)
            message = errors.get()
            make_error_pannel(self._root, message, self._program_running)

    def get_firmware_message(self, message: str):
        """Function is used as the callback function whenerver the LineReader
        reads something sent from firmware. Will call another function to
        handle GUI functionality upon recieveing something.
        Parameters
        ----------
        message : str
            The message recieved from firmware.
        Returns nothing.
        """
        if self._firm_message:
            # Basically to make sure that our previous message is fine.
            self._prev_message = self._firm_message
        self._firm_message = message

        lock.acquire()
        self.set_widget_vars(message)
        lock.release()

    def _check_and_set_alarm(self, message: str, is_high: bool):
        """Function is used to set alarm threasholds within the GUI.
        Parameters
        ----------
        message : str
            The message read from firmware.
        is_high: bool
            Indicates whether the messages data are higher or lower thresholds.
        Returns nothing.
        """
        if not message.count(" ") == 8:
            return
        # Splits the threshold message 8 times.
        message_split = message.split(" ", maxsplit=8)
        print(message_split)
        # For each message, if it's a channel, set the thresholds
        # appropriatley.
        for word in message_split:
            word_split = word.split(":", maxsplit=2)
            channel_name = word_split[0]
            if channel_name == "LT" or channel_name == "HT":
                continue
            elif channel_name not in ("CH1", "CH2", "CH3", "CH4",
                                      "CH5", "CH6", "CH7", "CH8"):
                return
            channel_idx = int(channel_name[-1])
            value = word_split[1]
            # Autoset thresholds to 0 if not set in the firmware.
            if value == "NAN":
                value = "0"
            if is_high:
                self._high_at[channel_idx - 1].set(value=value)
            else:
                self._low_at[channel_idx - 1].set(value=value)

    def set_widget_vars(self, message):
        """Function is used to adjust the GUI widgets depending on what message
        recieved from firmware.
        Parameters
        ----------
        message : str
            The message read from firmware.
        Returns nothing.
        """
        # Voltage scale messages.
        if message == "V0":
            self._volt_range.set(value=ONEV)

        elif message == "V1":
            self._volt_range.set(value=TENV)

        # Live data message.
        elif message[0:2] == "D:":
            self._data.append_data(message)

        elif message == "%START CONT":
            self._receiving_start_cons = 1

        # Finished recieving all the starting values.
        elif message == "END CONT":
            self._receiving_start_cons = 0
            if self._port.is_open:
                message = "END CONT#"
                if self._port.is_open:
                    self.inside_port_write(message)

        # High or Low starting thresholds recieved.
        elif message[0:6] == "HT: CH":
            self._check_and_set_alarm(message, True)

        elif message[0:6] == "LT: CH":
            # This is the staring high thresholds data.
            self._check_and_set_alarm(message, False)

        # Individual thresholds recieved.
        elif message[0:6] == "ALT CH":
            self._low_at[int(message[6]) - 1].set(value=message[8:])

        elif message[0:6] == "AHT CH":
            self._high_at[int(message[6]) - 1].set(value=message[8:])

        # Alarm status change.
        elif message[0:2] == "AS":
            channel = int(message[5])
            # Set the label in the GUI acording to the change.
            if (int(message[7])) == OFF:
                self._alarm_statuses[channel - 1].config(text=f"  CH{channel} "
                                                              f"Alarm Status: "
                                                              f"Off  \n")
            elif (int(message[7])) == LOWER_SOS:
                self._alarm_statuses[channel - 1].config(
                    text=f"  CH{channel} Alarm Status:  \nTHRESH "
                    "BREACH  ")
            elif (int(message[7])) == UPPER_SOS:
                self._alarm_statuses[channel - 1].config(
                    text=f"  CH{channel} Alarm Status:  \nTHRESH "
                    "BREACH  ")

        # Alarm mode change.
        elif message[0:5] == "AM CH":
            # Adjusting radio button in settings menu.
            self._alarm_modes[int(message[5]) - 1].set(value=message[7:])
            # Adjusting label on main screen.
            if (int(message[-1]) == DISABLED):
                self._alarm_mode_label[int(
                    message[5]) - 1].config(
                    text=f"Alarm Mode Ch{int(message[5])}: Disabled  ")
                self._alarm_modes[int(message[5]) - 1].set(value=DISABLED)
            elif (int(message[-1]) == LIVE):
                self._alarm_mode_label[int(
                    message[5]) - 1].config(
                    text=f"Alarm Mode Ch{int(message[5])}: Live  ")
                self._alarm_modes[int(message[5]) - 1].set(value=LIVE)
            else:
                self._alarm_mode_label[int(
                    message[5]) - 1].config(
                    text=f"Alarm Mode Ch{int(message[5])}: Latching  ")
                self._alarm_modes[int(message[5]) - 1].set(value=LATCHING)
        return

    def init_port_list(self, root: tk.Frame, port_list: ttk.Combobox):
        """Adds a comobox (dropdown) that lists the ports avaliable. Also is
        used to kill previous LineReaders after the portlist is refreshed.
        Parameters
        ----------
        root : tk.Frame
            Frame in which the port_list is located on the GUI.
        port_list: ttk.Combobox
            The tkinter widget used to be portlist.

        Returns a string indicating which port was selected.
        """
        # Check if a prexisting communication exists between firmware and GUI.
        if self._port:
            if self._port.is_open:
                # Stop firmware from sending any messages to GUI.
                message = "STOP CONT#"
                self.inside_port_write(message)

                # Killing the reader thread.
                self._protocol.close()
                self._protocol.join()

                self._port.close()

                # print(f"number of active threads: {th.active_count()}")

                # print(errors.empty())
                # time.sleep(0.3)
                # self._err_thread.join()

        # Destroying previous port_list.
        if port_list:
            port_list.destroy()

        # Pause data plotting.
        if self._data:
            self._data._ready_to_plot = 0

        # Fill out portlist.
        port_nos = stlp.comports(include_links=False)
        port_names = []
        for port_no in port_nos:
            port_names.append(port_no.device)

        tk.Label(root, text="Port Connection: ").grid(row=0, column=2)
        port_list = ttk.Combobox(root, values=[i for i in port_names],
                                 state="readonly")
        port_list.grid(row=0, column=3)

        # Reinstate serial connection once user has selected COM port.
        port = ser.Serial(baudrate=BAUDRATE, timeout=0.1)
        port_struct = [port, root, port_list]

        port_list.bind("<<ComboboxSelected>>",
                       lambda x: self.connect_to_firm(port_struct))
        self._port = port
        return port_list

    def refresh_port_list(self, control_frame: tk.Frame,
                          port_list: ttk.Combobox):
        """Creates a refresh button to reset the port connections and the
        port_list box.
        Parameters
        ----------
        contorl_frame : tk.Frame
            Frame in which the refresh button is located on the GUI.
        port_list: ttk.Combobox
            The tkinter widget used to be portlist.

        Returns nothing.
        """
        refresh_ports = tk.Button(control_frame, text="Refresh Portlist?",
                                  command=lambda: self.init_port_list(
                                      control_frame, port_list))
        refresh_ports.grid(row=1, column=3)
        self._refresh_but = refresh_ports
        return

    def inside_port_write(self, message):
        """Function trys to write a message to the firmware connection. If the
        write fails due to a closed port, a message will be print to the user.
        Parameters
        ----------
        message : str
            The message to send to firmware.
        Returns nothing.
        """
        try:
            self._port.write(message.encode("utf-8"))

        except ser.SerialException:
            print(f"lock status {lock.locked()}")
            print(f"Failed to send {message}!")
            self._prev_error = True

    def connect_to_firm(self, port_items: list):
        """Takes in the selected port from user and starts up connection
        to the firmware. Also starts up the reader thread.
        Parameters
        ----------
        port_items : list
            A list of various thingsm including:
            -   a default ser.Serial object, not connected to anything.
            -   tk.Frame where the port_list and refresh button are
                located within.
            -   a port_list variable (as described in earlier functions).

        Returns the ser.Serial port connection (after connection) if the
        connection is succesful. Othewise, an error is thrown and printed in
        the terminal, and function returns a faulty ser.Serial (which is then
        refreshed by the user).
        """
        port = port_items[0]
        port_list = port_items[2]

        if port_list:
            try:
                print("going...")
                port = ser.Serial(port_list.get(), baudrate=BAUDRATE,
                                  timeout=0.1)
            except (ser.SerialException, ser.SerialTimeoutException):
                make_error_pannel(self._root,
                                  "Invalid Port Connection, "
                                  "please refresh and try another.",
                                  self._program_running)
                return
            # Now we have to code here, where it detects person writing code,
            # and then reads in it when it
            # needs to be read in.

        self._port = port
        self._protocol = st.ReaderThread(
            self._port,
            lambda x=self._root: WriteLines(self.get_firmware_message, x))
        self._protocol.start()

        # Initiate graphs to be ready to plot data.
        self._data._ready_to_plot = 1
        self._data._start_time = time.time()
        self._live_graph.clear_graphs()

        # If a previous error has occured, send a message to Firmware to get
        # starting data.
        if self._prev_error:
            lock.acquire()
            message = "STOP CONT#"
            self.inside_port_write(message)
            self._prev_error = True
            lock.release()

        # Send a message to the firmware to say GUI has started connection.
        lock.acquire()
        self.inside_port_write(STARTCONTMESSAGE)
        lock.release()

        return port

    # Properties are used because it is bad to access private variables
    @property
    def port(self):
        return self._port

    @property
    def root(self):
        return self._root


def write_to_port(port_struct: Port, message: str):
    """Function trys to write a message to the firmware connection. If the
    write fails due to a closed port, function closes the LineReader thread.
    Parameters
    ----------
    port_struct: Port
        An instance of the custom Port class used to communicate with the
        firmware.
    message : str
        The message to send to firmware.
    Returns nothing.
    """
    serial_con = port_struct.port

    # Attempt to write to the port, if it is open.
    if serial_con:
        if serial_con.is_open:
            try:
                serial_con.write(message.encode("utf-8"))
                serial_con.flush()
                print(f"mess: {message}")
                return

            except ser.SerialException:
                print(f"Failed to send mess: {message}")
                # Killing the reader protocol.
                port_struct._protocol.close()
                port_struct._protocol.join()
                make_error_pannel(port_struct._root, "Port Connection Lost.",
                                  port_struct._program_running)


def setup_channel_controls(control_frame: tk.Frame, graph: Graph) -> None:
    """Function makes a frame for graph controls within the main GUI screen.
    Also adds in graph on/off controls into this frame.
    Parameters
    ----------
    control_frame: tk.Frame
        Where all the graph channel controls are located.
    graph: Graph
        Custom Graph class that has stores all relevant graph infromation.
    Returns nothing.
    """
    # Buffer space
    tk.Label(control_frame, text=" ").grid(row=2)

    tk.Label(control_frame, text="Channel Display and Alarm Statuses",
             font=(GUI_FONT, 12)).grid(row=3, columnspan=4)

    # Graph on/off buttons.
    check_button_frame = tk.Frame(control_frame, bd=4, bg="green")
    tk.Checkbutton(check_button_frame, text=V_TITLE,
                   variable=graph.show_graph_volt,
                   command=lambda t="V": graph.toggle_graph(t)).grid(padx=5,
                                                                     pady=1)
    tk.Checkbutton(check_button_frame, text=A_TITLE,
                   variable=graph.show_graph_accel,
                   command=lambda t="A": graph.toggle_graph(t)).grid(padx=5,
                                                                     pady=1)
    tk.Checkbutton(check_button_frame, text=T_TITLE,
                   variable=graph.show_graph_temp,
                   command=lambda t="T": graph.toggle_graph(t)).grid(padx=5,
                                                                     pady=1)
    check_button_frame.grid(row=6, columnspan=4)


class Replay:
    """Class is used to handle replay functionality within the GUI."""

    def __init__(self, control_frame: tk.Frame, data: Data,
                 port_struct: Port) -> None:
        """
        Parameters
        ----------
        control_frame: tk.Frame
            Where all the replay controls and graphs are located.
        data: Data
            Custom Data class that will be used to plot the replayed
            graph results.
        """
        # Set replaying to OFF by default.
        self._replaying = OFF
        self._port_info = port_struct
        self._port = port_struct.port

        self._data = data
        self._graph_data = [[] for _ in range(9)]
        control_frame.columnconfigure(0, weight=1)
        control_frame.rowconfigure(1, weight=1)
        self._replay_but = tk.Button(control_frame, text="Open CSV File",
                                     bg="gray", command=self.read_csv_file)

        self._replay_but.grid(row=0, column=0)
        self._stop_but = tk.Button(control_frame, text="Stop Replaying",
                                   bg="gray", state="disabled",
                                   command=self.stop_replay)
        self._stop_but.grid(row=0, column=1)
        self._graph = None

        self._graphs_on_bot = tk.Frame(control_frame)
        self._graphs_on_bot.columnconfigure(0, weight=1)
        self._graphs_on_bot.rowconfigure(0, weight=1)
        self._graph_frame = create_scrollable_frame(self._graphs_on_bot)
        self._graphs_on_bot.grid(row=1, column=0, sticky="nsew")

    def read_csv_file(self):
        """
        Function reads a csv file of the users choice, and plots the relevant
        data onto the graphs. If the wrong file was selected, or there was a
        issue with the dataset, function returns premptively. Either way,
        returns nothing.
        No Parameters.
        """
        filepath = filedialog.askopenfilename(title="Open CSV file",
                                              initialdir=os.getcwd(),
                                              filetypes=FILE_TYPES
                                              )
        data_to_plot = {}
        if not filepath:
            return
        file = open(filepath, "r")
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            return  # Files with incorrect format

        # Headers of the dictionary
        for header in reader.fieldnames:
            data_to_plot[header] = []

        try:
            first_row = next(reader)
        except StopIteration:
            return  # Files with incorrect format

        start_time = datetime.strptime(
            first_row["Time"], "%Y-%m-%d_%H-%M-%S.%f")
        start_time = start_time.timestamp()
        data_to_plot["Time"].append(0.0)
        for header, value in first_row.items():
            if header != "Time":
                data_to_plot[header].append(float(value))

        for row in reader:
            time_dt = datetime.strptime(row["Time"], "%Y-%m-%d_%H-%M-%S.%f")
            diff = time_dt.timestamp() - start_time
            data_to_plot["Time"].append(diff)
            for header, value in row.items():
                if header != "Time":
                    data_to_plot[header].append(float(value))

        temp_data = [[] for _ in range(9)]
        headers = []

        channel_num = 1
        for header, channel_data in data_to_plot.items():
            if header == "Time":
                temp_data[0] = channel_data
                headers.append("RPMODE")
            else:
                headers.append(header)
                temp_data[channel_num] = channel_data
                channel_num += 1
        self._graph = Graph(self._graph_frame, (V_TITLE, A_TITLE, T_TITLE),
                            (VOLT_Y_LABEL, ACCEL_Y_LABEL, TEMP_Y_LABEL))
        self._graph.add_to_plot(temp_data, headers)
        self._stop_but.config(state="active")
        message = "RPY ON#"
        write_to_port(self._port_info, message)
        self._replaying = ON

    def stop_replay(self):
        print("hi")
        # message = "STOP CONT"
        # write_to_port(self._port_info, message)
        message = "START CONT#"
        write_to_port(self._port_info, message)
        # Make graphs diseapear.
        self._graph.show_graph_accel.set(value=False)
        self._graph.show_graph_volt.set(value=False)
        self._graph.show_graph_temp.set(value=False)
        self._graph.toggle_graph("V")
        self._graph.toggle_graph("A")
        self._graph.toggle_graph("T")

        # Vanish textbox.
        self._graph._text_box.delete(0, tk.END)

        self._graph._graphs_canvas.draw()

        # Stopping user from stopping refresh twice.
        self._stop_but.config(state="disabled")

        self._replaying = OFF
        print("finished replay.")
        pass


def isfloat(input_str: str):
    """Function tries to find if the string entered is a positive or negative
    float. Returns 1 if a positive float, 2 if negative float, 0 if not."""
    try:
        float(input_str)
    except ValueError:
        # Checks if negative.
        try:
            float(input_str[1:])
        except ValueError:
            return 0
        if input_str[0] == "-":
            return 2
        return 0
    return 1


def get_num(input_str: str) -> float | str:
    """Input is a string, output is either a float.
    Returns "Fail" if there's an error."""
    if input_str == "":
        return "EMPTY"
    elif isfloat(input_str) == NEGATIVE:
        return round(float(input_str[1:]), 3) * -1
    elif isfloat(input_str) == POSITIVE:
        return round(float(input_str), 3)
    elif (input_str[0] == "-") and (input_str[1:].isdigit()):
        return float(input_str[1:]) * -1
    elif input_str.isdigit():
        return float(input_str)
    else:
        print("Number is not a float or integer")
        return "Fail"


def determine_channel(channel_str) -> int:
    """Returns the index as an int of each channel.
    Returns -1 if invalid channel is given
    Valid channels are from 1 to 4. This function is for rtemp."""
    match channel_str:
        case "CH1":
            ch_num = 1
        case "CH2":
            ch_num = 2
        case "CH3":
            ch_num = 3
        case "CH4":
            ch_num = 4
        case _:  # Anything else
            ch_num = -1
    return ch_num


class Settings:
    # Defines extra settings a user can implement for the task.
    def __init__(self, frame: ttk.Frame, notebook: ttk.Notebook,
                 port_struct: Port,
                 live_graphs: Graph, data: Data, control_frame: tk.Frame):
        """
        Parameters
        ----------
        frame: ttk.Frame
            The frame where the Settings go.
        notebook: ttk.Notebook
            The notebook is used to enable and disable the settings frame
        port_struct: Port
            Custom Port class used to maintain communication between GUI and
            firmware.
        live_graphs: Graph
            Custom graph class used to plot and store all Graph information.
        data: Data
            Custom Data class used to maintain the data recieved from the
            firmware.
        control_frame: tk.Frame
            Frame where all the graph on/off controls and voltage scaling
            controls is located.
        """
        self._live_graphs = live_graphs
        self.notebook = notebook
        self._data = data
        self._port = port_struct
        self._frame = frame
        self._alarmess_frame = control_frame

        # Heat variables
        self._amps = [None, None]
        self._sensor = [None, None]
        self._rtemp_channels = [None, None]
        self._combo_boxes = [[], []]

        # Scaling Variables
        # This variable allows a user to set the lower and
        # upper limits of the yaxis.
        self._low_yaxis_scaling = [
            tk.StringVar(value="-10"), tk.StringVar(value="-10"),
            tk.StringVar(value="0")]
        self._high_yaxis_scaling = [
            tk.StringVar(value="10"), tk.StringVar(value="10"),
            tk.StringVar(value="30")]

        self._lower_alarms = [tk.StringVar(), tk.StringVar(), tk.StringVar(),
                              tk.StringVar(),
                              tk.StringVar(), tk.StringVar(), tk.StringVar(),
                              tk.StringVar()]
        self._upper_alarms = [tk.StringVar(), tk.StringVar(), tk.StringVar(),
                              tk.StringVar(),
                              tk.StringVar(), tk.StringVar(), tk.StringVar(),
                              tk.StringVar()]

        self._alarm_modes = [tk.IntVar(value=DISABLED),
                             tk.IntVar(value=DISABLED),
                             tk.IntVar(value=DISABLED),
                             tk.IntVar(value=DISABLED),
                             tk.IntVar(value=DISABLED),
                             tk.IntVar(value=DISABLED),
                             tk.IntVar(value=DISABLED),
                             tk.IntVar(value=DISABLED)]

        self._alarm_labels = []

        self.generate_alarmode_labels()
        # Create all the panels
        self.rtemp_pannel()
        self.set_alarms()
        self.set_no_points()

    def rtemp_switch_on(self, channel: int, current: str, sensor: str):
        """Switches on Current Source and Thermistor settings if and only if
        the voltage channel has been set as a resistive temperature channel.
        Parameters
        ----------
        :param sensor: "THERMISTOR" or "PT1000"
        :param current: "200uA" or "10uA"
        :param channel: CH1 to CH4 inclusive
        """
        if channel in VOLT_CHANNELS:
            print(f"Turning on {channel}")
            self._data.toggle_rtemp_mode(channel, current, sensor)
            print("changed data")
            self._live_graphs.move_line(channel, to_temp=True)
            print("Changed live line")

    def rtemp_switch_off(self, channel: int):
        """Converts a temperature channel to a voltage channel.
        Parameters
        ----------
        :param channel: must be between 1 and 4 inclusive
        """
        if channel in VOLT_CHANNELS:
            self._data.toggle_rtemp_mode(channel, "OFF", "OFF")
            self._live_graphs.move_line(channel, to_temp=False)

    def check_rtemp_combobox(self, selection, index: int):
        """Function ensures that only there are only 2 thermistors/RTDs and
        current sources of different types. Returns nothing, but will return
        prematurely if somehow, the user is allowed to select 2 of the same
        current source/thermistor or RTD.
        Parameters
        ----------
        :param selection: what the user selected from the text box
        :param index: 0 is for the first row of combo boxe, 1 is for the
        second row
        """
        # Check if the selection is valid, if not valid return.
        if selection in CHANNELS_RTEMP:
            self._rtemp_channels[index] = selection
        elif selection in CURRENTS_RTEMP:
            self._amps[index] = selection
        elif selection in SENSOR_RTEMP:
            self._sensor[index] = selection
        else:
            return
        # Extract the information from the selected row
        channel = self._rtemp_channels[index]
        current = self._amps[index]
        sensor = self._sensor[index]
        # Find the index of the other row. There are only 2 rows.
        opposite_index = 1 if index == 0 else 0
        # If the same value occurs in the opposite row, reset the entire row.
        # Ensure that the line isn't cleared when doing so.
        if (channel == self._rtemp_channels[opposite_index]
                and channel is not None):
            self.reset_rtemp_comboboxes(index, clear_line=False)
            return
        if current == self._amps[opposite_index] and current is not None:
            self.reset_rtemp_comboboxes(index, clear_line=False)
            return
        if sensor == self._sensor[opposite_index] and sensor is not None:
            self.reset_rtemp_comboboxes(index, clear_line=False)
            return
        # Convert channel from a string to an int
        ch_num = determine_channel(channel)

        if channel is not None and current is not None and sensor is not None:
            print(
                f"Change channel {channel} to a rTemp with current {current} "
                f"and sensor {sensor}"
            )
            for combo_box in self._combo_boxes[index]:
                # The only way to edit it is by resetting
                combo_box.config(
                    state=tk.DISABLED)
            self.rtemp_switch_on(ch_num, current, sensor)

    def rtemp_pannel(self):
        """Sets user up with Resistive Temperature Control Settings, within the
        control settings pannel.
        No input parameters.
        Returns nothing.
        """
        # Resets our buttons.
        self._combo_boxes = [[], []]
        self._amps = [None, None]
        self._sensor = [None, None]
        self._rtemp_channels = [None, None]
        # Create a the frame for the tk widgets
        pannel = tk.Frame(self._frame)
        pannel.grid(row=0, column=0)
        # Setting Labels for the resistive settings.
        tk.Label(pannel,
                 text="Resistive Temperature Settings",
                 font=(GUI_FONT, 17)).grid(row=0, sticky="N", columnspan=4)
        tk.Label(pannel, text="Channel", font=(GUI_FONT, 14)).grid(row=1,
                                                                   column=0)
        tk.Label(pannel, text="Current", font=(GUI_FONT, 14)).grid(row=1,
                                                                   column=1)
        tk.Label(pannel, text="Sensor ", font=(GUI_FONT, 14)).grid(row=1,
                                                                   column=2)

        for i in range(2):
            # The Combobox for selecting the channel
            combo_ch = ttk.Combobox(pannel, values=CHANNELS_RTEMP[1:],
                                    state="readonly")
            combo_ch.set(CHANNELS_RTEMP[0])
            combo_ch.bind("<<ComboboxSelected>>",
                          lambda e, j=i: self.check_rtemp_combobox(
                              e.widget.get(), j))
            combo_ch.grid(row=2 + i, column=0)
            self._combo_boxes[i].append(combo_ch)
            # The Combobox for selecting current
            combo_curr = ttk.Combobox(pannel, values=CURRENTS_RTEMP[1:],
                                      state="readonly")
            combo_curr.set(CURRENTS_RTEMP[0])
            combo_curr.bind("<<ComboboxSelected>>",
                            lambda e, j=i: self.check_rtemp_combobox(
                                e.widget.get(), j))
            combo_curr.grid(row=2 + i, column=1)
            self._combo_boxes[i].append(combo_curr)
            # The Combobox for selecting the sensor
            combo_sens = ttk.Combobox(pannel, values=SENSOR_RTEMP[1:],
                                      state="readonly")
            combo_sens.set(SENSOR_RTEMP[0])
            combo_sens.bind("<<ComboboxSelected>>",
                            lambda e, j=i: self.check_rtemp_combobox(
                                e.widget.get(), j))
            combo_sens.grid(row=2 + i, column=2)
            self._combo_boxes[i].append(combo_sens)
            # The button for resetting the channel
            reset_button = tk.Button(pannel, text="Reset",
                                     command=lambda idx=i:
                                     self.reset_rtemp_comboboxes(idx))
            reset_button.grid(row=2 + i, column=3)
        return

    def reset_rtemp_comboboxes(self, index: int, clear_line: bool = True):
        """This function is used to reset the comboboxes that change a voltage
        line to a temperature channel.
        Parameters
        ----------
        index : int
            index is 0 or 1. It will fail if anything eles is given
        clear_line : bool
            if clear line is true the line will be removed from plot
        """
        channel_old = self._combo_boxes[index][0].get()
        amps_old = self._combo_boxes[index][1].get()
        sensor_old = self._combo_boxes[index][2].get()
        channel_int = determine_channel(channel_old)
        for combo_idx, combo_box in enumerate(self._combo_boxes[index]):
            if combo_idx == 0:
                combo_box.set(CHANNELS_RTEMP[0])
            elif combo_idx == 1:
                combo_box.set(CURRENTS_RTEMP[0])
            else:
                combo_box.set(SENSOR_RTEMP[0])
        self._rtemp_channels[index] = None
        self._amps[index] = None
        self._sensor[index] = None

        for c_box in self._combo_boxes[index]:
            c_box.config(state="readonly")
        # if any of the combobox values are null, exit the function
        if (channel_old == CHANNELS_RTEMP[0]) or (
                amps_old == CURRENTS_RTEMP[0]) or (
                sensor_old == SENSOR_RTEMP[0]):
            return
        # Clear the line
        if clear_line:
            self.rtemp_switch_off(channel_int)

    def check_yscale_input(self, setting: str, idx: int):
        """Function checks the ysacle input to make sure it is valid (i.e
        lower number is smaller than upper number).
        Parameters
        ----------
        setting: str
            Indicates whether the lower or upper yscale value has been
            modified.
        idx: int
            Integer indicating which graph the number of points is modifying.

        Returns nothing, but will print a message to the terminal if the lower
        setting is higher than the upper setting.
        """
        # Grabs the current lower and upper yscale settings.
        lower = get_num(self._low_yaxis_scaling[idx].get())
        upper = get_num(self._high_yaxis_scaling[idx].get())
        if lower == "Fail" or upper == "Fail":
            print("failed")
            (self._low_yaxis_scaling[idx]).set(value="-10")
            (self._high_yaxis_scaling[idx]).set(value="10")
            self._live_graphs.set_lower_limit(idx, -10.0)
            self._live_graphs.set_upper_limit(idx, 10.0)

        # Double check entered thresholds are ok.
        elif (lower != "EMPTY") and (upper != "EMPTY"):
            if lower >= upper:
                print("Upper limit must be more than lower limit.")
                if setting == "lower":
                    (self._low_yaxis_scaling[idx]).set(
                        self._live_graphs._lower_limit[idx])
                else:
                    (self._high_yaxis_scaling[idx]).set(
                        self._live_graphs._upper_limit[idx])
                return
            self._live_graphs.set_upper_limit(idx, upper)
            self._live_graphs.set_lower_limit(idx, lower)
        else:
            # To ensure "Empty" isn't put in empty boxes.
            if lower != "EMPTY":
                (self._low_yaxis_scaling[idx]).set(value=lower)
                print(lower)
                self._live_graphs.set_lower_limit(idx, lower)
            if upper != "EMPTY":
                (self._high_yaxis_scaling[idx]).set(value=upper)
                self._live_graphs.set_upper_limit(idx, upper)

    def _change_points_on_graphs(self, new_value: str):
        """Changes the number of points on the x-axis.
        Ensures the length of data is less than or equal to new_value.
        Parameters
        ----------
        new_value: str
            Indicates whether the new number of points to be displayed on the
            x axis.
        Returns nothing.
        """
        Graph.num_data_points = int(new_value)

    def set_no_points(self):
        """Function opens a new Toplevel used to configure the number of points
        on the xaxis, and the scale of the yaxis graphs.
        No input Parameters.
        Returns nothing, but will print a message to the terminal if the user
        has incorrectly inputed one of the x/yaxis scaling parameters.
        """

        pannel = tk.Frame(self._frame)
        pannel.grid(row=2, column=0)
        # Make the xaxis scaling widget.
        # Using self_no_points to remember values.
        tk.Label(pannel, text="No of Points Visible on Graphs",
                 font=(GUI_FONT, 17)).grid(row=0, column=1, sticky=tk.N)
        tk.Scale(pannel, from_=10, to_=1000, orient=tk.HORIZONTAL,
                 command=self._change_points_on_graphs).grid(row=1, column=1)

        for i in range(3):
            # Defining units to go next to scaling variables.
            if not i:
                unit = "V"
                channel_type = "Voltage"
            elif i == 1:
                unit = "m/s^2"
                channel_type = "Accel"
            else:
                unit = "C"
                channel_type = "Temp"

            tk.Label(pannel, text=f"Lower {channel_type} Y Limit").grid(
                row=3 + i, column=0)
            tk.Label(pannel, text=unit).grid(row=3 + i, column=2)
            tk.Label(pannel, text=f"Upper {channel_type} Y Limit").grid(
                row=3 + i, column=3)
            tk.Label(pannel, text=unit).grid(row=3 + i, column=4)

            # Make the tkinter Entry widgets to store the yaxis scaling
            # variables.
            lower_scaling = tk.Entry(
                pannel, textvariable=self._low_yaxis_scaling[i])
            lower_scaling.bind("<Return>",
                               lambda event, idx=i: self.check_yscale_input(
                                   "lower", idx))
            lower_scaling.grid(row=3 + i, column=1)

            upper_scaling = tk.Entry(
                pannel, textvariable=self._high_yaxis_scaling[i])
            upper_scaling.bind("<Return>",
                               lambda event, idx=i: self.check_yscale_input(
                                   "upper", idx))
            upper_scaling.grid(row=3 + i, column=3)

        return

    def check_alarm_input(self, alarm_th: str):
        """Check to make sure the input alarm thershold fields are valid (i.e.
        lower alarm is smaller than higher alarm).
        Parameters
        ----------
        alarm_th: str
            Indicates which alarm threshold has been changed by the user.
        Returns nothing.
        """
        print(f"string: {alarm_th}")
        for i in range(8):
            # Checks if the lower and upper alarms are integers.
            lower = get_num(self._lower_alarms[i].get())
            upper = get_num(self._upper_alarms[i].get())
            if lower == "Fail":
                (self._lower_alarms[i]).set(value="")
                continue
            elif upper == "Fail":
                (self._upper_alarms[i]).set(value="")
                continue
            elif (lower != "EMPTY") and (upper != "EMPTY"):
                if (upper <= lower):
                    # Set inputed alarm to EMPTY given the error.
                    if alarm_th[0:5] == "lower":
                        (self._lower_alarms[i]).set(value="")
                        (self._upper_alarms[i]).set(value=upper)
                    else:
                        (self._upper_alarms[i]).set(value="")
                        (self._lower_alarms[i]).set(value=lower)
                    print("Upper limit must be more than lower limit.")
                    continue
            # Send the corresponding succesful alarm threshold to firmware.
            if (alarm_th[0:5] == "lower") and (int(alarm_th[6]) == i):
                (self._lower_alarms[i]).set(value=lower)
                write_to_port(self._port, f"ALT CH{i + 1} {lower}#")
            elif (alarm_th[0:5] == "upper") and (int(alarm_th[6]) == i):
                (self._upper_alarms[i]).set(value=upper)
                write_to_port(self._port, f"AHT CH{i + 1} {upper}#")
        return

    def set_alarms(self):
        """Initializes alarm top level inputs section, and allows a user to
        change the alarm modes, and alarm thresholds on the GUI.
        No input parameters.
        Returns nothing.
        """

        alarm_frame = tk.Frame(self._frame)

        alarm_frame.grid(row=1, column=0)

        tk.Label(alarm_frame, text="Alarm Threshold Settings", font=(
            GUI_FONT, 17)).grid(row=0, columnspan=4, sticky="N")
        tk.Label(alarm_frame, text="Alarm Modes", font=(
            GUI_FONT, 13)).grid(row=6, columnspan=12, sticky="N")
        alarm_status_row = 7

        # Setting Radio buttons for the current source.
        for i in range(8):
            # Specifies which alarms go in which column/row.
            if i < 4:
                lo_alarm_row = 1
                hi_alarm_row = 4
                unit = "V"
                alarm_status_row = 7 if i < 3 else 8
            else:
                if i == 7:
                    unit = "C"
                else:
                    unit = "m/s^2"
                lo_alarm_row = 2
                hi_alarm_row = 5
                alarm_status_row = 8 if i < 6 else 9

            # Initlises the low and high alarm threshold entries.
            tk.Label(
                alarm_frame, text=f"Low Alarm ch{i + 1}").grid(
                    row=lo_alarm_row, column=(3*i) % 12)

            lower_alarm = tk.Entry(
                alarm_frame, textvariable=self._lower_alarms[i])
            lower_alarm.bind("<Return>",
                             lambda x, index=i: self.check_alarm_input(
                                 f"lower {index}"))
            # Places alarm appropriatley on grid.
            lower_alarm.grid(row=lo_alarm_row, column=(3 * i) % 12 + 1)
            tk.Label(alarm_frame, text=unit).grid(
                row=lo_alarm_row, column=(3 * i) % 12 + 2)

            # Empty Space.
            tk.Label(alarm_frame, text="   ").grid(row=3)

            tk.Label(
                alarm_frame, text=f"High Alarm ch{i + 1}").grid(
                row=hi_alarm_row, column=(3 * i) % 12)
            upper_alarm = tk.Entry(
                alarm_frame, textvariable=self._upper_alarms[i])
            upper_alarm.bind("<Return>",
                             lambda x, index=i: self.check_alarm_input(
                                 f"upper {index}"))

            upper_alarm.grid(row=hi_alarm_row, column=(3 * i) % 12 + 1)
            tk.Label(alarm_frame, text=unit).grid(
                row=hi_alarm_row, column=(3 * i) % 12 + 2)

            # Initialises the alarm modes for all channels.
            tk.Label(alarm_frame, text=f"Alarm Mode ch{i + 1}").grid(
                row=alarm_status_row, column=(4 * i) % 12)
            tk.Radiobutton(alarm_frame, text="Disabled",
                           variable=self._alarm_modes[i], value=DISABLED,
                           command=lambda index=i: self.handle_alarmmode(
                               index, "Disabled")
                           ).grid(row=alarm_status_row, column=(4 * i
                                                                ) % 12 + 1)
            tk.Radiobutton(alarm_frame, text="Live",
                           variable=self._alarm_modes[i], value=LIVE,
                           command=lambda index=i: self.handle_alarmmode(
                               index, "Live")
                           ).grid(row=alarm_status_row, column=(4 * i
                                                                ) % 12 + 2)
            tk.Radiobutton(alarm_frame, text="Latching",
                           variable=self._alarm_modes[i], value=LATCHING,
                           command=lambda index=i: self.handle_alarmmode(
                               index, "Latching")
                           ).grid(row=alarm_status_row, column=(4 * i
                                                                ) % 12 + 3)

    def handle_alarmmode(self, channel: int, mode: str):
        """Function updates the alarm modes on the main screen and shares
        these changes with firmware.
        Parameters
        ----------
        channel: int
            Indicates which channel has been changed.
        mode: str
            Indicates the new alarm mode.
        Returns nothing.
        """
        # Refresh the main screen alarm labels.
        (self._alarm_labels[channel]).config(
            text=f"  Alarm Mode CH{channel + 1}: {mode}  ")
        # Send a message to firmware.
        if mode == "Disabled":
            write_to_port(self._port, f"AM CH{channel + 1} {DISABLED}#")
        elif mode == "Live":
            write_to_port(self._port, f"AM CH{channel + 1} {LIVE}#")
        else:
            write_to_port(self._port, f"AM CH{channel + 1} {LATCHING}#")
        return

    def generate_alarmode_labels(self):
        """Function generates default 'Disabled' alarm modes and fills them
        into main screen.
        No input parameters.
        Returns nothing.
        """
        for i in range(8):
            alarm_type = "Disabled"
            alarm_mode = tk.Label(self._alarmess_frame, font=("Bold, 12"),
                                  text=f"  Alarm Mode Ch{i + 1}: {
                                      alarm_type}  "
                                  )
            alarm_mode.grid(row=8 + (i // 4), column=(i % 4))
            self._alarm_labels.append(alarm_mode)

    @property
    def alarm_labels(self):
        """Function is used to access the alarm labels of settings class"""
        return self._alarm_labels

    @property
    def alarm_modes(self):
        """Function is used to access the alarm modes
        (live, disabled, latching) of settings class"""
        return self._alarm_modes

    @property
    def upper_alarms(self):
        """Function is used to access the high alarms of settings class"""
        return self._upper_alarms

    @property
    def lower_alarms(self):
        """Function is used to access the low alarms of settings class"""
        return self._lower_alarms


def create_scrollable_frame(frame: tk.Frame) -> tk.Frame:
    """
    This function creates a frame that has a scroll bar.
    The scrollbar should be on the left hand side of the screen.
    """
    # Create canvas and scrollbar
    canvas = tk.Canvas(frame)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    # Function to resize scroll region
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    # Embed scrollable_frame inside canvas
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Place the scrollbar and canvas
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="nsew")
    return scrollable_frame


def create_alarm_statuses(control_frame: tk.Frame):
    """Creates in the main GUI screen a list of 8 labels representing the
    current alarm statuses, and whether a low threshold or high threshold was
    breached."""
    alarm_statuses = []
    for i in range(8):
        # All alarm statuses are defaulted to Off.
        alarm_status = tk.Label(control_frame, font=(GUI_FONT, 10),
                                text=f"  CH{i + 1} Alarm Status: Off  \n")
        alarm_status.grid(row=4 + i // 4, column=i % 4)
        alarm_statuses.append(alarm_status)

    return alarm_statuses


class Record:
    """Class initiates the record button, and allows the user to record their
    measurements, and save them to a csv file.
    """

    def __init__(self, control_frame: tk.Frame, clear_graphs: tk.Button,
                 replay: Replay, port_struct: Port, setting: Settings,
                 voltage_buttons: list, data: Data):
        """
        Parameters
        ----------
        control_frame: tk.Frame
            Where the record button is located.
        port_struct: Port
            Custom Port class used to maintain communication between GUI and
            firmware.
        setting: Settings
            Custom Settings class used to maintain all the GUI widgets
            effecting sensor measurement, alarms etc.
        voltage_buttons: list
            List of the tk.Buttons controlling the voltage scaling (1, 10V).
        data: Data
            Custom Data class used to maintain the data recieved from the
            firmware.
        """
        self._status = 0  # Set record button to off by default.
        self._controls = control_frame
        self._port = port_struct
        self._data = data
        self._record_but = tk.Button(control_frame, text="Record?",
                                     bg="gray", command=self.record_switch)
        self._record_but.grid(row=1, column=0)
        self._setting = setting
        self._vbuttons = voltage_buttons
        self._replay = replay
        self._clear_graphs = clear_graphs

    def record_switch(self):
        """
        Function is used to switch off all buttons, widgets etc. that are
        configurable parameters when recording is on, and switch them on
        when recording is off.
        No input parameters.
        Returns nothing.
        REF: https://stackoverflow.com/questions/20983309/
             how-to-enable-disable-tabs-in-a-tkinter-tix-python-gui
        """
        # If finished recording:
        if self._status:
            # Activate all controls turned off.
            self._record_but.config(text="Record?", bg="gray")
            print("Saved")
            # Save data as csv file.
            self._data.save_data()
            self._status = 0
            self._setting.notebook.tab(1,
                                       state=tk.NORMAL
                                       )  # REF see function header
            # Activate V buttons.
            for i in range(2):
                self._vbuttons[i].config(state="active")

            self._replay._replay_but.config(state="active")
            self._port._port_list['state'] = "readonly"
            self._clear_graphs.config(state="active")
            self._port._refresh_but.config(state="active")

            # Send message to firmware allowing user to change V scaling.
            write_to_port(self._port, "REC OFF#")

        # Disable all configurale parameters, and record.
        else:
            if self._port.port.is_open:
                self._record_but.config(text="Recording!!!", bg="red")
                self._data.record()
                self._status = 1
                self._setting.notebook.tab(1,
                                           state=tk.DISABLED
                                           )  # REF see function header
                # self._setting._menu.entryconfig("Settings", state="disabled")
                for i in range(2):
                    self._vbuttons[i].config(state="disabled")

                self._replay._replay_but.config(state="disabled")
                self._port._port_list['state'] = "disabled"

                self._clear_graphs.config(state="disabled")
                self._port._refresh_but.config(state="disabled")

                write_to_port(self._port, "REC ON#")
            elif self._replay._replaying == ON:
                make_error_pannel(self._controls,
                                  "Please finish replaying before recording.",
                                  self._port._program_running)
            else:
                make_error_pannel(self._controls,
                                  "Can't record without connection to board.",
                                  self._port._program_running)


def gui_close(root: tk.Tk, port: Port):
    """
    Function closes the window, and any ongoing threads when the user closes
    the GUI.
    Parameters
    ----------
    root: tk.Tk
        Main window of the GUI.
    port: Port
        Custom Port classed used to communication with firmware.
    """

    # Stop firmware from sending anymore messages through port.
    if port and port._port:
        message = "STOP CONT#"
        write_to_port(port, message)
    root.destroy()

    if port._protocol and port._protocol.is_alive():
        port._protocol.stop()
        port._protocol.close()
        port._protocol.join()

    if port and port._err_thread:
        port._program_running = False
        if port._err_thread.is_alive():
            if errors.empty():
                errors.put("Ending Program")
            port._err_thread.join()

    sys.exit()


def main() -> None:
    # Setup
    root = tk.Tk()  # initialise the window
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry(f"{width}x{height}")
    root.title("Data Acquisition Device")
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    # notebook, where all the tabs go
    notebook = ttk.Notebook(root)
    notebook.grid(row=0, column=0, sticky="nsew")
    # The tabs on the GUI
    controls_tab = ttk.Frame(notebook)
    setting_tab = ttk.Frame(notebook)
    graphs_tab = ttk.Frame(notebook)
    replay_tab = ttk.Frame(notebook)
    # Adding to notebook
    notebook.add(controls_tab, text="Controls")
    notebook.add(setting_tab, text="Settings")
    notebook.add(graphs_tab, text="Live Graphs")
    notebook.add(replay_tab, text="Replay")
    # Graphs
    graphs_tab.rowconfigure(0, weight=1)
    graphs_tab.columnconfigure(0, weight=1)
    graph_scroll_frame = create_scrollable_frame(graphs_tab)
    # Voltage
    live_graph = Graph(graph_scroll_frame,
                       (V_TITLE, A_TITLE, T_TITLE),
                       (VOLT_Y_LABEL, ACCEL_Y_LABEL, TEMP_Y_LABEL))

    loggy_data = Data(0)  # 0 indicates it's not yet ready to plot data.
    live_graph.add_live_plot(CHANNELS_LIST, loggy_data)

    # Controls
    tk.Label(controls_tab, text="Data Acquisition Device", font=(GUI_FONT, 20),
             bg="lightgray").grid(row=0, column=0, padx=5, pady=5)
    # Used so I can pack all (or most) of the control stuff together.
    control_frame = tk.Frame(controls_tab)
    control_frame.grid(row=1, column=0, sticky="n")
    # Sets up channel specific controls on the main screen.
    setup_channel_controls(control_frame, live_graph)
    # Sets up port connections.
    # First instance of init_port_list, so there are no prevous port lists.
    # Empty widget variable atm just so that
    # future code doesn't through any errors.
    port = Port(control_frame, live_graph, None, [[], [], [], [], [], [], []],
                None)
    # Empty list of lists used to pass initialise for empty widget vars.

    # Sets up the voltage range setting.
    volt_level = tk.IntVar()
    radio_frame = tk.Frame(control_frame)
    radio_frame.grid(row=0, column=0, columnspan=2)
    tk.Label(radio_frame, text="Input Voltage Range: ").grid(row=0, column=0)
    # # is used as an identifer for the firmware code.
    volt1 = tk.Radiobutton(radio_frame, text="+/-1V", variable=volt_level,
                           value=0,
                           command=lambda: write_to_port(port, "V0#"))
    volt1.grid(row=0, column=1)
    volt2 = tk.Radiobutton(radio_frame, text="+/-10V", variable=volt_level,
                           value=1,
                           command=lambda: write_to_port(port, "V1#"))
    volt2.grid(row=0, column=2)

    clear_graph = tk.Button(
        control_frame, text="Clear Graphs?", command=live_graph.clear_graphs)
    clear_graph.grid(row=1, column=2)

    setting = Settings(setting_tab, notebook, port, live_graph, loggy_data,
                       control_frame)

    # Port has assess to the widget variables that are effected by firmware.
    widget_var = (volt_level, setting.lower_alarms, setting.upper_alarms,
                  setting.alarm_modes, setting.alarm_labels, [])

    # Ensures that the port has non empty versions of each of these after
    # Setting Init.
    port._widget_vars = widget_var
    port._volt_range = volt_level
    port._low_at = setting.lower_alarms
    port._high_at = setting.upper_alarms
    port._alarm_modes = setting.alarm_modes
    port._alarm_mode_label = setting.alarm_labels

    # Sets up a alarm statuses:
    alarm_status_labels = create_alarm_statuses(control_frame)

    port._alarm_statuses = alarm_status_labels

    port._data = loggy_data

    # Replay
    # Sets up replay button.
    replay = Replay(replay_tab, loggy_data, port)

    # Sets up recording button
    Record(control_frame, clear_graph, replay, port, setting, [volt1, volt2],
           data=loggy_data)

    # End
    root.protocol("WM_DELETE_WINDOW", lambda: gui_close(root, port))

    root.mainloop()

    return


if __name__ == "__main__":
    main()


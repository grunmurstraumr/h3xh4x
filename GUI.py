import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter.messagebox import showwarning
from tkinter.scrolledtext import ScrolledText
import os, sys
from PyQt5.QtWidgets import QApplication, QWidget
from configparser import ConfigParser

config = ConfigParser()
config.read('settings.ini')

def hexify(byte):
    """ Returns the hex representation of a char without the 0x part"""
    temp = hex(byte).lstrip('0x') #Turn into hex and strip leading 0x
    while len(temp) < 2:
        temp = '0' + temp
    return temp


class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.minsize(300, 300)
        self.root.geometry('1000x700')

        #Initialize variables
        self.frame_index = 0
        self.frame_count = float('NaN')
        self.data = []
        #self.buffer_size = 2048
        self.current_tab = None #Should point to a selected tab in ttk.Notebook

        #Set up view window
        self.tabbed_views = ttk.Notebook(master=self.root)
        self.view_frame = tk.Frame(master=self.tabbed_views)
        self.hex_window = tk.Text(master=self.view_frame, wrap=tk.WORD)
        self.hex_scroll = tk.Scrollbar(master=self.view_frame,  command=self.hex_window.yview())
        self.text_frame = tk.Frame(master=self.tabbed_views)
        self.text_window = tk.Text(master=self.text_frame, wrap=tk.WORD)
        self.text_scroll = tk.Scrollbar(master=self.text_frame, command=self.text_window.yview())
        self.tabbed_views.add(self.view_frame, text='Hex')
        self.tabbed_views.add(self.text_frame, text='Text')

        #Set up menus
        self.main_menu = tk.Menu(master=self.root)
        self.file_menu = tk.Menu(master=self.main_menu)
        self.file_menu.add_command(label='Load File', command=self.load_file)
        self.file_menu.add_command(label="Save file", command=self.save_file)
        self.main_menu.add_cascade(label='File', menu=self.file_menu)


        #Set up labels
        self.frame_count_label = tk.Label(text="{} of {}".format(self.frame_index, self.frame_count))

        #Set up buttons
        self.nav_button_frame = tk.Frame()
        self.previous_frame_btn = tk.Button(master=self.nav_button_frame, text="Previous frame", command=self._print_previous_frame)
        self.next_frame_btn = tk.Button(master=self.nav_button_frame, text='next frame', command=self._print_next_frame)

        #Pack and position
        self.root.config(menu=self.main_menu)
        self.next_frame_btn.grid(row=0, column=1)
        self.previous_frame_btn.grid(row=0, column=0)
        self.frame_count_label.pack()
        self.nav_button_frame.pack()
        self.tabbed_views.pack()
        self.text_window.grid(row=0, column=0)
        self.text_scroll.grid(row=0, column=0, sticky='nsew')
        self.text_window['yscrollcommand'] = self.text_scroll.set
        self.hex_window.grid(row=0, column=0)
        self.hex_scroll.grid(row=0, column=1, sticky='nsew')
        self.hex_window['yscrollcommand'] = self.hex_scroll.set


    def _update_view(self):
        #Clear editor window
        self.frame_count_label.configure(text="{} of {}".format(self.frame_index+1, self.frame_count))
        self.hex_window.delete('0.0', tk.END)
        #Insert new content
        self.hex_window.insert(tk.END, self.data[self.frame_index])


    def _validate_and_retrieve_data(self):
        return self._validate_data()

    def report_input_error(self):
        """Raises an alert window to inform the user that there is erroneous input"""
        showwarning('Warning', "Invalid input detected. Please check that everything is correct before proceeding")

    def _print_next_frame(self):
        #Check so data is loaded, Do nothing if theres no data
        if not self.data:
            return

        #Save changes made in editor to data.
        try:
            self.data[self.frame_index] = self._validate_and_retrieve_data()
        except ValueError as error:
            self.report_input_error()
            return
        #Increment the frame 'pointer'
        self.frame_index += 1
        #Check if the pointer is past the end and if so reset to begining
        if self.frame_index > len(self.data)-1:
            self.frame_index -= len(self.data)

        self._update_view()

    def _print_previous_frame(self):
        # Check so data is loaded, Do nothing if theres no data
        if not self.data:
            return

        #Save changes made in editor.
        try:
            self.data[self.frame_index] = self._validate_and_retrieve_data()
        except ValueError as error:
            self.report_input_error()
            return
        self.frame_index -= 1
        if self.frame_index < 0:
            #If we move past the first frame, load the last instead
            self.frame_index = len(self.data)-1

        self._update_view()

    def load_file(self):
        filename = filedialog.askopenfilename(initialdir=os.curdir, filetypes=(("All files", "*.*"),("Executable","*.exe"),))
        if filename:
            self.file_cursor_pos = 0
            self.hex_window.delete('0.0', tk.END)
            self.load_file_data(filename)
            self.frame_count_label.config(text='{} of {}'.format(self.frame_index,self.frame_count))
            self._update_view()


    def load_file_data(self, filename: str):
        buffer_size = int(config.get(option='buffer_size', section='FILES', fallback=8192))
        print(buffer_size)
        self.data = []
        self.frame_index = 0
        with open(filename, mode='rb') as file:
            while True:
                chunk = file.read(buffer_size)
                if chunk:
                    self.data.append(chunk)
                else:
                    break
        self.frame_count = len(self.data)
        for index in range(0, self.frame_count):
            self.data[index] = ' '.join([hexify(char) for char in self.data[index]])

        return self.data


    def save_file(self):
        try:
            self.data[self.frame_index] = self._validate_and_retrieve_data()
        except ValueError as error:
            self.report_input_error()
            return
        filename = filedialog.asksaveasfilename(initialdir=os.curdir)
        if filename:
            self._write_file(filename)

    def _validate_data(self):
        """Validates that data retrieved from window is valid hex-data by converting it to bytes. Returns the data
        if it is valid"""
        data = self.hex_window.get('0.0', tk.END)
        bytes.fromhex(data)
        return data

    def _write_file(self, filename):
        with open(filename, mode='wb') as file:
            file.write(bytes.fromhex(''.join([item for item in self.data])))


    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    g = GUI()
    g.run()
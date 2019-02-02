import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter.messagebox import showwarning
from tkinter.scrolledtext import ScrolledText
import os, sys
from PyQt5.QtWidgets import QApplication, QWidget
from configparser import ConfigParser
import re

config = ConfigParser()
config.read('settings.ini')

STRING_ENCODING = config.get('FILES', 'encoding')
if STRING_ENCODING == 'default':
    STRING_ENCODING = sys.getfilesystemencoding()



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
        self.byte_count = 0
        self.frame_index = 0
        self.frame_count = float('NaN')
        self.text_available = True
        self.data = []

        #Set up view window
        self.tabbed_views = ttk.Notebook(master=self.root)
        self.hex_frame = tk.Frame(master=self.tabbed_views)
        self.hex_window = ScrolledText(master=self.hex_frame, wrap=tk.WORD)#tk.Text(master=self.hex_frame, wrap=tk.WORD)
        #self.hex_scroll = tk.Scrollbar(master=self.hex_frame, command=self.hex_window.yview())
        self.text_frame = tk.Frame(master=self.tabbed_views)
        self.text_window = ScrolledText(master=self.text_frame)
        #self.text_scroll = tk.Scrollbar(master=self.text_frame, command=self.text_window.yview())
        self.tabbed_views.add(self.hex_frame, text='Hex')
        self.tabbed_views.add(self.text_frame, text='Text')
        self.tab_id = self.tabbed_views.select()
        self.current_tab = self.hex_window  # Should point to a selected tab in ttk.


        #Set up menus
        self.main_menu = tk.Menu(master=self.root)
        self.file_menu = tk.Menu(master=self.main_menu)
        self.file_menu.add_command(label='Load File', command=self.load_file)
        self.file_menu.add_command(label="Save file", command=self.save_file)
        self.main_menu.add_cascade(label='File', menu=self.file_menu)

        #Bind events
        #Tect window events
        self.text_window.bind('<Visibility>', self._switch_tab)
        self.text_window.bind('<Up>', self._cursor_step_up )
        self.text_window.bind('<Down>', self._cursor_step_down )


        #Hex window events
        self.hex_window.bind('<Visibility>', self._switch_tab)
        self.hex_window.bind('<ButtonRelease-1>', self._update_cursor)
        self.hex_window.bind('<Right>', self._cursor_step_right)
        self.hex_window.bind('<Left>', self._cursor_step_left)
        self.hex_window.bind('<Key>', self._handle_key)
        self.hex_window.bind('<Up>', self._cursor_step_up )
        self.hex_window.bind('<Down>', self._cursor_step_down )



        #Set up labels
        self.byte_number_label = tk.Label(self.root)
        self.error_label = tk.Label(master=self.root, foreground=config.get('PALETTE', 'error_foreground'))
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
        self.error_label.pack()
        self.tabbed_views.pack(fill=tk.BOTH, expand=1)
        self.text_window.pack(fill=tk.BOTH, expand=1)
        self.hex_window.pack(fill=tk.BOTH, expand=1)
        self.byte_number_label.pack()


    def _switch_tab(self, event):
        try:
            self._update_data()
            self.tab_id = self.tabbed_views.select()
            self.current_tab = event.widget
            self._update_view()

        except ValueError:
            self.tabbed_views.select(self.tab_id)
            self.report_input_error()
            return


    def _calculate_byte_number(self, cursor_position):
        buffer_size = int(config.get(option='buffer_size', section='FILES', fallback=8192))
        return (cursor_position[1]//3) + (self.frame_index * buffer_size) + 1

    def _update_cursor(self, event):
        position = [int(i) for i in self.current_tab.index(tk.INSERT).split('.')]
        #Update the byte number display
        self.byte_number_label.configure(text='Byte {} of {}'.format(self._calculate_byte_number(position), self.byte_count))
        #Move cursor to start of byte
        diff = position[1] % 3
        if not diff == 0:
            position[1] -= diff
            self.hex_window.mark_set(tk.INSERT, '.'.join(map(str, position)))


    def _cursor_step_up(self, event):
        position = [int(i) for i in self.current_tab.index(tk.INSERT).split('.')]
        position[0] -= 1
        self.hex_window.mark_set(tk.INSERT, '.'.join(map(str, position)))
        self.byte_number_label.configure(
            text='Byte {} of {}'.format(self._calculate_byte_number(position), self.byte_count))

    def _cursor_step_down(self, event):
        position = [int(i) for i in self.current_tab.index(tk.INSERT).split('.')]
        position[0] += 1
        self.hex_window.mark_set(tk.INSERT, '.'.join(map(str, position)))
        self.byte_number_label.configure(
            text='Byte {} of {}'.format(self._calculate_byte_number(position), self.byte_count))

    def _cursor_step_right(self, event):
        position = [int(i) for i in self.current_tab.index(tk.INSERT).split('.')]
        position[1] += 3
        diff = position[1] % 3
        if not diff == 0:
            position[1] -= diff
        self.hex_window.mark_set(tk.INSERT, '.'.join(map(str, position)))
        self.byte_number_label.configure(text='Byte {} of {}'.format(self._calculate_byte_number(position), self.byte_count))

        return 'break';

    def _cursor_step_left(self, event):
        position = [int(i) for i in self.current_tab.index(tk.INSERT).split('.')]
        position[1] -= 3
        diff = position[1] % 3
        if not diff == 0:
            position[1] -= diff
        self.hex_window.mark_set(tk.INSERT, '.'.join(map(str, position)))
        self.byte_number_label.configure(
            text='Byte {} of {}'.format(self._calculate_byte_number(position), self.byte_count))
        return 'break';

    def _handle_key(self, event):
        position = [int(i) for i in self.current_tab.index(tk.INSERT).split('.')]
        keys = [str(i) for i in range(0, 10)]
        keys.extend(['a', 'b', 'c', 'd', 'e', 'f'])
        if event.char in keys and not self.hex_window.get(tk.INSERT) == ' ':
            self.hex_window.delete(tk.INSERT)
            self.hex_window.insert(tk.INSERT, event.char)
            position[1] += 1
            self.hex_window.mark_set(tk.INSERT, '.'.join(map(str, position)))
        return "break"

    def _update_view(self):
        if not self.data:
            "Early exit if no data is present"
            return
        #Clear editor window
        self.frame_count_label.configure(text="{} of {}".format(self.frame_index+1, self.frame_count))
        self.current_tab.delete('0.0', tk.END)
        #Insert new content
        if self.current_tab is self.hex_window:
            output = self._hexify_output(self.data[self.frame_index])
            self.error_label.config(text="")
        elif self.current_tab is self.text_window:
            output = self._textify_output(self.data[self.frame_index])
            if not self.text_available:
                self.text_window.configure(foreground=config.get("PALETTE", "error_foreground"), wrap=tk.WORD)
                self.error_label.configure(text="Warning, no text representation available. Hex displayed instead.")
            else:
                self.text_window.configure(foreground=config.get('PALETTE', 'standard_foreground'), wrap=tk.CHAR)
                self.error_label.configure(text="")
        else:
            raise RuntimeError
        self.byte_number_label.configure(text='Byte {} of {}'.format(0, self.byte_count))
        self.current_tab.insert(tk.END, output)

    def _update_data(self):
        try:
            self.data[self.frame_index] = self._validate_and_retrieve_data()
        except IndexError: # No data is previously loaded, assume new data is entered
            self.data.append(self._validate_and_retrieve_data())

    def _validate_and_retrieve_data(self):
        if self.current_tab is self.hex_window or not self.text_available:
            return self._validate_hex_data()
        else:
            return self._validate_string_data()

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
            self.current_tab.delete('0.0', tk.END)
            self.load_file_data(filename)
            self.frame_count_label.config(text='{} of {}'.format(self.frame_index,self.frame_count))
            self._update_view()


    def load_file_data(self, filename: str):
        buffer_size = int(config.get(option='buffer_size', section='FILES', fallback=8192))
        self.byte_count = 0
        self.data = []
        self.frame_index = 0
        with open(filename, mode='rb') as file:
            while True:
                chunk = file.read(buffer_size)
                self.byte_count += len(chunk)
                if chunk:
                    self.data.append(chunk)
                else:
                    break
        self.frame_count = len(self.data)
        self.text_available = True
        if self.frame_count == 0:
            #Emty file was read. Append empty bytes object to data
            self.data.append(bytes(''))
        #for index in range(0, self.frame_count):
        #    self.data[index] = ' '.join([hexify(char) for char in self.data[index]])

        return self.data

    def _hexify_output(self, data):
        return ' '.join([hexify(char) for char in data])

    def _textify_output(self, data):
        """Returns the string representation of input data if it can be decoded. Falls back to hexify_output if an error
        occurs. """
        try:
            self.text_available = True
            return data.decode(STRING_ENCODING)
        except Exception:
            self.text_available = False
            return self._hexify_output(data)

    def save_file(self):
        try:
            self.data[self.frame_index] = self._validate_and_retrieve_data()
        except ValueError as error:
            self.report_input_error()
            return
        except IndexError:
            #No data exists in current frame. Append to data
            self.data.append(self._validate_and_retrieve_data())
        filename = filedialog.asksaveasfilename(initialdir=os.curdir)
        if filename:
            self._write_file(filename)

    def _validate_hex_data(self):
        """Validates that data retrieved from window is valid hex-data by converting it to bytes. Returns the data
        if it is valid"""
        data = self.current_tab.get('0.0', tk.END)[:-1] #This returns a newline character at the end, slice to remove
        return bytes.fromhex(data)

    def _validate_string_data(self):
        data = self.current_tab.get('0.0', tk.END)[:-1]
        return bytes(data, STRING_ENCODING)

    def _write_file(self, filename):
        with open(filename, mode='wb') as file:
            file.write(b''.join(self.data))


    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    g = GUI()
    g.run()
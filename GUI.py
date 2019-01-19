import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import os, sys
from PyQt5.QtWidgets import QApplication, QWidget

def hexify(byte):
    """ Returns the hex representation of a char without the 0x part"""
    temp = hex(byte).lstrip('0x') #Turn into hex and strip leading 0x
    while len(temp) < 2:
        temp = '0' + temp
    return temp

def dehexify(stripped_hex):
    """Adds back the 0x to the start of a hex-string. Does nothing because bytes.fromhex used in writing
    back to file uses same format as output"""
    #if stripped_hex[0] == '0':
    #    stripped_hex = stripped_hex.lstrip('0')
    #stripped_hex = '0x' + stripped_hex
    return stripped_hex

class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.hex_window_old = ScrolledText(wrap=tk.WORD)
        self.view_frame = tk.Frame()
        self.hex_window = tk.Text(master=self.view_frame, wrap=tk.WORD)
        self.hex_scroll = tk.Scrollbar(master=self.view_frame,  command=self.hex_window.yview())
        self.load_file_button = tk.Button(text='Load file', command=self.load_file)
        self.save_file_button = tk.Button(text="Save file", command=self.save_file)
        self.frame_index = 0
        self.data = []

        self.nav_button_frame = tk.Frame()
        self.previous_frame_btn = tk.Button(master=self.nav_button_frame, text="Previous frame", command=self._print_previous_frame)

        self.next_frame_btn = tk.Button(master=self.nav_button_frame, text='next frame', command=self._print_next_frame)
        self.next_frame_btn.grid(row=0, column=1)
        self.previous_frame_btn.grid(row=0,column=0)
        self.nav_button_frame.pack()
        self.load_file_button.pack()
        self.save_file_button.pack()
        self.view_frame.pack()
        self.hex_window.grid(row=0, column=0)
        self.hex_scroll.grid(row=0, column=1, sticky='nsew')
        self.hex_window['yscrollcommand'] = self.hex_scroll.set
        self.buffer_size = 2048

    def _update_view(self):
        #Clear editor window
        self.hex_window.delete('0.0', tk.END)
        #Insert new content
        self.hex_window.insert(tk.END, self.data[self.frame_index])

    def _print_first_frame(self):
        self.hex_window.delete('0.0', tk.END)
        self.hex_window.insert(tk.END, self.data[self.frame_index])#' '.join([hexify(char) for char in self.data[self.frame_index]]))

    def _print_next_frame(self):
        #Check so data is loaded, Do nothing if theres no data
        if not self.data:
            return

        #Save changes made in editor to data. WARNING NO CHECKS!!!
        self.data[self.frame_index] = self.hex_window.get('0.0', tk.END)
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

        self.data[self.frame_index] = self.hex_window.get('0.0', tk.END)
        #Save changes made in editor. WARNING NO CHECKS FOR VALID DATA
        self.frame_index -= 1
        if self.frame_index < 0:
            self.frame_index += len(self.data)

        self._update_view()

    def load_file(self):
        filename = filedialog.askopenfilename(initialdir=os.curdir, filetypes=(("Executable","*.exe"),("All files", "*.*")))
        if filename:
            self.file_cursor_pos = 0
            self.hex_window.delete('0.0', tk.END)
            self.load_file_data(filename)
            self._print_first_frame()


    def load_file_data(self, filename: str):
        self.data = []
        self.frame_index = 0
        with open(filename, mode='rb') as file:
            while True:
                chunk = file.read(8192)
                if chunk:
                    self.data.append(chunk)
                else:
                    break
        data_len = len(self.data)
        for index in range(0, data_len):
            self.data[index] = ' '.join([hexify(char) for char in self.data[index]])

        return self.data


    def save_file(self):
        filename = filedialog.asksaveasfilename(initialdir=os.curdir)
        if filename:
            self._write_file(filename)

    def _write_file(self, filename):
        with open(filename, mode='wb') as file:
            file.write(bytes.fromhex(''.join([item for item in self.data])))


    def run(self):
        self.root.mainloop()


class QtGUI():
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = QWidget()
        self.window.resize(250,150)

    def run(self):
        self.window.show()
        return self.app.exec_()

if __name__ == '__main__':
    g = GUI()
    g.run()
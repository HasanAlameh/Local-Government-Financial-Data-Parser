from tkinter import filedialog
from tkinter import *
import tkinter.font as font
from newParse import *
import subprocess, os, platform

ftypes = [
    ('PDF', '*.pdf')
]

def browse_button():
    # Allow user to select a directory and store it in global var
    # called folder_path
    global filename, filePath
    filename = filedialog.askopenfile(filetypes=ftypes)
    filePath = filename.name
    lbl1.config(text=filename.name)
def program_instructions():
    print("=============================USER INSTRUCTIONS================================================")
    print("-  CLOSE THE MASTER CSV FILE PRIOR TO RUNNING THE PROGRAM, program cannot write to an open CSV file.")
    print("-  The program can ONLY handle readable PDF files (not image PDFs, textual only), therefore \nplease check before you feed in the files to the system.")
    print("-  Browse Button - This is used to navigate to your PDF file & get the path.")
    print("-  Submit Button - This is used to initiate the parser.")
    print("-  Open Button - This is used to open the CSV file after the data has been parsed and transferred into it.")
    print("-  NOTE: The CSV file is rewritten everytime the tool is ran, \nwhich means the old data is wiped out and new data is written based on the PDF uploaded.\nTherefore, it's best to save the CSV elsewhere before trying a second run.")
    print("==============================================================================================")
def run_prog():
    # This is your function maitra use the folder_path variable to get filename
    saveCSVfilepath = file_parse(filePath)
    finish_msg = StringVar()
    lbl2 = Label(master = root, textvariable=finish_msg, bg='#FED000', fg='black', font = font.Font(size=15), height= 3, highlightthickness = 0, bd = 0)
    #finish_msg.set("MESSAGE: Your master CSV file is ready, \nClick on 'Open Master CSV' to open it! \n PATH: " + saveCSVfilepath)
    lbl2.pack()

def open_file():
    filepath = 'newOutput.csv'
    if platform.system() == 'Darwin':       # macOS
        subprocess.call(('open', filepath))
    elif platform.system() == 'Windows':    # Windows
        os.startfile(filepath)
    else:                                   # linux variants
        subprocess.call(('xdg-open', filepath))

#Change button color on hover & back again
def btn_on_enter(self):
    self.widget['background'] = '#343434'

def btn_on_leave(self):
    self.widget['background'] = '#424242'

root = Tk()
program_instructions()
myFont = font.Font(size=30)
root.geometry("790x350")
root.configure(bg='#1F1F1F')
root.title("TREASURY DATA PARSER")

frame1 = Frame(bg = '#1F1F1F', height=1)
frame1.pack(fill=X)

lbl1 = Label(frame1,text="No Audit file selected.", bg='#1F1F1F', fg='white', font = 30, height= 2, width = 61,relief="ridge")
lbl1.pack(side=LEFT, padx=5, pady=20)

button2 = Button(frame1, text="Browse", command=browse_button, relief="groove", cursor="hand2")
button2['font'] = font.Font(size = 10)
button2.config(height=2, width = 10)
button2.pack(side=LEFT)

button3 = Button(text="Submit", command=run_prog, bg='#424242', fg='white', activebackground='#343434', activeforeground='white', relief="raised", cursor="hand2") # put your function name in the command option maitra
button3['font'] = myFont
button3.config(height=1, width = 15)
button3.pack(side=LEFT, padx=10)
button3.bind("<Enter>", btn_on_enter)
button3.bind("<Leave>", btn_on_leave)

button4 = Button(text="Open Master CSV", command=open_file, bg='#424242', fg='white', activebackground='#343434', activeforeground='white', relief="raised", cursor="hand2") # put your function name in the command option maitra
button4['font'] = myFont
button4.config(height=1, width = 17)
button4.pack(side=LEFT, padx=5)
button4.bind("<Enter>", btn_on_enter)
button4.bind("<Leave>", btn_on_leave)

mainloop()
from tkinter import *
from tkinter import ttk

root = Tk()

frame = ttk.Frame(root, padding=10)
frame.grid()

# Create label
ex_label = ttk.Label(frame, text="This is an example label")
ex_label.grid(column=0, row=0)  # layout in grid

# Button widget, under frame widget in hierarchy
# .grid can be done with the declaration, but then ex_button won't
# call to the button
ex_button = ttk.Button(frame, text="This is an example quit button", command=root.destroy)
ex_button.grid(column=1, row=0)

# Updating widgets after creation
ex_label.config(text="Edited text!")

root.mainloop()
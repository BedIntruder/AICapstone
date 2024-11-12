import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from tkinter import filedialog, font
from tkinter import *
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import json

from tagger import predict_and_list_labels

# Global variables to track images, tags, and UI state
image_files = []
current_image_index = -1
tags_dict = {}
resize_enabled = True
active_edit_entry = None

CONFIDENCE=0.6

# Load tags from a JSON file (tag.json)
def load_tags():
    global tags_dict

    if os.path.exists("tag.json"):
        with open("tag.json", "r") as file:
            tags_dict = json.load(file)
    else:
        tags_dict = {}

# Save tags to a JSON file (tag.json)
def save_tags():
    with open("tag.json", "w") as file:
        json.dump(tags_dict, file)

# Show delete tag button
def show_button(btn):
    if btn.winfo_exists():
        btn.pack(side=tk.LEFT)  # Show button

# Hide delete tag button
def hide_button(btn):
    if btn.winfo_exists():
        btn.pack_forget()  # Hide the button

# Display tags in the tag frame
def display_tags():
    global t_width, delete_button_width, tag_frame_width, active_edit_entry

    # Clear existing widgets from the tag display frame
    for widget in tag_frame.winfo_children():
        widget.destroy()

    t_width= []

    # Set up tag buttons with delete buttons and add them to the frame
    if current_image_index != -1:

         # Get tags for the currently selected image
        current_image = image_files[current_image_index]
        image_tags = tags_dict.get(current_image, [])

        row = 0
        total_width = 0

        # Define frame width and button sizes based on window and font metrics
        tag_frame_width = int(root.winfo_width() * 0.29) - 10
        font_metrics = font.Font(font=style.lookup("new.TButton", "font"))
        delete_button_text = "X"
        delete_button_width = font_metrics.measure(delete_button_text) + 15
        index = 0

        # Loop through each tag, creating buttons for each tag and delete option
        for tag in image_tags:
            tag_text_width = font_metrics.measure(tag) + 20
            
            # Adjust row if tag width exceeds frame width
            if total_width + tag_text_width + delete_button_width > tag_frame_width:
                row += 1
                total_width = 0

            # Calculate rel position for each tag
            relx_tag = 0.015 + total_width / tag_frame_width
            rely_tag = 0.03 + (row * 0.1)

            # Create frame for each tag
            tag_frame_inner = Frame(tag_frame, height=25, bg="#6184ac",name=f"tag_inner_frame{index}")
            tag_frame_inner.place(relx=relx_tag, rely=rely_tag)

            # Add the tag button
            t_width.append(tag_text_width + delete_button_width + 10)
            tag_button = ttk.Button(tag_frame_inner, text=tag, command=lambda t=tag, pf=tag_frame_inner, idx= index: create_edit_entry(t, pf,idx), style="new.TButton")
            tag_button.config(width=int(tag_text_width / 8))
            tag_button.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Add delete button
            delete_button = ttk.Button(tag_frame_inner, text=delete_button_text, command=lambda t=tag: delete_tag(t), style="new.TButton")
            delete_button.config(width=int(delete_button_width / 8) - 1)
            delete_button.pack(side=tk.LEFT)
            delete_button.pack_forget()
            
            # Show/hide delete button on mouse enter/leave events
            tag_frame_inner.bind("<Enter>", lambda e, btn=delete_button: show_button(btn))
            tag_frame_inner.bind("<Leave>", lambda e, btn=delete_button: hide_button(btn))
            delete_button.bind("<Enter>", lambda e, btn=delete_button: show_button(btn))
            delete_button.bind("<Leave>", lambda e, btn=delete_button: hide_button(btn))
            total_width += tag_text_width + delete_button_width + 10
            index+=1

        # Add button to create a new tag
        add_tag_button = ttk.Button(tag_frame, text="+", command=add_new_tag, width=3, style="new.TButton")
        if total_width + 45 > tag_frame_width:
            row += 1
            total_width = 0
        t_width.append(total_width)
        relx_add_tag = 0.015 + (total_width / tag_frame_width)
        add_tag_button.place(relx=relx_add_tag, rely=0.03 + (row * 0.1))
        active_edit_entry = None

# Create an entry to edit a tag
def create_edit_entry(tag, parent_frame, entry_index):
    global active_edit_entry
    
    # Clear previous active entry if any
    if active_edit_entry is not None:
        display_tags()

    # Clear existing widgets in the parent frame
    for widget in parent_frame.winfo_children():
        widget.destroy()
    
    active_edit_entry = tag

    # Set font size for the entry based on window width
    entry_font_size = int(root.winfo_width() * 0.0078)
    if entry_font_size < 9:
        entry_font_size = 9
    edit_entry = ttk.Entry(parent_frame, style="new.TButton", font=("DilleniaUPC", entry_font_size), justify=CENTER)
    edit_entry.insert(0, tag)
    edit_entry.focus()
    
    # Adjust the width of the entry
    def adjust_entry_width(event=None):
        font_metrics = font.Font(font=style.lookup("new.TButton", "font"))
        text = edit_entry.get()
        text_width = font_metrics.measure(text) + 20
        total_width = text_width + delete_button_width + 10

        if event and total_width >= tag_frame_width and event.keysym not in ('BackSpace', 'Left', 'Right', "Return"):
            return "break"

        edit_entry.config(width=int(text_width / 8) + 1)
        edit_entry.update_idletasks()
        reposition_tag_frames(edit_entry.get(), entry_index)
    
    # Cancel editing
    def cancel_edit(event=None):
        display_tags()
        tag_frame.unbind("<Button-1>")

    tag_frame.bind("<Button-1>", lambda event: cancel_edit())
    edit_entry.bind("<KeyRelease>", adjust_entry_width)
    edit_entry.bind("<Key>", adjust_entry_width)
    edit_entry.bind("<Return>", lambda event, t=tag, e=edit_entry, idx=entry_index: finish_edit_tag(t, e, idx))
    adjust_entry_width()
    edit_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Reposition of tags when editing
def reposition_tag_frames(last_word,entry_index):
    row, total_width , index = 0, 0, 0  
    font_metrics = font.Font(font=style.lookup("new.TButton", "font"))
    text = last_word
    text_width = font_metrics.measure(text)+20

    for tag_frame_inner in tag_frame.winfo_children():
        if index == entry_index:tag_width = text_width + delete_button_width + 10
        elif index == len(t_width)-1: tag_width = 45
        else:tag_width = t_width[index]

        # Start a new row if total width exceeds frame width
        if total_width + tag_width > tag_frame_width:
            row += 1
            total_width = 0 
            
        relx = 0.015 + total_width / tag_frame_width
        rely = 0.03 + (row * 0.1)
        tag_frame_inner.place_configure(relx=relx, rely=rely)
        total_width += tag_width 
        index+=1
        
# Finalize the tag edit and update the display
def finish_edit_tag(old_tag, entry_widget, entry_index):
    new_tag = entry_widget.get()

    if current_image_index != -1:
        current_image = image_files[current_image_index]
        
        # Update the tags dictionary
        if new_tag:
            if current_image in tags_dict and old_tag in tags_dict[current_image]:
                tags_dict[current_image][entry_index] = new_tag
            save_tags()

    display_tags()

# Delete tag
def delete_tag(tag):
    if current_image_index != -1:
        current_image = image_files[current_image_index]
        if current_image in tags_dict and tag in tags_dict[current_image]:
            tags_dict[current_image].remove(tag)
            save_tags()
            display_tags()

# Add a new default tag
def add_new_tag():
    if current_image_index != -1:
        current_image = image_files[current_image_index]
        new_tag = "New Tag"
        if current_image not in tags_dict:
            tags_dict[current_image] = []
        tags_dict[current_image].append(new_tag)
        save_tags()
        display_tags()

# Open file dialog to select and display an image
def open_file_explorer():
    global image_files, current_image_index

    toggle_resize(False)
    file_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
    
    if file_path:
        image_files.append(file_path)
        current_image_index = len(image_files) - 1
        tags=predict_and_list_labels(file_path, confidence=CONFIDENCE)
        tags_dict[file_path]=tags
        display_image(file_path)
        display_tags()
        update_index_label()
    toggle_resize(True)

# Handle file drop onto the image display
def drop_inside_image_label(event):
    global image_files, current_image_index, tags_dict

    files = event.data.strip('{}').split(' ')

    for file_path in files:
        if file_path.lower().endswith((".png", ".jpg", ".jpeg")):
            image_files.append(file_path)
            tags=predict_and_list_labels(file_path, confidence=CONFIDENCE)
            tags_dict[file_path]=tags

    if image_files:
        current_image_index = len(image_files) - 1
        display_image(image_files[current_image_index])
        display_tags()
        update_index_label()

# Display selected image in the left frame
def display_image(file_path):
    global img_tk

    try:
        img = Image.open(file_path)

        # Calculate the maximum width and height based on root window size
        max_width = int(root.winfo_width() / 1.92)
        max_height = int(root.winfo_height() / 1.32)

        img.thumbnail((max_width, max_height), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)

        # Clear any existing images and display the new image
        image_label.delete("all")
        image_label.create_image(max_width // 2, max_height // 2, anchor=tk.CENTER, image=img_tk)
        image_label.config(width=max_width, height=max_height)

        update_index_label()

    # Handle errors if the image cannot be loaded
    except Exception as e:
        print(f"Error opening image: {e}")
        index_label.configure(text="Error loading image")

# Show the previous image
def show_previous_image():
    global current_image_index

    if len(image_files) > 0:
        current_image_index = (current_image_index - 1) % len(image_files)
        display_image(image_files[current_image_index])
        display_tags()
        update_index_label()

# Show the next image
def show_next_image():
    global current_image_index

    if len(image_files) > 0:
        current_image_index = (current_image_index + 1) % len(image_files)
        display_image(image_files[current_image_index])
        display_tags()
        update_index_label()

# Update the label showing the current image index
def update_index_label():
    total_images = len(image_files)
    current_index_display = current_image_index + 1 if total_images > 0 else 0
    file_name = os.path.basename(image_files[current_image_index]) if current_image_index != -1 else ""
    index_label.configure(text=f"Image {current_index_display} of {total_images}: {file_name}")

# Enable or disable resizing functionality
def toggle_resize(enable):
    global resize_enabled
    resize_enabled = enable

# Resize UI elements when window size changes
def resize(event=None):
    global prev_size,img_tk, prev_icon, next_icon, browser_icon

    current_size = (root.winfo_width(), root.winfo_height())
    if current_size == prev_size:  # If the size hasn't changed, do nothing
        return
    prev_size = current_size  # Update the previous size
    
    window_width = root.winfo_width()
    window_height = root.winfo_height()

    # Resize image label
    if current_image_index != -1 and image_files:
        img = Image.open(image_files[current_image_index])
        img.thumbnail((int(window_width / 1.92), int(window_height / 1.32)), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        image_label.config(width=int(window_width / 1.92), height=int(window_height / 1.32))
        image_label.delete("all")
        image_label.create_image(int(window_width / 1.92) // 2, int(window_height / 1.32) // 2, anchor=tk.CENTER, image=img_tk)
    else:
        image_label.config(width=int(window_width / 1.92), height=int(window_height / 1.32))

    # Adjust tags font size
    tag_font_size = int(window_height * 0.015)
    if tag_font_size < 7:
        tag_font_size = 7
    style.configure("new.TButton", font=("DilleniaUPC", int(tag_font_size)))
    display_tags()

    # Resize index label font size
    font_size = int(window_height * 0.015)
    if font_size < 5:
        font_size = 5
    new_font = font.Font(family="Bodoni MT", size=font_size)
    index_label.config(font=new_font)

    # Resize icon size
    icon_size = int(window_width * 0.05)
    if icon_size < 20:
        icon_size = 20

    prev_img_resized = prev_img.resize((icon_size, icon_size), Image.LANCZOS)
    next_img_resized = next_img.resize((icon_size, icon_size), Image.LANCZOS)
    browser_img_resized = open_file_img.resize((icon_size, icon_size), Image.LANCZOS)

    prev_icon = ImageTk.PhotoImage(prev_img_resized)
    next_icon = ImageTk.PhotoImage(next_img_resized)
    browser_icon = ImageTk.PhotoImage(browser_img_resized)

    prev_button.config(image=prev_icon)
    next_button.config(image=next_icon)
    open_file_button.config(image=browser_icon)

# Initialize and run the main application
def main():
    global root, style, main_frame, left_frame, right_frame, image_label, tag_frame, tag_title_label, prev_size
    global prev_icon, next_icon, prev_button, next_button, index_label, open_file_icon, open_file_button, prev_img, next_img, open_file_img, my_font

    # Tkinter setup and UI layout configuration
    root = TkinterDnD.Tk()
    root.state('zoomed')
    root.minsize(1100, 600)
    root.bind('<Configure>', resize)

    prev_size = (root.winfo_width(), root.winfo_height())

    style = ttk.Style()
    style.configure("new.TButton", background="#6184ac", bd=0, font=(int(root.winfo_width() * 0.015)))

    # Main frame
    main_frame = Frame(root, background="#294361")
    main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    # Image frame
    left_frame = ctk.CTkFrame(main_frame, fg_color="#b7d0d7", border_width=3, corner_radius=25, border_color="#7799b9", bg_color="#294361")
    left_frame.place(relx=0.02, rely=0.03, relwidth=0.665, relheight=0.83)

    # Tag frame
    right_frame = ctk.CTkFrame(main_frame, fg_color="#294361", bg_color="#294361")
    right_frame.place(relx=0.7, rely=0.03, relwidth=0.29, relheight=0.95)

    # Image display
    image_label = Canvas(left_frame, background='#b7d0d7', width=800, height=600, highlightthickness=1, highlightbackground="#7799b9", highlightcolor="black")
    image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    image_label.drop_target_register(DND_FILES)
    image_label.dnd_bind('<<Drop>>', drop_inside_image_label)

    # Tag display frame
    tag_frame = ctk.CTkFrame(right_frame, fg_color="#6184ac", bg_color="#294361", border_width=3, corner_radius=25, border_color="#ADD8E6")
    tag_frame.place(relx=0, rely=0.12, relwidth=1, relheight=0.883)

    tag_title_frame = ctk.CTkFrame(right_frame, corner_radius=25, bg_color="#294361", fg_color="#e5b945", border_width=3, border_color="black")
    tag_title_frame.place(relx=0, rely=0, relwidth=1, relheight=0.105)
    my_font = ctk.CTkFont(family="Arial Rounded MT Bold", size=24)

    tag_title_label = ctk.CTkLabel(tag_title_frame, text="Recommended tags:", corner_radius=25, font=my_font, text_color="black")
    tag_title_label.place(relx=0.15, rely=0.15, relwidth=0.7, relheight=0.7)

    load_tags()

    # Navigation buttons
    prev_button_frame = ctk.CTkFrame(main_frame, corner_radius=25, fg_color="#9ab3ca", bg_color="#294361", border_width=2, border_color="#4a6b8a")
    prev_button_frame.place(relx=0.04, rely=0.88, relwidth=0.1, relheight=0.1)

    next_button_frame = ctk.CTkFrame(main_frame, corner_radius=25, fg_color="#9ab3ca", bg_color="#294361", border_width=2, border_color="#4a6b8a")
    next_button_frame.place(relx=0.57, rely=0.88, relwidth=0.1, relheight=0.1)

    index_label_frame = ctk.CTkFrame(main_frame, corner_radius=25, fg_color="#799abf", bg_color="#294361", border_width=2, border_color="#5d7d9a")
    index_label_frame.place(relx=0.155, rely=0.88, relwidth=0.4, relheight=0.1)

    prev_img = Image.open("assets/icons/prev.png")
    next_img = Image.open("assets/icons/next.png")

    prev_icon = ImageTk.PhotoImage(prev_img)
    next_icon = ImageTk.PhotoImage(next_img)

    prev_button = Button(prev_button_frame, command=show_previous_image, image=prev_icon, background="#9ab3ca", activebackground="#9ab3ca", bd=0)
    prev_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relheight=0.9, relwidth=0.7)

    next_button = Button(next_button_frame, command=show_next_image, image=next_icon, background="#9ab3ca", activebackground="#9ab3ca", bd=0)
    next_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relheight=0.9, relwidth=0.7)

    index_label = ttk.Label(index_label_frame, text="Image 0 of 0", background='#799abf')
    index_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    # Open file button
    open_file_img = Image.open("assets/icons/browse.png")
    open_file_icon = ImageTk.PhotoImage(open_file_img)

    open_file_button = Button(left_frame, image=open_file_icon, compound="right", command=open_file_explorer, background="#b7d0d7", activebackground="#b7d0d7", bd=0)
    open_file_button.place(relx=0.95, rely=0.09, anchor=tk.CENTER)

    root.mainloop()

# Run the app
if __name__ == "__main__":
    main()

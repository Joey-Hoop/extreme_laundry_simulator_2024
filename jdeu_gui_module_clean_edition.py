import tkinter as tk
from tkinter import messagebox
import threading
import jdeu_logic_module_clean_edition  # Ensure this is in the same directory
import colorsys


def process_tickets_thread(url: str, username: str, token: str, project_key: str, start_range: str, end_range: str):
    try:
        filename = jdeu_logic_module_clean_edition.process_tickets(url, username, token, project_key, start_range,
                                                                   end_range)
        messagebox.showinfo("Success", f"Data written to {filename}")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        # Enable the button and clear the warning message after processing
        process_button.config(state=tk.NORMAL)
        warning_label.config(text="")
        start_color_cycle()  # Restart the color cycle


def handle_button_click():
    # Disable the button and set its color to gray
    process_button.config(state=tk.DISABLED, bg="gray", activebackground="gray")
    root.after_cancel(color_cycle_id)  # Stop the color cycling

    # Update warning message
    warning_label.config(text="DO NOT CLOSE THIS WINDOW\nTHIS MAY TAKE A WHILE\nSEE CONSOLE FOR PROCESS OUTPUT",
                         fg="red")

    # Start the process in a new thread
    url = url_entry.get()
    username = username_entry.get()
    token = token_entry.get()
    project_key = project_key_entry.get()
    start_range = int(start_range_entry.get())
    end_range = int(end_range_entry.get())

    threading.Thread(target=process_tickets_thread, args=(url, username, token, project_key, start_range, end_range),
                     daemon=True).start()


def cycle_colors():
    hue = 0
    while True:
        rgb = colorsys.hsv_to_rgb(hue, 1, 1)
        hex_color = "#{:02x}{:02x}{:02x}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        process_button.config(bg=hex_color, activebackground=hex_color)
        hue += 0.01
        if hue >= 1:
            hue = 0
        yield


def start_color_cycle():
    global color_cycle, color_cycle_id
    color_cycle = cycle_colors()
    color_cycle_id = root.after(50, lambda: update_color())


def update_color():
    global color_cycle_id
    try:
        next(color_cycle)
        color_cycle_id = root.after(50, lambda: update_color())
    except StopIteration:
        color_cycle_id = None


root = tk.Tk()
root.title("Jira Data Extraction Utility")
root.geometry("500x500")

# Default values
default_url = ""
default_username = ""
default_token = ""
default_project_key = ""
default_start_range = ""
default_end_range = ""

# Labels and entries with padding
tk.Label(root, text="Jira URL:").pack(pady=2)
url_entry = tk.Entry(root)
url_entry.insert(0, default_url)
url_entry.pack(pady=2)

tk.Label(root, text="Jira Username:").pack(pady=2)
username_entry = tk.Entry(root)
username_entry.insert(0, default_username)
username_entry.pack(pady=2)

tk.Label(root, text="Jira Token:").pack(pady=2)
token_entry = tk.Entry(root, show="*")
token_entry.insert(0, default_token)
token_entry.pack(pady=2)

tk.Label(root, text="Project Key:").pack(pady=2)
project_key_entry = tk.Entry(root)
project_key_entry.insert(0, default_project_key)
project_key_entry.pack(pady=2)

tk.Label(root, text="Start Range:").pack(pady=2)
start_range_entry = tk.Entry(root)
start_range_entry.insert(0, default_start_range)
start_range_entry.pack(pady=2)

tk.Label(root, text="End Range:").pack(pady=2)
end_range_entry = tk.Entry(root)
end_range_entry.insert(0, default_end_range)
end_range_entry.pack(pady=2)

# Process button with padding
process_button = tk.Button(root, text="Extract Data", command=handle_button_click)
process_button.pack(pady=2)

# Warning label with padding
warning_label = tk.Label(root, text="", font=("Helvetica", 10, "bold"))
warning_label.pack(pady=2)

color_cycle = None
color_cycle_id = None
start_color_cycle()

root.mainloop()

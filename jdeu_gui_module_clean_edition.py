"""
<h1>jdeu_gui_module</h1>
<h2>Extreme Laundry Simulator (Don't laugh at me, I know this is a temporary name)>
<h3>IEW&S<h3>
<p>
The jdeu_gui_module file creates an interface for the user to input
the JIRA database URL, the user's email, their JIRA token, 
the project key, and the starting index as well as the ending index
</p>
@Author Evan Snyder
@Since MM/DD/YYYY
@Version 1.2
"""

import tkinter as tk
from tkinter import messagebox
import threading
import jdeu_logic_module_clean_edition  # Ensure this is in the same directory
import colorsys
from math import ceil
from multiprocessing import Process
from multiprocessing import Lock
import multiprocessing
from datetime import datetime
import json

CPU_COUNT = multiprocessing.cpu_count()
if __name__ == '__main__':
    lock = Lock()


    def process_tickets_thread(url: str, username: str, token: str, project_key: str, start_range: int, end_range: int):
        """
        This function parses the given list from Jira using all available processors,
        then each processor runs the logic module on their respective sublist (Runs in parallel)

        Parameters:
        url (str): Jira database URL
        username (str): Appropriate username with access to the database
        token (str): user's Jira token
        project_key (str): The project key from the user input
        start_range (int): Lower bound of jira database range given by user
        end_range (int): Upper bound of jira database range given by user

        Returns:
        None
        """
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'jira_data_{current_time}.csv'
        try:
            processes = []
            # For now, we assume that end_range > start_range, but we can add a failsafe for bad input later
            step_size = ceil((end_range - start_range) / CPU_COUNT)

            for i in range(CPU_COUNT):
                process_min = (i * step_size) + start_range
                process_max = process_min + step_size if (process_min + step_size < end_range) else end_range
                processes.append(Process(target=jdeu_logic_module_clean_edition.process_tickets,
                                         args=(url, username, token, project_key, process_min,
                                               process_max, filename, lock)))

                '''filename = jdeu_logic_module_clean_edition.process_tickets(url, username, token, project_key, 
                start_range, end_range, filename, lock)'''

            for p in processes:
                p.start()
            for p in processes:
                p.join()
            messagebox.showinfo("Success", f"Data written to {filename}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            # Enable the button and clear the warning message after processing
            process_button.config(state=tk.NORMAL)
            warning_label.config(text="")
            start_color_cycle()  # Restart the color cycle


    def handle_button_click():
        """
        This function receives the user input then passes the values to the process_tickets_thread function
        once the GUI button is clicked

        Parameters:
        None

        Returns:
        None
        """
        save_configs()
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

        threading.Thread(target=process_tickets_thread,
                         args=(url, username, token, project_key, start_range, end_range),
                         daemon=True).start()


    def cycle_colors():
        """
        This function prepares the colors for our GUI

        Parameters:
        None

        Returns:
        None
        """
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
        """
        This function begins the color cycle

        Parameters:
        None

        Returns:
        None
        """
        global color_cycle, color_cycle_id
        color_cycle = cycle_colors()
        color_cycle_id = root.after(50, lambda: update_color())


    def update_color():
        """
        This function receives the user input then passes the values to the process_tickets_thread function
        once the GUI button is clicked

        Parameters:
        None

        Returns:
        None
        """
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
    #NEW STUFF HERE
    #
    #
    with open("configs.json", "r") as json_file:
        configs = json.load(json_file)

     # Move this to after scan so we can edit values before the file closes

    config_booleans = []
    for header in configs:
        config_booleans.append(tk.BooleanVar(value =configs[header]))
    config_buttons = []
    for header, bool in zip(configs, config_booleans):
        config_buttons.append(tk.Checkbutton(root, text=f"Include {header}", variable=bool, 
                             onvalue=True, offvalue=False))
    def save_configs():
        for header, bool in zip(configs, config_booleans):
            configs[header] = bool.get()
        with open("configs.json", 'w') as file:
            json.dump(configs, file, indent=4)

    def scan_button_click():
        configBool.set(not(configBool.get()))
        start_range_entry.delete(0, tk.END)
        start_range_entry.insert(0, "0")
        # Add other scan stuff in here later, such as setting range
        if configBool.get():
            for button in config_buttons:
                button.pack(pady=2)
        else:
            for button in config_buttons:
                button.pack_forget()

    configBool = tk.BooleanVar(value=False)
    
    # This is temporary just to show that the values update independently
    for bool in config_booleans:
        tk.Label(root, textvariable=bool).pack(pady=2)
    
    scan_button = tk.Button(root, text="Scan And Configure", command=scan_button_click)
    scan_button.pack(pady=2)
    #
    #
    #STOOOOOP!!!!!!!
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

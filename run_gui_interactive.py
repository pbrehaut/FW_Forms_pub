import tkinter as tk
from tkinter import ttk, messagebox, Text, filedialog
import json
import generate_xls_diagrams
from configmanager import ConfigManager

# Global variable for config file
CONFIG_FILE = 'config.ini'


class NetworkInfoGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Network Information")
        self.master.geometry("400x600")

        topology = ConfigManager(CONFIG_FILE)
        self.customers = topology.get_customers()
        self.results = {}
        self.selected_customer = tk.StringVar()
        self.file_path = tk.StringVar()

        # Initial Form
        self.create_initial_form()

    def create_initial_form(self):
        # File Selection Section
        self.file_label = tk.Label(self.master, text="Load from File", font=("Arial", 12, "bold"))
        self.file_label.pack(pady=(20, 10))

        file_frame = tk.Frame(self.master)
        file_frame.pack(pady=5)

        self.file_entry = tk.Entry(file_frame, textvariable=self.file_path, width=30)
        self.file_entry.pack(side=tk.LEFT)

        self.browse_button = tk.Button(file_frame, text="Browse", command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT)

        self.load_button = tk.Button(self.master, text="Load JSON File", command=self.load_file)
        self.load_button.pack(pady=5)

        # Separator
        self.separator = ttk.Separator(self.master, orient='horizontal')
        self.separator.pack(fill='x', pady=20)

        # Customer Selection Section
        self.customer_label = tk.Label(self.master, text="Manual Input", font=("Arial", 12, "bold"))
        self.customer_label.pack(pady=(10, 10))

        self.select_customer_label = tk.Label(self.master, text="Select Customer:")
        self.select_customer_label.pack()

        self.customer_combo = ttk.Combobox(self.master, textvariable=self.selected_customer, values=list(self.customers))
        self.customer_combo.pack(pady=5)

        self.start_manual_button = tk.Button(self.master, text="Start Manual Input", command=self.start_manual_input)
        self.start_manual_button.pack(pady=5)

    def create_manual_input_form(self):
        #  Reset self.results to an empty dictionary
        # self.results = {}

        self.manual_input_frame = ttk.Frame(self.master)
        self.manual_input_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Input Form
        input_form = ttk.LabelFrame(self.manual_input_frame, text="Input Form")
        input_form.pack(padx=10, pady=10, fill="both", expand=True)

        self.input_fields = {}
        field_heights = {"Source IPs": 5, "Destination IPs": 5, "Services": 2, "Comments": 3}

        first_field = None

        for field, height in field_heights.items():
            frame = ttk.Frame(input_form)
            frame.pack(fill="x", padx=5, pady=5)
            ttk.Label(frame, text=f"{field}:").pack(anchor="w", padx=5)
            text = Text(frame, height=height, width=40)
            text.pack(fill="x", padx=5)
            self.input_fields[field] = text

            # Make Text widgets tabbable
            text.configure(takefocus=1)

            # Store the first field
            if first_field is None:
                first_field = text

        # Buttons
        button_frame = ttk.Frame(input_form)
        button_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(button_frame, text="Add Entry", command=self.add_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Update Entry", command=self.update_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Entry", command=self.delete_entry).pack(side=tk.LEFT, padx=5)

        # Submit Button (now in button_frame)
        self.submit_button = ttk.Button(button_frame, text="Submit", command=self.submit_results)
        self.submit_button.pack(side=tk.RIGHT, padx=5)

        # Assuming this is part of a class, and self.manual_input_frame already exists

        # Create a frame to hold the Treeview and scrollbar
        tree_frame = tk.Frame(self.manual_input_frame)
        tree_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Create the Treeview widget
        self.tree = ttk.Treeview(tree_frame,
                                 columns=("Source IPs", "Destination IPs", "Services", "Comments"), show="headings")
        self.tree.heading("Source IPs", text="Source IPs")
        self.tree.column("Source IPs", width=0, stretch=tk.NO)
        self.tree.heading("Destination IPs", text="Destination IPs")
        self.tree.column("Destination IPs", width=0, stretch=tk.NO)
        self.tree.heading("Services", text="Services")
        self.tree.column("Services", width=0, stretch=tk.NO)
        self.tree.heading("Comments", text="Comments")
        self.tree.column("Comments", width=200)

        # Create vertical scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        # Grid layout for Treeview and scrollbar
        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')

        # Configure the tree_frame grid
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # Set tab order
        self.bind_tab_navigation()

        # Load data into Treeview if provided
        if self.results:
            data = self.results.get(self.selected_customer.get(), [])
            for entry in data:
                self.tree.insert("", "end", values=entry)

        # Set focus to the first field
        if first_field:
            self.master.after(100, lambda: first_field.focus_set())

    def bind_tab_navigation(self):
        def focus_next_widget(event):
            event.widget.tk_focusNext().focus()
            return "break"

        def focus_previous_widget(event):
            event.widget.tk_focusPrev().focus()
            return "break"

        for field in self.input_fields.values():
            field.bind("<Tab>", focus_next_widget)
            field.bind("<Shift-Tab>", focus_previous_widget)

        self.tree.bind("<Tab>", focus_next_widget)
        self.tree.bind("<Shift-Tab>", focus_previous_widget)

        for button in [self.submit_button]:  # Add other buttons if needed
            button.bind("<Tab>", focus_next_widget)
            button.bind("<Shift-Tab>", focus_previous_widget)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if file_path:
            self.file_path.set(file_path)

    def load_file(self):
        if not self.file_path.get():
            messagebox.showwarning("Warning", "Please select a file.")
            return
        try:
            with open(self.file_path.get(), 'r') as file:
                self.results = json.load(file)

            # Extract the customer key from the JSON data
            customer_key = list(self.results.keys())[0]
            self.selected_customer.set(customer_key)

            # Remove initial form
            for widget in self.master.winfo_children():
                widget.destroy()

            # Create and show manual input form
            self.create_manual_input_form()

            messagebox.showinfo("File Loaded", f"File {self.file_path.get()} loaded successfully.")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON file. Please select a valid JSON file.")
        except IOError:
            messagebox.showerror("Error",
                                 "Could not read the file. Please check if the file exists and you have permission to read it.")

    import tkinter as tk
    from tkinter import ttk, messagebox, Text, filedialog

    def process_results(self):
        config_mgr = ConfigManager(CONFIG_FILE)
        user_msg = generate_xls_diagrams.generate_output(self.results, config_mgr)

        if not user_msg:
            user_msg = "No IPs unmatched to a topology."

        header = f'''Requested rules processed and output to:\n{config_mgr.get_output_directory(self.selected_customer.get())}\n\n'''

        user_msg = header + user_msg

        # Create a new window for the custom input form
        result_window = tk.Toplevel(self.master)
        result_window.title("Output")
        result_window.geometry("600x400")

        # Create a frame to hold the text box
        text_frame = tk.Frame(result_window)
        text_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Create the text box
        result_text = Text(text_frame, width=80, height=15, font=("Arial", 12))
        result_text.pack(fill="both", expand=True)

        # Insert the user_msg into the text box
        result_text.insert("1.0", user_msg)

        # Create a button to close the window
        close_button = tk.Button(result_window, text="Close", command=result_window.destroy)
        close_button.pack(pady=10)

        # Set the text box as read-only
        result_text.configure(state="disabled")

    def submit_results(self):
        self.results[self.selected_customer.get()] = [self.tree.item(item)["values"] for item in
                                                      self.tree.get_children()]
        self.process_results()

    def start_manual_input(self):
        if not self.selected_customer.get():
            messagebox.showwarning("Warning", "Please select a customer.")
            return

        # Remove initial form
        for widget in self.master.winfo_children():
            widget.destroy()

        # Create and show manual input form
        self.create_manual_input_form()
        self.results[self.selected_customer.get()] = []

    def add_entry(self):
        entry = {field: self.input_fields[field].get("1.0", tk.END).strip() for field in self.input_fields}
        self.tree.insert("", "end", values=(entry["Source IPs"], entry["Destination IPs"], entry["Services"], entry["Comments"].replace('\n', '; ')))
        self.clear_input_fields()

    def update_entry(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an entry to update.")
            return

        entry = {field: self.input_fields[field].get("1.0", tk.END).strip() for field in self.input_fields}
        self.tree.item(selected_item, values=(entry["Source IPs"], entry["Destination IPs"], entry["Services"], entry["Comments"].replace('\n', '; ')))
        self.clear_input_fields()

    def delete_entry(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an entry to delete.")
            return
        self.tree.delete(selected_item)

    def on_tree_double_click(self, event):
        item = self.tree.selection()[0]
        values = self.tree.item(item, "values")
        for field, value in zip(self.input_fields.keys(), values):
            self.input_fields[field].delete("1.0", tk.END)
            if field == "Comments":
                value = value.replace('; ', '\n')
            self.input_fields[field].insert("1.0", value)

    def clear_input_fields(self):
        for text in self.input_fields.values():
            text.delete("1.0", tk.END)


def run_gui():
    root = tk.Tk()
    gui = NetworkInfoGUI(root)
    root.mainloop()
    return gui.results


if __name__ == "__main__":
    run_gui()

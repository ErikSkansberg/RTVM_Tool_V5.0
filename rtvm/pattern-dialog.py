# rtvm/gui/pattern_dialog.py - Pattern Dialog UI component

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Callable, Dict, List, Optional

from rtvm.models.pattern_generator import PatternGenerator
from rtvm.utils.config import config

logger = logging.getLogger(__name__)

class PatternDialog(tk.Toplevel):
    """
    Dialog for creating verification patterns.
    """
    
    def __init__(self, 
                 master: tk.Widget, 
                 obj_identifier: str, 
                 di_number: str, 
                 current_row: int,
                 on_save_callback: Callable[[str], bool]):
        """
        Initialize the pattern dialog.
        
        Args:
            master: The parent widget
            obj_identifier: The object identifier to use
            di_number: The DI number to use
            current_row: The current row being edited
            on_save_callback: Callback function to save the pattern
        """
        super().__init__(master)
        self.title("Pattern Generator")
        
        # Store parameters
        self.obj_identifier = obj_identifier
        self.di_number = di_number
        self.current_row = current_row
        self.on_save_callback = on_save_callback
        
        # Initialize variables
        self.patterns = []
        
        # Create UI
        self._create_widgets()
        
        # Center the dialog on the parent window
        self.transient(master)  # Set to be on top of the parent window
        self.grab_set()  # Make this dialog modal
        
        # Wait until the window appears on the screen before positioning it
        self.update_idletasks()
        self._center_window()
        
        # Load status values from config if available
        self._load_config_values()
    
    def _create_widgets(self):
        """Create and configure all widgets in the dialog."""
        # Main frame with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Object Identifier
        ttk.Label(main_frame, text="Object Identifier").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.obj_identifier_entry = ttk.Entry(main_frame, width=40)
        self.obj_identifier_entry.grid(row=0, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        self.obj_identifier_entry.insert(0, self.obj_identifier)
        
        # CDRL Name
        ttk.Label(main_frame, text="(4) CDRL File Name").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.cdrl_name_entry = ttk.Entry(main_frame, width=40)
        self.cdrl_name_entry.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Detailed Location - Page/Sheet
        ttk.Label(main_frame, text="(4) Page/Sheet").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.page_sheet_var = tk.StringVar(self)
        self.page_sheet_var.set("Page")  # default value
        self.page_sheet_combobox = ttk.Combobox(
            main_frame, textvariable=self.page_sheet_var,
            values=["Page", "Sheet"], width=8, state="readonly")
        self.page_sheet_combobox.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.page_sheet_entry = ttk.Entry(main_frame, width=15)
        self.page_sheet_entry.grid(row=2, column=2, sticky="w", padx=5, pady=5)
        
        # Detailed Location - Plan View/Section
        ttk.Label(main_frame, text="(4) Plan View/Section").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.plan_view_var = tk.StringVar(self)
        self.plan_view_var.set("Plan View")  # default value
        self.plan_view_combobox = ttk.Combobox(
            main_frame, textvariable=self.plan_view_var,
            values=["Plan View", "Section"], width=8, state="readonly")
        self.plan_view_combobox.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.plan_view_entry = ttk.Entry(main_frame, width=15)
        self.plan_view_entry.grid(row=3, column=2, sticky="w", padx=5, pady=5)
        
        # Contractor Assessed Status
        ttk.Label(main_frame, text="(5) Contractor Assessed Status").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.status_var = tk.StringVar(self)
        self.status_var.set("")  # Default to blank
        self.status_combobox = ttk.Combobox(
            main_frame, textvariable=self.status_var, 
            values=["SAT", "UNSAT"], width=10, state="readonly")
        self.status_combobox.grid(row=4, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        
        # DI Number
        ttk.Label(main_frame, text="DI Number").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        self.di_number_entry = ttk.Entry(main_frame, width=20)
        self.di_number_entry.grid(row=5, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        self.di_number_entry.insert(0, self.di_number)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        # Generate Button
        ttk.Button(
            button_frame, text="(6) Generate Pattern", 
            command=self.generate_pattern
        ).grid(row=0, column=0, padx=5, pady=5)
        
        # Copy Button
        ttk.Button(
            button_frame, text="(7) Copy to Clipboard", 
            command=self.copy_to_clipboard
        ).grid(row=0, column=1, padx=5, pady=5)
        
        # Save to Excel Button
        ttk.Button(
            button_frame, text="Save Generated Pattern to Excel", 
            command=self.save_to_excel
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Reset Button
        ttk.Button(
            button_frame, text="Reset", 
            command=self.reset_fields
        ).grid(row=0, column=3, padx=5, pady=5)
        
        # Also create the 180-Vessel Version Button
        ttk.Button(
            button_frame, text="Also create a 180-Vessel Version", 
            command=self.create_180_version
        ).grid(row=1, column=0, columnspan=4, padx=5, pady=5)
        
        # Generated Pattern
        ttk.Label(main_frame, text="Generated Pattern: For column G").grid(
            row=7, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 0))
        self.output_text = tk.Text(main_frame, height=6, width=70)
        self.output_text.grid(row=8, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        
        # Add scrollbar for output text
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        scrollbar.grid(row=8, column=3, sticky="ns")
        self.output_text.config(yscrollcommand=scrollbar.set)
        
        # Configure grid weights for resizing
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(8, weight=1)
    
    def _center_window(self):
        """Center the dialog window on its parent."""
        parent = self.master
        
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        
        # Ensure the window is visible on screen
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        
        x = max(0, min(x, screen_width - self.winfo_width()))
        y = max(0, min(y, screen_height - self.winfo_height()))
        
        self.geometry(f"+{x}+{y}")
    
    def _load_config_values(self):
        """Load values from config if available."""
        # If there are predefined CDRL values, populate the dropdown
        saved_cdrl = config.get("last_entries", "cdrl_name", None)
        if saved_cdrl:
            self.cdrl_name_entry.insert(0, saved_cdrl)
        
        # Load last used status
        saved_status = config.get("last_entries", "contractor_status", None)
        if saved_status:
            self.status_var.set(saved_status)
    
    def _save_config_values(self):
        """Save current values to config for future use."""
        cdrl_name = self.cdrl_name_entry.get().strip()
        if cdrl_name:
            config.set("last_entries", "cdrl_name", cdrl_name)
        
        status = self.status_var.get()
        if status:
            config.set("last_entries", "contractor_status", status)
    
    def generate_pattern(self):
        """Generate a verification pattern based on user inputs."""
        # Clear output text
        self.output_text.delete("1.0", tk.END)
        self.patterns = []
        
        # Validate inputs
        is_valid, error_messages = PatternGenerator.validate_pattern_inputs(
            self.obj_identifier_entry.get(),
            self.cdrl_name_entry.get(),
            self.page_sheet_entry.get(),
            self.plan_view_entry.get(),
            self.status_var.get()
        )
        
        if not is_valid:
            messagebox.showerror("Input Error", "\n".join(error_messages))
            return
        
        # Generate the pattern
        pattern = PatternGenerator.generate_standard_pattern(
            self.obj_identifier_entry.get(),
            self.cdrl_name_entry.get(),
            self.page_sheet_var.get(),
            self.page_sheet_entry.get(),
            self.plan_view_var.get(),
            self.plan_view_entry.get(),
            self.status_var.get()
        )
        
        # Save the pattern
        self.pattern1 = pattern
        self.patterns.append(self.pattern1)
        
        # Output patterns
        self.output_text.insert(tk.END, "\n".join(self.patterns))
        
        # Save values to config
        self._save_config_values()
        
        logger.info(f"Generated pattern: {pattern}")
    
    def create_180_version(self):
        """Create a pattern variant for the 180-WLR vessel."""
        # Check if the first pattern has been generated
        if not hasattr(self, 'pattern1'):
            messagebox.showerror("Error", "Please generate the initial pattern first.")
            return
        
        # Generate the 180-WLR version
        pattern = PatternGenerator.generate_vessel_specific_pattern(
            "180-WLR",
            self.di_number_entry.get(),
            self.cdrl_name_entry.get(),
            self.page_sheet_var.get(),
            self.page_sheet_entry.get(),
            self.plan_view_var.get(),
            self.plan_view_entry.get(),
            self.status_var.get()
        )
        
        # Save the pattern
        self.pattern2 = pattern
        self.patterns.append(self.pattern2)
        
        # Append the pattern to the output
        self.output_text.insert(tk.END, "\n" + self.pattern2)
        
        logger.info(f"Generated 180-WLR pattern: {pattern}")
    
    def copy_to_clipboard(self):
        """Copy the generated patterns to the clipboard."""
        # Clear the clipboard
        self.clipboard_clear()
        
        # Get the content from the output text box
        patterns = self.output_text.get("1.0", tk.END).strip()
        
        if not patterns:
            messagebox.showinfo("Info", "No patterns to copy.")
            return
        
        # Copy the content to the clipboard
        self.clipboard_append(patterns)
        
        # Update the root window to ensure the clipboard retains the copied content
        self.update()
        
        messagebox.showinfo("Success", "Patterns copied to clipboard.")
        logger.info("Patterns copied to clipboard")
    
    def save_to_excel(self):
        """Save the generated patterns to the Excel file."""
        # Get the generated patterns
        patterns = self.output_text.get("1.0", tk.END).strip()
        
        if not patterns:
            messagebox.showerror("Error", "No patterns generated to save.")
            return
        
        # Use the callback to save the patterns
        success = self.on_save_callback(patterns)
        
        if success:
            messagebox.showinfo("Success", "Patterns saved to Excel file successfully.")
            logger.info(f"Patterns saved for row {self.current_row}")
        else:
            messagebox.showerror("Error", "Failed to save patterns to Excel file.")
            logger.error(f"Failed to save patterns for row {self.current_row}")
    
    def reset_fields(self):
        """Reset all input fields to their default values."""
        self.cdrl_name_entry.delete(0, tk.END)
        self.page_sheet_entry.delete(0, tk.END)
        self.plan_view_entry.delete(0, tk.END)
        self.status_var.set("")
        self.output_text.delete("1.0", tk.END)
        self.patterns = []
        
        logger.debug("Reset pattern dialog fields")

# rtvm/gui/main_app.py - Main application class for the RTVM Tool

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import logging
import os
import threading
from typing import Dict, List, Optional, Set, Tuple, Any

from rtvm.gui.pattern_dialog import PatternDialog
from rtvm.gui.tools.disagreement_manager import DisagreementManager
from rtvm.gui.tools.removal_tool import RemovalTool
from rtvm.gui.tools.subset_manager import SubsetManager
from rtvm.gui.tools.compair_tool import CompairTool
from rtvm.gui.charts import PieChartWindow
from rtvm.utils.config import config

logger = logging.getLogger(__name__)

class RTVMApp:
    """
    Main application class for the RTVM Tool.
    Provides the primary user interface and coordinates between different modules.
    """
    
    def __init__(self, root):
        """
        Initialize the RTVM Tool application.
        
        Args:
            root: The Tkinter root window
        """
        self.root = root
        
        # Initialize variables
        self.current_row = 0
        self.df = None
        self.matrix_df = None
        self.excel_file_path = ""
        self.status_data = []
        self.current_comments = {}
        self.highlighted_items = []
        self.save_lock = threading.Lock()  # Prevent simultaneous saves
        
        # Initialize filter variables
        self.filtered_row_indices = []
        self.current_filtered_index = 0
        
        # Initialize unique statuses
        self.unique_object_statuses = set()
        self.unique_contractor_statuses = set()
        self.unique_government_statuses = set()
        
        # Create the user interface
        self._create_ui()
        
        # Load configuration
        window_width = config.get("ui", "window_width", 1600)
        window_height = config.get("ui", "window_height", 800)
        self.root.geometry(f"{window_width}x{window_height}")
        
        # Initialize the visibility settings
        self.toggle_history_tables()
        self.toggle_progress_bar()
    
    def _create_ui(self):
        """Create the main user interface."""
super().__init__(master)
        self.title("Pattern Generator")
        self.app = app  # Reference to the RTVMApp instance
        self.current_row = current_row  # Store the current row index

        # Initialize variables
        self.obj_identifier = obj_identifier
        self.di_number = di_number
        self.deletions = []

        # Object Identifier
        self.obj_identifier_label = tk.Label(self, text="Object Identifier")
        self.obj_identifier_label.grid(row=0, column=0, sticky="e")
        self.obj_identifier_entry = tk.Entry(self)
        self.obj_identifier_entry.grid(row=0, column=1, columnspan=2, sticky="w")
        self.obj_identifier_entry.insert(0, self.obj_identifier)

        # CDRL Name
        self.cdrl_name_label = tk.Label(self, text="(4) CDRL File Name")
        self.cdrl_name_label.grid(row=1, column=0, sticky="e")
        self.cdrl_name_entry = tk.Entry(self)
        self.cdrl_name_entry.grid(row=1, column=1, columnspan=2, sticky="w")

        # Detailed Location - Page/Sheet
        self.page_sheet_label = tk.Label(self, text="(4) Page/Sheet")
        self.page_sheet_label.grid(row=2, column=0, sticky="e")
        self.page_sheet_option_var = tk.StringVar(self)
        self.page_sheet_option_var.set("Page")  # default value
        self.page_sheet_option_menu = ttk.Combobox(
            self, textvariable=self.page_sheet_option_var,
            values=["Page", "Sheet"], width=8)
        self.page_sheet_option_menu.grid(row=2, column=1, sticky="w")
        self.page_sheet_entry = tk.Entry(self)
        self.page_sheet_entry.grid(row=2, column=2, sticky="w")

        # Detailed Location - Plan View/Section
        self.plan_view_label = tk.Label(self, text="(4) Plan View/Section")
        self.plan_view_label.grid(row=3, column=0, sticky="e")
        self.plan_view_option_var = tk.StringVar(self)
        self.plan_view_option_var.set("Plan View")  # default value
        self.plan_view_option_menu = ttk.Combobox(
            self, textvariable=self.plan_view_option_var,
            values=["Plan View", "Section"], width=8)
        self.plan_view_option_menu.grid(row=3, column=1, sticky="w")
        self.plan_view_entry = tk.Entry(self)
        self.plan_view_entry.grid(row=3, column=2, sticky="w")

        # Contractor Assessed Status
        self.status_label = tk.Label(self, text="(5) Contractor Assessed Status")
        self.status_label.grid(row=4, column=0, sticky="e")
        self.status_var = tk.StringVar(self)
        self.status_var.set("")  # Default to blank
        self.status_dropdown = ttk.Combobox(
            self, textvariable=self.status_var, values=["SAT", "UNSAT"])
        self.status_dropdown.grid(row=4, column=1, columnspan=2, sticky="w")

        # DI Number
        self.di_number_label = tk.Label(self, text="DI Number")
        self.di_number_label.grid(row=5, column=0, sticky="e")
        self.di_number_entry = tk.Entry(self)
        self.di_number_entry.grid(row=5, column=1, columnspan=2, sticky="w")
        self.di_number_entry.insert(0, self.di_number)

        # Buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=6, column=0, columnspan=3)

        # Generate Button
        self.generate_button = tk.Button(
            self.button_frame, text="(6) Generate Pattern", command=self.generate_pattern)
        self.generate_button.grid(row=0, column=0, padx=5, pady=5)

        # Copy Button
        self.copy_button = tk.Button(
            self.button_frame, text="(7) Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.grid(row=0, column=1, padx=5, pady=5)

        # Save to Excel Button
        self.save_button = tk.Button(
            self.button_frame, text="Save Generated Pattern to Excel", command=self.save_to_excel)
        self.save_button.grid(row=0, column=2, padx=5, pady=5)

        # Reset Button
        self.reset_button = tk.Button(
            self.button_frame, text="Reset", command=self.reset_fields)
        self.reset_button.grid(row=0, column=3, padx=5, pady=5)

        # New Button to create the 180-Vessel Version
        self.create_180_button = tk.Button(
            self.button_frame, text="Also create a 180-Vessel Version", command=self.create_180_version)
        self.create_180_button.grid(row=1, column=0, columnspan=4, padx=5, pady=5)

        # Generated Pattern
        self.output_label = tk.Label(self, text="Generated Pattern: For column G")
        self.output_label.grid(row=7, column=0, columnspan=3, sticky="w")
        self.output_text = tk.Text(self, height=6, width=70)
        self.output_text.grid(row=8, column=0, columnspan=3)

        # Configure grid weights for proper resizing
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
    

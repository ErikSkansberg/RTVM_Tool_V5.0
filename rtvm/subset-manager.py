# rtvm/gui/tools/subset_manager.py - Tool for managing RTVM subsets

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pandas as pd
import logging
import os
import shutil
import threading
import queue
from openpyxl import load_workbook
from copy import copy
from typing import Dict, List, Optional, Set, Tuple, Any

from rtvm.utils.config import config

logger = logging.getLogger(__name__)

class SubsetManager:
    """
    Tool for creating and managing subsets of RTVM data, 
    organized by SWBS groups.
    """
    
    def __init__(self, master: tk.Widget, app):
        """
        Initialize the subset manager.
        
        Args:
            master: The parent widget
            app: The main application instance
        """
        self.master = master
        self.app = app
        
        # Create and show the tool window
        self.create_window()
    
    def create_window(self):
        """Create the subset manager window."""
        self.window = tk.Toplevel(self.master)
        self.window.title("RTVM Subset Management")
        self.window.geometry("900x600")
        self.window.transient(self.master)  # Set as transient to main window
        
        # Explanation text
        explanation = (
            "This RTVM Subset Management tool allows you to:\n"
            "- Create a summary report of verification data\n"
            "- Export photos of the generated report\n"
            "- Create subsets of the RTVM based on predefined SWBS groups\n"
            "- Recombine these subsets back into a single file\n"
            "- Merge a single subset into the main RTVM file\n\n"
            "The data is taken from the currently loaded main RTVM file.\n"
            "Please select a base location first."
        )
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Explanation label
        ttk.Label(main_frame, text=explanation, justify="left").pack(pady=10, padx=10)
        
        # Top frame for controls
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # File info and base location controls
        ttk.Button(
            top_frame, text="Select Base Location", command=self.select_base_location
        ).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Label(top_frame, text="Current (New) File:").grid(row=0, column=1, sticky="w")
        self.file_name_var = tk.StringVar(
            value=self.app.model.excel_file_path if self.app.model.excel_file_path else "No File Loaded"
        )
        ttk.Label(top_frame, textvariable=self.file_name_var, width=50).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # PMR Number frame
        pmr_frame = ttk.Frame(main_frame)
        pmr_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(pmr_frame, text="PMR Number:").grid(row=0, column=0, sticky="w")
        self.pmr_var = tk.StringVar()
        ttk.Entry(pmr_frame, textvariable=self.pmr_var, width=10).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Template file selection
        ttk.Label(pmr_frame, text="Template File:").grid(row=1, column=0, sticky="w")
        self.template_file_var = tk.StringVar(
            value=config.get("paths", "template_file_path", "No Template Selected")
        )
        ttk.Label(pmr_frame, textvariable=self.template_file_var, width=50).grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        ttk.Button(
            pmr_frame, text="Select Template", command=self.select_template_file
        ).grid(row=1, column=3, padx=5, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Operation buttons
        ttk.Button(
            button_frame, text="Create Summary Report", command=self.create_summary_report
        ).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Button(
            button_frame, text="Export Photos of Report", command=self.export_photos_of_report
        ).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(
            button_frame, text="Create Subsets", command=self.create_subsets
        ).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(
            button_frame, text="Recombine Subsets", command=self.recombine_subsets
        ).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(
            button_frame, text="Merge Single Subset", command=self.merge_single_subset
        ).grid(row=0, column=4, padx=5, pady=5)
        
        # Progress frame (initially hidden)
        self.progress_frame = ttk.Frame(main_frame, padding="10")
        self.progress_frame.pack(fill=tk.X, padx=10, pady=10)
        self.progress_frame.pack_forget()  # Hide initially
        
        ttk.Label(self.progress_frame, text="Processing...").pack(side=tk.LEFT, padx=5)
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, orient='horizontal', length=400, mode='determinate'
        )
        self.progress_bar.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.progress_label = ttk.Label(self.progress_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT, padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Operation Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(log_frame, height=10, width=80)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar for log text
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.window, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load and set the assigned verification cells
        self.set_assigned_verification_cells()
        
        # Initialize data storage
        self.figures_data = []
        self.selected_base_path = config.get("paths", "last_output_directory", None)
        if self.selected_base_path:
            self.log(f"Base location loaded from config: {self.selected_base_path}")
    
    def log(self, message):
        """
        Add a message to the log text widget.
        
        Args:
            message: The message to log
        """
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)  # Scroll to the end
        logger.info(message)
    
    def set_assigned_verification_cells(self):
        """Load assigned verification cells from the data model."""
        # Check if the data model is loaded
        if self.app.model.df is None:
            self.log("No main file loaded. Please upload a main file before using this tool.")
            self.assigned_verification_cells = []
            return
        
        assigned_column = "Assigned Verification Documents"
        if assigned_column in self.app.model.df.columns:
            self.assigned_verification_cells = self.app.model.df[assigned_column].tolist()
            self.log(f"Loaded {len(self.assigned_verification_cells)} assigned verification cells")
        else:
            self.log(f"Column '{assigned_column}' not found in the loaded DataFrame.")
            self.assigned_verification_cells = []
    
    def select_base_location(self):
        """Select a base directory for PMR-related files and subsets."""
        selected_directory = filedialog.askdirectory(title="Select Base Directory for PMR Files")
        if selected_directory:
            self.selected_base_path = selected_directory
            config.set("paths", "last_output_directory", selected_directory)
            self.log(f"Base location set to: {self.selected_base_path}")
        else:
            self.log("No base location selected.")
    
    def select_template_file(self):
        """Select a template Excel file for subset creation."""
        template_file_path = filedialog.askopenfilename(
            title="Select Template Excel File",
            filetypes=[("Excel files", "*.xls;*.xlsx")]
        )
        if template_file_path:
            self.template_file_var.set(os.path.basename(template_file_path))
            config.set("paths", "template_file_path", template_file_path)
            self.log(f"Template file selected: {template_file_path}")
        else:
            self.log("No template file selected.")
    
    def get_pmr_number(self):
        """
        Get the PMR number from the entry field or prompt the user if not set.
        
        Returns:
            int or None: The PMR number or None if canceled
        """
        pmr_number = self.pmr_var.get().strip()
        if pmr_number:
            try:
                return int(pmr_number)
            except ValueError:
                self.log(f"Invalid PMR number: {pmr_number}. Please enter a valid integer.")
                return None
        
        # Prompt user if not set
        pmr_number = simpledialog.askinteger("PMR Number", "Enter the PMR number:")
        if pmr_number is not None:
            self.pmr_var.set(str(pmr_number))
        return pmr_number
    
    def get_swbs_group(self, detailed_location):
        """
        Determine the SWBS group from a detailed location string.
        
        Args:
            detailed_location: The detailed location string
            
        Returns:
            str: The SWBS group or "Default SWBS" if not found
        """
        # Look for SWBS keywords in the detailed location
        if "SWBS" in detailed_location:
            # Extract the SWBS identifier (e.g., "SWBS 100")
            import re
            match = re.search(r'SWBS\s+\d+', detailed_location)
            if match:
                return match.group(0)
        
        return "Default SWBS"
    
    def extract_detailed_location(self, assigned_docs):
        """
        Extract the detailed location from the assigned documents text.
        
        Args:
            assigned_docs: The assigned documents text
            
        Returns:
            str: The detailed location or default text if not found
        """
        if pd.isna(assigned_docs) or not isinstance(assigned_docs, str):
            return "Location Not Provided"
        
        # Look for "Detailed Location:" in the text
        lines = assigned_docs.split('\n')
        for line in lines:
            if "Detailed Location:" in line:
                _, location = line.split(':', 1)
                return location.strip()
        
        return str(assigned_docs)
    
    def create_summary_report(self):
        """Generate a summary report with pie charts for verification data."""
        if not self.assigned_verification_cells:
            self.log("No assigned verification cells available. Please load a main file first.")
            return
        
        pmr_number = self.get_pmr_number()
        if pmr_number is None:
            return
        
        if not self.selected_base_path:
            self.log("Please select a base location first.")
            return
        
        # Show progress
        self.status_var.set("Creating summary report...")
        self.show_progress_frame(0, 100)
        self.progress_label.config(text="Processing data...")
        
        # Start processing in a background thread
        threading.Thread(
            target=self._create_summary_report_thread,
            args=(pmr_number,),
            daemon=True
        ).start()
    
    def _create_summary_report_thread(self, pmr_number):
        """
        Background thread for creating the summary report.
        
        Args:
            pmr_number: The PMR number to use
        """
        try:
            # Collect data from all Assigned Verification Documents
            self.log(f"Creating summary report for PMR {pmr_number}...")
            data_list = []
            
            for i, cell_content in enumerate(self.assigned_verification_cells):
                self.update_progress(i, len(self.assigned_verification_cells), f"Processing cell {i+1}/{len(self.assigned_verification_cells)}")
                
                # Convert cell_content to string to avoid float error
                if pd.isna(cell_content):
                    continue
                cell_str = str(cell_content)
                if not cell_str or cell_str.strip().lower() == "nan":
                    continue
                
                # Split entries separated by lines of underscores
                entries = cell_str.split('______________________')
                for entry in entries:
                    entry = entry.strip()
                    if not entry:
                        continue
                    
                    # Initialize variables
                    data = {
                        'Object Identifier': "",
                        'DI Number': "",
                        'Government Assessed Status': "",
                        'Contractor Assessed Status': ""
                    }
                    
                    # Split entry into lines
                    lines = entry.split('\n')
                    for line in lines:
                        line = line.strip()
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            if key in data:
                                data[key] = value
                    
                    data_list.append(data)
            
            # Now, data_list contains all the entries
            if not data_list:
                self.log("No Assigned Verification Documents data found.")
                self.hide_progress_frame()
                self.status_var.set("Failed to create report: No data found")
                return
            
            # Convert to a DataFrame
            df_data = pd.DataFrame(data_list)
            
            # Get the SWBS groups from config
            swbs_groups = config.get("swbs_groups", None)
            if not swbs_groups:
                self.log("SWBS group configuration not found. Using default groups.")
                # Default SWBS groups (simplified for example)
                swbs_groups = {
                    'SWBS 000': ['040-001', '042-001'],
                    'SWBS 100': ['100-001', '100-002'],
                    'SWBS 200': ['200-001', '200-003']
                }
            
            # Create the PMR folder
            pmr_folder = os.path.join(self.selected_base_path, f"PMR {pmr_number}")
            os.makedirs(pmr_folder, exist_ok=True)
            self.log(f"Created PMR folder: {pmr_folder}")
            
            # Create report data
            self.figures_data = []
            
            # Overall Government Assessed Status
            gov_status_counts = df_data['Government Assessed Status'].value_counts()
            
            # Define colors
            status_colors = {
                'Disagree': 'red',
                'Agree': 'green',
                'Pending Review': 'orange',
                'Awaiting Input': 'blue'
            }
            
            gov_colors = [status_colors.get(status, 'grey') for status in gov_status_counts.index]
            
            # Store data for exporting
            self.figures_data.append({
                'swbs': 'Overall Status',
                'chart_type': 'Government Assessed Status',
                'counts': gov_status_counts.values,
                'labels': gov_status_counts.index.tolist(),
                'colors': gov_colors,
                'table_data': gov_status_counts.reset_index().values.tolist(),
                'table_columns': ['Status', 'Count']
            })
            
            # Overall Contractor Assessed Status
            contractor_status_counts = df_data['Contractor Assessed Status'].value_counts()
            
            # Define colors for Contractor Assessed Status
            contractor_status_colors = {
                'Satisfactory': 'green',
                'SAT': 'green',
                'Unsatisfactory': 'red',
                'UNSAT': 'red',
                'TBD': 'grey'
            }
            
            contractor_colors = [contractor_status_colors.get(status, 'grey') for status in contractor_status_counts.index]
            
            self.figures_data.append({
                'swbs': 'Overall Status',
                'chart_type': 'Contractor Assessed Status',
                'counts': contractor_status_counts.values,
                'labels': contractor_status_counts.index.tolist(),
                'colors': contractor_colors,
                'table_data': contractor_status_counts.reset_index().values.tolist(),
                'table_columns': ['Status', 'Count']
            })
            
            # Overall DI Number Distribution
            di_number_counts = df_data['DI Number'].value_counts()
            
            self.figures_data.append({
                'swbs': 'Overall Status',
                'chart_type': 'DI Number Distribution',
                'counts': di_number_counts.values,
                'labels': di_number_counts.index.tolist(),
                'colors': None,  # No specific colors
                'table_data': di_number_counts.reset_index().values.tolist(),
                'table_columns': ['DI Number', 'Count']
            })
            
            # For each SWBS group, create statistics
            for swbs, di_numbers in swbs_groups.items():
                # Strip spaces from swbs to avoid mismatch
                swbs = swbs.strip()
                
                # Filter the data for this SWBS group
                df_swbs = df_data[df_data['DI Number'].isin(di_numbers)]
                if df_swbs.empty:
                    continue
                
                # Government Assessed Status for SWBS
                gov_status_counts_swbs = df_swbs['Government Assessed Status'].value_counts()
                gov_colors_swbs = [status_colors.get(status, 'grey') for status in gov_status_counts_swbs.index]
                
                self.figures_data.append({
                    'swbs': swbs.replace('SWBS ', ''),
                    'chart_type': 'Government Assessed Status',
                    'counts': gov_status_counts_swbs.values,
                    'labels': gov_status_counts_swbs.index.tolist(),
                    'colors': gov_colors_swbs,
                    'table_data': gov_status_counts_swbs.reset_index().values.tolist(),
                    'table_columns': ['Status', 'Count']
                })
                
                # Contractor Assessed Status for SWBS
                contractor_status_counts_swbs = df_swbs['Contractor Assessed Status'].value_counts()
                contractor_colors_swbs = [contractor_status_colors.get(status, 'grey') for status in contractor_status_counts_swbs.index]
                
                self.figures_data.append({
                    'swbs': swbs.replace('SWBS ', ''),
                    'chart_type': 'Contractor Assessed Status',
                    'counts': contractor_status_counts_swbs.values,
                    'labels': contractor_status_counts_swbs.index.tolist(),
                    'colors': contractor_colors_swbs,
                    'table_data': contractor_status_counts_swbs.reset_index().values.tolist(),
                    'table_columns': ['Status', 'Count']
                })
                
                # DI Number Distribution for SWBS
                di_number_counts_swbs = df_swbs['DI Number'].value_counts()
                
                self.figures_data.append({
                    'swbs': swbs.replace('SWBS ', ''),
                    'chart_type': 'DI Number Distribution',
                    'counts': di_number_counts_swbs.values,
                    'labels': di_number_counts_swbs.index.tolist(),
                    'colors': None,  # No specific colors
                    'table_data': di_number_counts_swbs.reset_index().values.tolist(),
                    'table_columns': ['DI Number', 'Count']
                })
            
            self.hide_progress_frame()
            self.log(f"Summary report created with {len(self.figures_data)} charts")
            self.status_var.set("Report created successfully")
            
        except Exception as e:
            logger.error(f"Error creating summary report: {e}", exc_info=True)
            self.log(f"Error creating summary report: {str(e)}")
            self.hide_progress_frame()
            self.status_var.set("Error creating report")
    
    def export_photos_of_report(self):
        """Export pie chart photos and data from the summary report."""
        if not hasattr(self, 'figures_data') or not self.figures_data:
            self.log("No report generated. Please create the summary report first.")
            return
        
        pmr_number = self.get_pmr_number()
        if pmr_number is None:
            return
        
        if not self.selected_base_path:
            self.log("Please select a base location first.")
            return
        
        # Show progress
        self.status_var.set("Exporting photos...")
        self.show_progress_frame(0, len(self.figures_data))
        
        # Start processing in a background thread
        threading.Thread(
            target=self._export_photos_thread,
            args=(pmr_number,),
            daemon=True
        ).start()
    
    def _export_photos_thread(self, pmr_number):
        """
        Background thread for exporting report photos.
        
        Args:
            pmr_number: The PMR number to use
        """
        try:
            import matplotlib.pyplot as plt
            
            pmr_folder = os.path.join(self.selected_base_path, f"PMR {pmr_number}")
            if not os.path.exists(pmr_folder):
                os.makedirs(pmr_folder)
            
            self.log(f"Exporting photos to {pmr_folder}...")
            
            for i, data in enumerate(self.figures_data):
                self.update_progress(i, len(self.figures_data), f"Exporting chart {i+1}/{len(self.figures_data)}")
                
                swbs = data['swbs']
                chart_type = data['chart_type']
                counts = data['counts']
                labels = data['labels']
                colors = data['colors']
                table_data = data['table_data']
                table_columns = data['table_columns']
                
                # Strip spaces from swbs to ensure exact match
                swbs = swbs.strip()
                
                if swbs == 'Overall Status':
                    swbs_folder = os.path.join(pmr_folder, "Overall Status")
                else:
                    swbs_folder = os.path.join(pmr_folder, f"{swbs} SWBS", "Status Photos")
                
                if not os.path.exists(swbs_folder):
                    os.makedirs(swbs_folder)
                
                # Recreate the figure
                fig, ax = plt.subplots(figsize=(6, 6))
                if colors:
                    ax.pie(
                        counts, labels=labels,
                        autopct='%1.1f%%', startangle=90, colors=colors
                    )
                else:
                    ax.pie(
                        counts, labels=labels,
                        autopct='%1.1f%%', startangle=90
                    )
                ax.axis('equal')
                ax.set_title(f"{swbs} - {chart_type}")
                
                # Save the figure
                filename = f"PMR {pmr_number} - SWBS {swbs} - {chart_type}.png"
                save_path = os.path.join(swbs_folder, filename)
                
                # Ensure directories exist before saving
                if not os.path.exists(swbs_folder):
                    os.makedirs(swbs_folder)
                
                fig.savefig(save_path, bbox_inches='tight')
                plt.close(fig)
                
                # Prepare data for Excel export
                if swbs == 'Overall Status':
                    excel_filename = f"PMR {pmr_number} - Overall Status - Raw Data Export.xlsx"
                    excel_save_path = os.path.join(swbs_folder, excel_filename)
                else:
                    excel_filename = f"PMR {
# rtvm/gui/tools/disagreement_manager.py - Tool for managing disagreements

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pandas as pd
import logging
import os
import re
import subprocess
import platform
import threading
import queue
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import acroform
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from rtvm.utils.config import config

logger = logging.getLogger(__name__)

class DisagreementManager:
    """
    Tool for managing disagreements between contractors and government assessments.
    Creates formal disagreement reports as PDFs or Excel files and manages 
    a database of disagreement reports.
    """
    
    def __init__(self, master: tk.Widget, app):
        """
        Initialize the disagreement manager.
        
        Args:
            master: The parent widget
            app: The main application instance
        """
        self.master = master
        self.app = app
        
        # Initialize variables
        self.disagreement_items = []
        
        # Create and show the tool window
        self.create_window()
    
    def create_window(self):
        """Create the disagreement manager window."""
        self.window = tk.Toplevel(self.master)
        self.window.title("Disagreement Manager - Batch Reports")
        self.window.geometry("900x600")
        self.window.transient(self.master)  # Set as transient to main window
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Explanation text
        explanation = (
            "This Disagreement Manager tool helps manage disagreements between "
            "contractor and government assessments. It can:\n"
            "- Create formal disagreement reports as PDFs or Excel files\n"
            "- Organize reports by tracking number/SWBS group\n"
            "- Find and open existing disagreement reports\n\n"
            "The tool searches for rows where the Government Assessed Status is 'Disagree' "
            "and the Object Status is 'Accepted'."
        )
        ttk.Label(main_frame, text=explanation, justify="left").pack(pady=10, padx=10)
        
        # Top frame for controls
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Database location selection
        ttk.Button(
            top_frame, text="Select Database Location", command=self.select_database_location
        ).grid(row=0, column=0, padx=5, pady=5)
        
        self.db_location_var = tk.StringVar(
            value=config.get("paths", "disagreement_reports_folder", "No location selected")
        )
        ttk.Label(top_frame, textvariable=self.db_location_var, width=50).grid(
            row=0, column=1, padx=5, pady=5, sticky="w"
        )
        
        # Button row
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            button_frame, text="B.1 Create Disagreement Reports", command=self.create_disagreement_reports
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            button_frame, text="Refresh Report List", command=self.refresh_report_list
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Report table frame
        table_frame = ttk.LabelFrame(main_frame, text="Disagreement Reports", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create report table
        columns = ("SpecID", "Status", "Location", "Report_File")
        self.report_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.report_tree.heading("SpecID", text="Spec ID")
        self.report_tree.heading("Status", text="Status")
        self.report_tree.heading("Location", text="Location")
        self.report_tree.heading("Report_File", text="Report File")
        
        self.report_tree.column("SpecID", width=120)
        self.report_tree.column("Status", width=100)
        self.report_tree.column("Location", width=150)
        self.report_tree.column("Report_File", width=400)
        
        self.report_tree.bind("<Double-1>", self.on_report_double_click)
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar for report table
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.report_tree.yview)
        self.report_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
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
        
        self.log_text = tk.Text(log_frame, height=8, width=80)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar for log text
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.window, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Find disagreements in the current data
        self.find_disagreements()
        
        # Refresh the report list
        self.refresh_report_list()
    
    def log(self, message):
        """
        Add a message to the log text widget.
        
        Args:
            message: The message to log
        """
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)  # Scroll to the end
        logger.info(message)
    
    def select_database_location(self):
        """Select a location for storing disagreement reports."""
        db_location = filedialog.askdirectory(
            title="Select Database Location for Disagreement Reports"
        )
        if db_location:
            self.db_location_var.set(db_location)
            config.set("paths", "disagreement_reports_folder", db_location)
            self.log(f"Database location set to: {db_location}")
            
            # Refresh the report list with the new location
            self.refresh_report_list()
    
    def find_disagreements(self):
        """Find disagreements in the current data."""
        if self.app.model.df is None:
            self.log("No main Excel file is loaded. Please upload a main file first.")
            return
        
        # Filter rows where Government Assessed Status = "Disagree" and Object Status = "Accepted"
        self.disagreement_items = []
        
        for item in self.app.model.status_data:
            government_status = item.get('government_status', '').strip().lower()
            object_status = item.get('object_status', '').strip().lower()
            
            if government_status == 'disagree' and object_status == 'accepted':
                self.disagreement_items.append(item)
        
        self.log(f"Found {len(self.disagreement_items)} rows with disagreements.")
    
    def refresh_report_list(self):
        """Scan the database folder for PDF disagreement reports and update the treeview."""
        # Get the database location
        db_location = config.get("paths", "disagreement_reports_folder", None)
        if not db_location or not os.path.exists(db_location):
            self.log("No valid database location set. Please select a database folder first.")
            return
        
        # Clear the treeview
        for child in self.report_tree.get_children():
            self.report_tree.delete(child)
        
        # Walk the folder and collect report files
        self.status_var.set("Scanning for reports...")
        report_count = 0
        
        for root_dir, dirs, files in os.walk(db_location):
            for file in files:
                if file.endswith(".pdf") and "Disagreement Report - WCC-SPEC-" in file:
                    # Extract the spec ID from the filename
                    m = re.search(r"Disagreement Report - (WCC-SPEC-[^.]+)\.pdf", file)
                    if m:
                        spec_id = m.group(1)
                    else:
                        spec_id = file
                    
                    file_path = os.path.join(root_dir, file)
                    
                    # Extract location (folder path relative to db_location)
                    rel_path = os.path.relpath(root_dir, db_location)
                    location = rel_path if rel_path != "." else ""
                    
                    # Get status - for now, just set as "Pending"
                    # Could later parse PDF forms to get actual status
                    status = "Pending"
                    
                    # Add to treeview
                    self.report_tree.insert(
                        "", "end", 
                        values=(spec_id, status, location, file_path)
                    )
                    report_count += 1
                
                elif file.endswith(".xlsx") and "Disagreement Report - WCC-SPEC-" in file:
                    # Also include Excel-based disagreement reports
                    m = re.search(r"Disagreement Report - (WCC-SPEC-[^.]+)\.xlsx", file)
                    if m:
                        spec_id = m.group(1)
                    else:
                        spec_id = file
                    
                    file_path = os.path.join(root_dir, file)
                    
                    # Extract location (folder path relative to db_location)
                    rel_path = os.path.relpath(root_dir, db_location)
                    location = rel_path if rel_path != "." else ""
                    
                    # Get status - for Excel, just set as "Excel Format"
                    status = "Excel Format"
                    
                    # Add to treeview
                    self.report_tree.insert(
                        "", "end", 
                        values=(spec_id, status, location, file_path)
                    )
                    report_count += 1
        
        self.status_var.set(f"Found {report_count} disagreement reports")
        self.log(f"Found {report_count} existing disagreement reports in {db_location}")
    
    def on_report_double_click(self, event):
        """Handle double-click events on the report treeview."""
        item_id = self.report_tree.identify_row(event.y)
        if item_id:
            values = self.report_tree.item(item_id, "values")
            if values and len(values) >= 4:
                report_file = values[3]
                if os.path.exists(report_file):
                    try:
                        # Open the file with the default application
                        if platform.system() == 'Windows':
                            os.startfile(report_file)
                        elif platform.system() == 'Darwin':  # macOS
                            subprocess.call(('open', report_file))
                        else:  # Linux and other Unix-like
                            subprocess.call(('xdg-open', report_file))
                        
                        self.log(f"Opened report: {report_file}")
                    except Exception as e:
                        logger.error(f"Failed to open file: {e}", exc_info=True)
                        messagebox.showerror("Error", f"Failed to open file: {str(e)}")
                else:
                    messagebox.showerror("File Not Found", f"The file does not exist:\n{report_file}")
    
    def create_disagreement_reports(self):
        """Create disagreement reports for all found disagreements."""
        if not self.disagreement_items:
            messagebox.showinfo("No Disagreements", "No disagreements found to report.")
            return
        
        # Get the database location
        db_location = config.get("paths", "disagreement_reports_folder", None)
        if not db_location:
            # Prompt to select a location
            db_location = filedialog.askdirectory(title="Select Database Location for Disagreement Reports")
            if not db_location:
                self.log("No database location selected. Cannot create reports.")
                return
            config.set("paths", "disagreement_reports_folder", db_location)
            self.db_location_var.set(db_location)
        
        # Ask user for preferred format: PDF or Excel
        format_choice = simpledialog.askstring(
            "Report Format",
            "Choose report format: PDF or Excel",
            initialvalue="PDF"
        )
        
        if not format_choice:
            return
        
        format_choice = format_choice.upper()
        if format_choice not in ["PDF", "EXCEL"]:
            messagebox.showerror("Invalid Format", "Please choose either 'PDF' or 'Excel'.")
            return
        
        # Group disagreement items by VeriDoc ID
        grouped_items = {}
        for item in self.disagreement_items:
            veridoc = item.get("veridoc_number", "").strip().lower()
            if veridoc:
                grouped_items.setdefault(veridoc, []).append(item)
        
        # Show progress
        self.status_var.set(f"Creating {format_choice} reports...")
        self.show_progress_frame(0, len(grouped_items))
        
        # Start processing in a background thread
        threading.Thread(
            target=self._create_reports_thread,
            args=(grouped_items, db_location, format_choice),
            daemon=True
        ).start()
    
    def _create_reports_thread(self, grouped_items, db_location, format_choice):
        """
        Background thread for creating disagreement reports.
        
        Args:
            grouped_items: Dictionary of grouped disagreement items
            db_location: Path to save reports
            format_choice: "PDF" or "EXCEL"
        """
        try:
            total_items = len(grouped_items)
            processed = 0
            created_reports = []
            
            for veridoc, items in grouped_items.items():
                processed += 1
                percent = int((processed / total_items) * 100)
                self.update_progress(processed, total_items, f"Creating report {processed}/{total_items} ({percent}%)")
                
                # Check if any item in this group has government_status "agree" - if so, skip
                if any(item.get("government_status", "").strip().lower() == "agree" for item in items):
                    self.log(f"Skipping {veridoc} because some items have 'agree' status")
                    continue
                
                # Pick a representative item (the first one)
                rep_item = items[0]
                
                # Create the report
                if format_choice == "PDF":
                    result = self.generate_pdf_for_disagreement(rep_item, db_location)
                else:  # EXCEL
                    result = self.generate_excel_for_disagreement(rep_item, db_location)
                
                if result:
                    pdf_path, swbs_group = result
                    created_reports.append({
                        "path": pdf_path,
                        "swbs": swbs_group,
                        "veridoc": veridoc
                    })
                    self.log(f"Created report for {veridoc} in {swbs_group}")
                else:
                    self.log(f"Failed to create report for {veridoc}")
            
            # Summary
            if created_reports:
                self.log(f"Created {len(created_reports)} disagreement reports")
                self.window.after(0, lambda: messagebox.showinfo(
                    "Reports Created",
                    f"Created {len(created_reports)} disagreement reports."
                ))
            else:
                self.log("No reports were created")
                self.window.after(0, lambda: messagebox.showinfo(
                    "No Reports Created",
                    "No disagreement reports were created."
                ))
            
            # Refresh the report list
            self.window.after(0, self.refresh_report_list)
            
            self.hide_progress_frame()
            self.status_var.set("Report creation completed")
            
        except Exception as e:
            logger.error(f"Error creating reports: {e}", exc_info=True)
            self.log(f"Error creating reports: {str(e)}")
            self.hide_progress_frame()
            self.status_var.set("Error creating reports")
            
            self.window.after(0, lambda: messagebox.showerror(
                "Error",
                f"Failed to create reports:\n\n{str(e)}"
            ))
    
    def generate_pdf_for_disagreement(self, item, output_folder):
        """
        Generate a PDF disagreement report for an item.
        
        Args:
            item: The disagreement item
            output_folder: Where to save the PDF
            
        Returns:
            Tuple of (pdf_path, swbs_group) or None if failed
        """
        try:
            # Set the current row
            row_index = item['row_index']
            self.app.current_row = row_index
            self.app.update_ui_after_navigation()
            
            # Get DOORS SPEC ID from the first column
            doors_spec_id = self.app.model.df.iloc[row_index, 0]
            if pd.isna(doors_spec_id):
                doors_spec_id = ""
            elif not isinstance(doors_spec_id, str):
                doors_spec_id = str(doors_spec_id)
            
            # Retrieve the specification text
            spec_text = ""
            if len(self.app.model.df.columns) > 1:
                spec_text = self.app.model.df.iloc[row_index, 1]
                if pd.isna(spec_text):
                    spec_text = ""
                elif not isinstance(spec_text, str):
                    spec_text = str(spec_text)
            
            # Get Contractor Proposed Change Comment History (column I, index 8)
            contractor_history_content = ""
            if len(self.app.model.df.columns) > 8:
                val = self.app.model.df.iloc[row_index, 8]
                if pd.isna(val):
                    val = ""
                contractor_history_content = str(val)
            
            # Get Government Adjudication Comment History (column J, index 9)
            gov_history_content = ""
            if len(self.app.model.df.columns) > 9:
                val = self.app.model.df.iloc[row_index, 9]
                if pd.isna(val):
                    val = ""
                gov_history_content = str(val)
            
            # Use the "Assigned Verification Documents" cell to extract the Detailed Location
            try:
                row = self.app.model.df.iloc[row_index]
                assigned_docs = row["Assigned Verification Documents"]
            except Exception:
                assigned_docs = ""
            
            detailed_location = self.extract_detailed_location(assigned_docs)
            swbs_group = self.get_swbs_group(detailed_location)
            
            # Determine tracking number and PDF filename
            tracking_number = self.generate_tracking_number(item)
            filename = f"Disagreement Report - WCC-SPEC-{tracking_number}.pdf"
            
            # Create a subfolder based on SWBS group
            target_folder = os.path.join(output_folder, swbs_group)
            os.makedirs(target_folder, exist_ok=True)
            pdf_path = os.path.join(target_folder, filename)
            
            # Page setup
            width, height = letter
            left_margin = 72
            right_margin = 72
            top_margin = 50
            bottom_margin = 72
            usable_width = width - (left_margin + right_margin)
            
            # Build breakdown table data from self.app.table
            items_ids = self.app.table.get_children()
            breakdown_data = [["VeriDoc Number", "DI Number", "CDRL Subtitle", "Government Assessed Status"]]
            for line_id in items_ids:
                values = self.app.table.item(line_id, 'values')
                breakdown_data.append([values[0], values[1], values[2], values[5]])
            
            # Count agreements and disagreements
            agree_count = 0
            disagree_count = 0
            for i in range(1, len(breakdown_data)):
                gov_status = str(breakdown_data[i][3]).strip().lower()
                if gov_status == "agree":
                    agree_count += 1
                elif gov_status == "disagree":
                    disagree_count += 1
            
            # Extract rows with disagreement
            disagreement_rows = []
            for i in range(1, len(breakdown_data)):
                if str(breakdown_data[i][3]).strip().lower() == "disagree":
                    disagreement_rows.append(breakdown_data[i])
            
            # Set up the canvas and acroform
            c = canvas.Canvas(pdf_path, pagesize=letter)
            form = acroform.AcroForm(c)
            
            def wrap_text_to_pdf(c, text, x, y, max_width):
                """Helper function to wrap text in the PDF."""
                chars_per_line = int(max_width / 6)  # Approximation for 12pt font
                
                # Split the text into paragraphs
                paragraphs = text.split('\n')
                
                for paragraph in paragraphs:
                    # Wrap each paragraph to fit width
                    import textwrap
                    wrapped_lines = textwrap.wrap(paragraph, width=chars_per_line)
                    
                    if not wrapped_lines:
                        # Empty line - just advance vertically
                        y -= 14
                        continue
                    
                    for wline in wrapped_lines:
                        if y < bottom_margin:
                            c.showPage()
                            c.setFont("Helvetica", 12)
                            y = height - top_margin
                        c.drawString(x, y, wline)
                        y -= 14
                
                return y
            
            # Write header information
            c.setFont("Helvetica", 8)
            y = height - top_margin
            current_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.drawString(left_margin, y, f"Date/Time: {current_dt}")
            y -= 10
            c.drawString(left_margin, y, "Contract: 70Z02323D93270001")
            y -= 10
            
            distribution_text = (
                "DISTRIBUTION STATEMENT D: DISTRIBUTION AUTHORIZED TO DHS/CG/DOD AND THEIR "
                "CONTRACTORS ONLY DUE TO ADMINISTRATIVE OR OPERATIONAL USE (5 OCT 2022). "
                "OTHER REQUESTS SHALL BE REFERRED TO COMMANDANT (CG-9327)."
            )
            destruction_text = (
                "DESTRUCTION NOTICE: DESTROY THIS DOCUMENT BY ANY METHOD THAT WILL "
                "PREVENT DISCLOSURE OF CONTENTS OR RECONSTRUCTION OF THE DOCUMENT."
            )
            y = wrap_text_to_pdf(c, distribution_text, left_margin, y, usable_width)
            y -= 10
            y = wrap_text_to_pdf(c, destruction_text, left_margin, y, usable_width)
            
            # DOORS SPEC ID Summary Table
            id_table_data = [
                ["DOORS SPEC ID", "Excel Row", "Total Agreements", "Total Disagreements"],
                [doors_spec_id, str(row_index + 2), str(agree_count), str(disagree_count)],
            ]
            id_table = Table(id_table_data, colWidths=[130, 60, 100, 120])
            id_style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.
# rtvm/gui/tools/comair_tool.py - Excel file comparison tool

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import logging
import os
from typing import Dict, List, Optional, Set, Tuple, Any

logger = logging.getLogger(__name__)

class CompairTool:
    """
    Tool for comparing two Excel files and identifying differences.
    """
    
    def __init__(self, master: tk.Widget, app):
        """
        Initialize the comparison tool.
        
        Args:
            master: The parent widget
            app: The main application instance
        """
        self.master = master
        self.app = app
        
        # Create and show the tool window
        self.create_window()
    
    def create_window(self):
        """Create the comparison tool window."""
        self.window = tk.Toplevel(self.master)
        self.window.title("Compair Tool")
        self.window.geometry("900x700")
        self.window.transient(self.master)  # Set as transient to main window
        
        # Create the file selection frame
        file_frame = ttk.Frame(self.window, padding="10")
        file_frame.pack(side=tk.TOP, fill=tk.X)
        
        # First file selection
        ttk.Label(file_frame, text="Select First Excel File:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.file1_entry = ttk.Entry(file_frame, width=50)
        self.file1_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file1).grid(row=0, column=2, padx=5, pady=5)
        
        # Second file selection
        ttk.Label(file_frame, text="Select Second Excel File:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.file2_entry = ttk.Entry(file_frame, width=50)
        self.file2_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file2).grid(row=1, column=2, padx=5, pady=5)
        
        # Sheet selection
        ttk.Label(file_frame, text="Sheet Name (optional):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.sheet_entry = ttk.Entry(file_frame, width=20)
        self.sheet_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(self.window, padding="10")
        button_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Compare and save buttons
        ttk.Button(button_frame, text="Compare Files", command=self.compare_files).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(button_frame, text="Save Results", command=self.save_comparison_results).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Results frame
        results_frame = ttk.Frame(self.window, padding="10")
        results_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Results table
        columns = ("Row", "Column", "Value in File 1", "Value in File 2")
        self.results_table = ttk.Treeview(results_frame, columns=columns, show="headings")
        self.results_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure columns
        for col in columns:
            self.results_table.heading(col, text=col)
            self.results_table.column(col, anchor='center', width=150)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_table.yview)
        self.results_table.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.window, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def browse_file1(self):
        """Browse for the first file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xls;*.xlsx")]
        )
        if file_path:
            self.file1_entry.delete(0, tk.END)
            self.file1_entry.insert(0, file_path)
    
    def browse_file2(self):
        """Browse for the second file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xls;*.xlsx")]
        )
        if file_path:
            self.file2_entry.delete(0, tk.END)
            self.file2_entry.insert(0, file_path)
    
    def compare_files(self):
        """Compare the two Excel files and display differences."""
        file1_path = self.file1_entry.get()
        file2_path = self.file2_entry.get()
        sheet_name = self.sheet_entry.get() or None  # Use None if no sheet specified
        
        if not file1_path or not file2_path:
            messagebox.showerror("Error", "Please select both Excel files to compare.")
            return
        
        try:
            # Update status
            self.status_var.set("Loading files...")
            self.window.update_idletasks()
            
            # Load the Excel files
            df1 = pd.read_excel(file1_path, sheet_name=sheet_name)
            df2 = pd.read_excel(file2_path, sheet_name=sheet_name)
            
            # Clear previous results
            self.results_table.delete(*self.results_table.get_children())
            
            # Update status
            self.status_var.set("Comparing files...")
            self.window.update_idletasks()
            
            # Compare the dataframes
            diff_df = self.get_differences(df1, df2)
            
            if diff_df.empty:
                self.status_var.set("No differences found")
                messagebox.showinfo("No Differences", "The two files are identical.")
            else:
                # Display differences in the results table
                for index, row in diff_df.iterrows():
                    self.results_table.insert(
                        "", "end", 
                        values=(
                            row['Row'], 
                            row['Column'], 
                            row['Value in File 1'], 
                            row['Value in File 2']
                        )
                    )
                self.status_var.set(f"Found {len(diff_df)} differences")
        
        except Exception as e:
            logger.error(f"Failed to compare Excel files: {e}", exc_info=True)
            self.status_var.set("Error comparing files")
            messagebox.showerror("Error", f"Failed to compare Excel files: {str(e)}")
    
    def get_differences(self, df1, df2):
        """
        Get differences between two DataFrames.
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            
        Returns:
            DataFrame containing differences
        """
        try:
            # Align the DataFrames
            df1, df2 = df1.align(df2, join='outer', axis=1)
            df1.fillna('', inplace=True)
            df2.fillna('', inplace=True)
            
            # Prepare a list to collect differences
            differences = []
            
            # Compare cell by cell
            for i in range(max(len(df1), len(df2))):
                for col in df1.columns:
                    # Skip if row doesn't exist in one DataFrame
                    if i >= len(df1) or i >= len(df2):
                        continue
                    
                    val1 = df1.iloc[i, df1.columns.get_loc(col)]
                    val2 = df2.iloc[i, df2.columns.get_loc(col)]
                    
                    # Convert both values to strings for comparison
                    if pd.isna(val1):
                        val1 = ''
                    if pd.isna(val2):
                        val2 = ''
                    val1_str = str(val1)
                    val2_str = str(val2)
                    
                    # Compare the string values
                    if val1_str != val2_str:
                        # Add to differences list
                        differences.append({
                            'Row': i + 2,  # +2 to account for 1-indexing and header row
                            'Column': col,
                            'Value in File 1': val1_str,
                            'Value in File 2': val2_str
                        })
            
            # Create the DataFrame from the list of differences
            diff_df = pd.DataFrame(differences, columns=['Row', 'Column', 'Value in File 1', 'Value in File 2'])
            return diff_df
            
        except Exception as e:
            logger.error(f"Error in get_differences: {e}", exc_info=True)
            raise
    
    def save_comparison_results(self):
        """Save the comparison results to an Excel file."""
        # Get the data from the results table
        rows = self.results_table.get_children()
        if not rows:
            messagebox.showinfo("No Data", "No differences to save.")
            return
        
        # Prepare data for DataFrame
        data = []
        for row_id in rows:
            row = self.results_table.item(row_id)['values']
            data.append(row)
        
        df = pd.DataFrame(data, columns=['Row', 'Column', 'Value in File 1', 'Value in File 2'])
        
        # Ask user for a file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Save Comparison Results"
        )
        
        if file_path:
            try:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", f"Results saved to {file_path}")
            except Exception as e:
                logger.error(f"Failed to save comparison results: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to save results: {str(e)}")

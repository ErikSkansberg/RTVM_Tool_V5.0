# rtvm/gui/charts.py - Chart visualization for RTVM data

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import logging
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple, Any

logger = logging.getLogger(__name__)

class PieChartWindow:
    """
    Window for displaying pie charts of RTVM data statistics.
    """
    
    def __init__(self, master: tk.Widget, model):
        """
        Initialize the pie chart window.
        
        Args:
            master: The parent widget
            model: The data model containing RTVM data
        """
        self.master = master
        self.model = model
        self.pie_chart_window = None
        
        # Initialize variables for filtering
        self.unique_object_statuses = self.model.unique_object_statuses
        self.unique_contractor_statuses = self.model.unique_contractor_statuses
        self.unique_government_statuses = self.model.unique_government_statuses
        
        # Initialize total counts for comparison
        self.compute_total_counts()
    
    def show(self):
        """Create and display the pie chart window."""
        # Create a new window
        self.pie_chart_window = tk.Toplevel(self.master)
        self.pie_chart_window.title("Pie Charts")
        self.pie_chart_window.geometry("1000x800")
        
        # Create filter frame
        filter_frame = ttk.Frame(self.pie_chart_window)
        filter_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # Object Status Filter
        ttk.Label(filter_frame, text="Object Status").pack(side=tk.LEFT, padx=5, pady=5)
        self.pie_object_status_var = tk.StringVar()
        self.pie_object_status_dropdown = ttk.Combobox(
            filter_frame,
            textvariable=self.pie_object_status_var,
            values=["Any"] + sorted(self.unique_object_statuses),
            state="readonly",
            width=15
        )
        self.pie_object_status_dropdown.pack(side=tk.LEFT)
        self.pie_object_status_var.set("Any")
        
        # Contractor Assessed Status Filter
        ttk.Label(filter_frame, text="Contractor Assessed Status").pack(side=tk.LEFT, padx=5, pady=5)
        self.pie_contractor_status_var = tk.StringVar()
        self.pie_contractor_status_dropdown = ttk.Combobox(
            filter_frame,
            textvariable=self.pie_contractor_status_var,
            values=["Any"] + sorted(self.unique_contractor_statuses),
            state="readonly",
            width=15
        )
        self.pie_contractor_status_dropdown.pack(side=tk.LEFT)
        self.pie_contractor_status_var.set("Any")
        
        # Government Assessed Status Filter
        ttk.Label(filter_frame, text="Government Assessed Status").pack(side=tk.LEFT, padx=5, pady=5)
        self.pie_government_status_var = tk.StringVar()
        self.pie_government_status_dropdown = ttk.Combobox(
            filter_frame,
            textvariable=self.pie_government_status_var,
            values=["Any"] + sorted(self.unique_government_statuses),
            state="readonly",
            width=15
        )
        self.pie_government_status_dropdown.pack(side=tk.LEFT)
        self.pie_government_status_var.set("Any")
        
        # Update Charts Button
        ttk.Button(
            filter_frame,
            text="Update Charts",
            command=self.update_pie_charts
        ).pack(side=tk.LEFT, padx=10)
        
        # Export Button
        ttk.Button(
            filter_frame,
            text="Export Charts",
            command=self.export_charts
        ).pack(side=tk.LEFT, padx=10)
        
        # Now create a frame to hold four charts in a 2×2 grid
        charts_frame = ttk.Frame(self.pie_chart_window)
        charts_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Create the four figures and embed them using grid
        self.object_status_fig = Figure(figsize=(4, 4), dpi=100)
        self.object_status_canvas = FigureCanvasTkAgg(self.object_status_fig, charts_frame)
        self.object_status_canvas.get_tk_widget().grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.contractor_status_fig = Figure(figsize=(4, 4), dpi=100)
        self.contractor_status_canvas = FigureCanvasTkAgg(self.contractor_status_fig, charts_frame)
        self.contractor_status_canvas.get_tk_widget().grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.government_status_fig = Figure(figsize=(4, 4), dpi=100)
        self.government_status_canvas = FigureCanvasTkAgg(self.government_status_fig, charts_frame)
        self.government_status_canvas.get_tk_widget().grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        self.gov_req_status_fig = Figure(figsize=(4, 4), dpi=100)
        self.gov_req_status_canvas = FigureCanvasTkAgg(self.gov_req_status_fig, charts_frame)
        self.gov_req_status_canvas.get_tk_widget().grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        # Optionally configure the grid so cells expand equally
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)
        charts_frame.rowconfigure(0, weight=1)
        charts_frame.rowconfigure(1, weight=1)
        
        # Create a frame for the counts table
        counts_frame = ttk.Frame(self.pie_chart_window)
        counts_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Create scrollable table for counts
        self.counts_table = ttk.Treeview(
            counts_frame,
            columns=("Status", "Count", "Total Count"),
            show="headings"
        )
        self.counts_table.heading("Status", text="Status")
        self.counts_table.heading("Count", text="Count")
        self.counts_table.heading("Total Count", text="Total Count")
        self.counts_table.column("Status", width=200, anchor="w")
        self.counts_table.column("Count", width=100, anchor="center")
        self.counts_table.column("Total Count", width=100, anchor="center")
        self.counts_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar for counts table
        scrollbar = ttk.Scrollbar(counts_frame, orient=tk.VERTICAL, command=self.counts_table.yview)
        self.counts_table.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Update the charts initially
        self.update_pie_charts()
    
    def update_pie_charts(self):
        """Update all pie charts based on the selected filters."""
        # Get the selected filters
        selected_object_status = self.pie_object_status_var.get()
        selected_contractor_status = self.pie_contractor_status_var.get()
        selected_government_status = self.pie_government_status_var.get()
        
        if selected_object_status == "Any":
            selected_object_status = ''
        if selected_contractor_status == "Any":
            selected_contractor_status = ''
        if selected_government_status == "Any":
            selected_government_status = ''
        
        # Filter the status data based on the selected filters (for the first three charts)
        filtered_items = []
        for item in self.model.status_data:
            object_match = True
            contractor_match = True
            government_match = True
            
            if selected_object_status:
                object_match = (item['object_status'] == selected_object_status)
            if selected_contractor_status:
                contractor_match = (item['contractor_status'] == selected_contractor_status)
            if selected_government_status:
                government_match = (item['government_status'] == selected_government_status)
            
            if object_match and contractor_match and government_match:
                filtered_items.append(item)
        
        filtered_statuses = {
            'object_status': [item['object_status'] for item in filtered_items],
            'contractor_status': [item['contractor_status'] for item in filtered_items],
            'government_status': [item['government_status'] for item in filtered_items]
        }
        
        # Plot the first three charts using the filtered data
        self.plot_pie_chart(self.object_status_fig, filtered_statuses['object_status'], 'Object Status')
        self.plot_pie_chart(self.contractor_status_fig, filtered_statuses['contractor_status'], 'Contractor Assessed Status')
        self.plot_pie_chart(self.government_status_fig, filtered_statuses['government_status'], 'Government Assessed Status')
        
        # --- Now compute the per-requirement overall government status ---
        # We will group by row index (each row is one requirement)
        from collections import defaultdict
        
        req_status = defaultdict(list)
        for item in self.model.status_data:
            row_idx = item['row_index']
            status = item['government_status']
            if isinstance(status, str):
                req_status[row_idx].append(status.strip().lower())
        
        # Define the order of precedence (lower number = higher precedence)
        precedence = {"agree": 1, "disagree": 2, "pending review": 3, "awaiting input": 4}
        
        overall_status_list = []
        for row_idx, statuses in req_status.items():
            overall = None
            min_rank = float('inf')
            for s in statuses:
                rank = precedence.get(s, 100)  # default to a high rank if unknown
                if rank < min_rank:
                    min_rank = rank
                    overall = s
            if overall:
                # Capitalize the first letter (so "agree" becomes "Agree", etc.)
                overall_status_list.append(overall.capitalize())
        
        # Plot the new pie chart using the overall status per requirement
        self.plot_pie_chart(self.gov_req_status_fig, overall_status_list, 'Government Assessed Status Per Requirement')
        
        # Redraw all canvases
        self.object_status_canvas.draw()
        self.contractor_status_canvas.draw()
        self.government_status_canvas.draw()
        self.gov_req_status_canvas.draw()
        
        # Update counts table
        self.update_counts_table(filtered_statuses)
    
    def plot_pie_chart(self, fig, data_list, title):
        """
        Plot a pie chart on the given figure.
        
        Args:
            fig: The matplotlib figure to plot on
            data_list: List of status values
            title: Title for the chart
        """
        # Clear the figure
        fig.clear()
        
        # Count occurrences of each status
        counter = Counter(data_list)
        labels = list(counter.keys())
        sizes = list(counter.values())
        
        # Define color mapping for statuses
        status_color_map = {
            'Agree': 'green',
            'Disagree': 'red',
            'Awaiting input': 'yellow',
            'Pending review': 'blue',
            'SAT': 'green',
            'UNSAT': 'red',
            'TBD': 'gray',
            'Accepted': 'lightblue',
            'Depreciated': 'darkgray',
            'Proposed add': 'orange',
            'Proposed delete': 'purple'
        }
        
        # We standardize each label by capitalizing it before checking the mapping
        colors = []
        for label in labels:
            label_cap = label.capitalize()
            colors.append(status_color_map.get(label_cap, 'gray'))
        
        # Handle the case of no data
        if not sizes:
            labels = ['No Data']
            sizes = [1]
            colors = ['lightgray']
        
        # Create the pie chart with the specified colors
        ax = fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors
        )
        
        # Make labels more visible
        plt_texts = texts + autotexts
        for text in plt_texts:
            text.set_fontsize(9)
        
        # Equal aspect ratio ensures the pie chart is circular
        ax.axis('equal')
        ax.set_title(title)
    
    def update_counts_table(self, filtered_statuses):
        """
        Update the counts table with filtered and total counts.
        
        Args:
            filtered_statuses: Dictionary of filtered statuses for each type
        """
        # Clear the table
        for item in self.

# RTVM_Tool_V5.0.py - Main entry point for the RTVM Tool application

import sys
import os
from rtvm.utils.dependency_manager import ensure_dependencies
from rtvm.gui.main_app import RTVMApp
from rtvm.utils.logger_setup import setup_logger
import tkinter as tk

def main():
    """
    Main entry point for the RTVM Tool application.
    Sets up logging, ensures dependencies are installed, and starts the application.
    """
    # Set up logging
    logger = setup_logger()
    logger.info("Starting RTVM Tool application")
    
    # Ensure all required dependencies are installed
    try:
        ensure_dependencies()
    except Exception as e:
        tk.messagebox.showerror("Dependency Error", 
                            f"Failed to install required dependencies: {str(e)}\n"
                            "Please ensure you have internet connectivity and permissions to install packages.")
        sys.exit(1)
    
    # Create the main Tkinter window
    root = tk.Tk()
    root.title("RTVM Tool V5.0")
    
    # Set initial window size (adjustable by the user)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = min(int(screen_width * 0.8), 1600)
    window_height = min(int(screen_height * 0.8), 800)
    root.geometry(f"{window_width}x{window_height}")
    
    # Create the main application instance
    try:
        app = RTVMApp(root)
        logger.info("RTVM Tool interface initialized")
        
        # Start the Tkinter main loop
        root.mainloop()
    except Exception as e:
        logger.error(f"Error in main application: {str(e)}", exc_info=True)
        tk.messagebox.showerror("Application Error", 
                             f"An unexpected error occurred: {str(e)}\n"
                             "Please check the log file for details.")
        sys.exit(1)
    
    logger.info("RTVM Tool application closed")

if __name__ == "__main__":
    main()
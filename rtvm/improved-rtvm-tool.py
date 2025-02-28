# main.py - Main entry point for the RTVM Tool application

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Import modules from the application structure
from rtvm.utils.dependency_manager import ensure_dependencies
from rtvm.gui.main_app import RTVMApp
from rtvm.utils.logger import setup_logger

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
        messagebox.showerror("Dependency Error", 
                            f"Failed to install required dependencies: {str(e)}\n"
                            "Please ensure you have internet connectivity and permissions to install packages.")
        sys.exit(1)
    
    # Create the main Tkinter window
    root = tk.Tk()
    root.title("RTVM Tool")
    
    # Set initial window size (adjustable by the user)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = min(int(screen_width * 0.8), 1600)
    window_height = min(int(screen_height * 0.8), 800)
    root.geometry(f"{window_width}x{window_height}")
    
    # Set the application icon if available
    icon_path = os.path.join(os.path.dirname(__file__), "rtvm", "resources", "icon.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except tk.TclError:
            logger.warning("Failed to set application icon")
    
    # Create the main application instance
    try:
        app = RTVMApp(root)
        logger.info("RTVM Tool interface initialized")
        
        # Start the Tkinter main loop
        root.mainloop()
    except Exception as e:
        logger.critical(f"Error in main application: {str(e)}", exc_info=True)
        messagebox.showerror("Application Error", 
                             f"An unexpected error occurred: {str(e)}\n"
                             "Please check the log file for details.")
        sys.exit(1)
    
    logger.info("RTVM Tool application closed")

if __name__ == "__main__":
    main()

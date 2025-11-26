"""
BMSgo - Smart Inventory System Launcher
This script serves as the entry point for the packaged application.
"""
import os
import sys
import webbrowser
import threading
import time
from inventory_system import create_app

def open_browser():
    """Open the browser after a short delay to ensure the server is running."""
    time.sleep(2)  # Wait for the server to start
    webbrowser.open('http://127.0.0.1:5000')

def main():
    """Main entry point for the application."""
    # Set up the environment
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app 
        # path into variable _MEIPASS.
        application_path = sys._MEIPASS
        os.chdir(application_path)
    
    # Create and configure the app
    app = create_app()
    
    # Open browser in a separate thread
    threading.Thread(target=open_browser).start()
    
    # Run the app
    app.run(debug=False, threaded=True)

if __name__ == '__main__':
    main()

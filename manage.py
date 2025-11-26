from inventory_system import create_app
import webbrowser
import threading
import time

app = create_app()

def open_browser():
    """Open the browser after a short delay to ensure the server is running."""
    time.sleep(2)  # Wait for the server to start
    webbrowser.open('http://127.0.0.1:5000')

def main():
    # Open browser in a separate thread
    threading.Thread(target=open_browser).start()

    # Run the app
    app.run(debug=True)

if __name__ == '__main__':
    main()

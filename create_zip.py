"""
Create a ZIP file of the BMSgo application for distribution.
"""
import os
import zipfile
import datetime

def create_zip():
    """Create a ZIP file of the BMSgo application."""
    # Get the current date for the filename
    today = datetime.datetime.now().strftime("%Y%m%d")
    
    # Create the ZIP filename
    zip_filename = f"BMSgo_v1.0_{today}.zip"
    
    # Create the ZIP file
    print(f"Creating {zip_filename}...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the dist/BMSgo directory and add all files
        for root, _, files in os.walk('dist/BMSgo'):
            for file in files:
                file_path = os.path.join(root, file)
                # Calculate the path inside the ZIP file
                arcname = os.path.relpath(file_path, 'dist')
                print(f"Adding {arcname}")
                zipf.write(file_path, arcname)
    
    print(f"\nZIP file created: {os.path.abspath(zip_filename)}")
    print(f"Size: {os.path.getsize(zip_filename) / (1024*1024):.2f} MB")

if __name__ == '__main__':
    create_zip()

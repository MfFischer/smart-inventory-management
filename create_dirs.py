# Save this as create_dirs.py in your project root
import os

# Create the includes directory if it doesn't exist
includes_dir = os.path.join('app', 'templates', 'includes')
if not os.path.exists(includes_dir):
    os.makedirs(includes_dir)
    print(f"Created directory: {includes_dir}")
else:
    print(f"Directory already exists: {includes_dir}")

# Check if the navbar.html file exists
navbar_path = os.path.join(includes_dir, 'navbar.html')
if not os.path.exists(navbar_path):
    print(f"Warning: {navbar_path} does not exist")
else:
    print(f"File exists: {navbar_path}")

# Check if the flash_messages.html file exists
flash_path = os.path.join(includes_dir, 'flash_messages.html')
if not os.path.exists(flash_path):
    print(f"Warning: {flash_path} does not exist")
else:
    print(f"File exists: {flash_path}")
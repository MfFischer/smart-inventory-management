# Save this as check_models.py in your project root
import os

# Print current directory
print(f"Current directory: {os.getcwd()}")

# Check if the models file exists
models_path = os.path.join('modules', 'users', 'models.py')
print(f"Checking for file: {models_path}")
print(f"File exists: {os.path.exists(models_path)}")

# Print the content of the models file
if os.path.exists(models_path):
    with open(models_path, 'r') as f:
        content = f.read()
        print("\nContent of models.py:")
        print(content)
        
        # Check if DataAccessRequest is defined in the file
        if "class DataAccessRequest" in content:
            print("\nDataAccessRequest class is defined in the file.")
        else:
            print("\nDataAccessRequest class is NOT defined in the file.")
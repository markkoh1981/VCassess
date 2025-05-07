import ctypes
import os

# Ensure the MSYS2 UCRT64 bin directory is temporarily at the start of the DLL search path for this script
# This is an alternative way to influence DLL loading for this specific process
msys_bin_path = r"C:\msys64\ucrt64\bin"
original_path = os.environ["PATH"]

if msys_bin_path not in original_path:
    os.environ["PATH"] = msys_bin_path + os.pathsep + original_path
    print(f"Temporarily prepended to PATH: {msys_bin_path}")
else:
    print(f"MSYS2 bin path already in PATH: {msys_bin_path}")

dll_path = r"C:\msys64\ucrt64\bin\libgobject-2.0-0.dll"

print(f"Attempting to load: {dll_path}")

try:
    # Try loading with just the name, relying on PATH
    # mydll = ctypes.CDLL("libgobject-2.0-0.dll") 
    # Or try loading with the full path
    mydll = ctypes.CDLL(dll_path)
    print(f"Successfully loaded {dll_path} using ctypes!")
except OSError as e:
    print(f"OSError when loading {dll_path} with ctypes: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    # Restore original PATH if it was changed
    if msys_bin_path not in original_path:
        os.environ["PATH"] = original_path
        print("Restored original PATH.")


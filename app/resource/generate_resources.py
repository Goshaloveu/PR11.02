"""
Script to generate PyQt6 resources from .qrc file
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Generate resource_rc.py from resource.qrc"""
    # Get the directory where this script is located
    current_dir = Path(__file__).resolve().parent
    
    # Resource file paths
    qrc_file = current_dir / "resource.qrc"
    output_file = current_dir / "resource_rc.py"
    
    # Verify resource.qrc exists
    if not qrc_file.exists():
        print(f"Error: {qrc_file} not found!")
        return 1
        
    success = False
        
    try:
        # Try using PyQt6's pyside6-rcc tool
        try:
            print("Attempting to generate resources with pyside6-rcc...")
            result = subprocess.run(["pyside6-rcc", str(qrc_file), "-o", str(output_file)], 
                                   check=True, capture_output=True, text=True)
            print("Successfully generated resource file with pyside6-rcc")
            success = True
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"pyside6-rcc attempt failed: {e}")
            
        # Try using PyQt6's direct tool
        if not success:
            try:
                print("Attempting to generate resources with pyrcc6...")
                result = subprocess.run(["pyrcc6", str(qrc_file), "-o", str(output_file)], 
                                       check=True, capture_output=True, text=True)
                print("Successfully generated resource file with pyrcc6")
                success = True
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                print(f"pyrcc6 attempt failed: {e}")
                
        # Try using PyQt6's pyrcc5
        if not success:
            try:
                print("Attempting to generate resources with pyrcc5...")
                result = subprocess.run(["pyrcc5", str(qrc_file), "-o", str(output_file)], 
                                       check=True, capture_output=True, text=True)
                print("Successfully generated resource file with pyrcc5")
                success = True
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                print(f"pyrcc5 attempt failed: {e}")
            
        # If all methods above failed, create a simple Python-only solution
        if not success:
            print("All resource compilation methods failed.")
            print("Using fallback resource_simple.py for image loading.")
            
            # Make sure resource_simple.py is up-to-date
            # (No need to regenerate it since we already have it in the project)
            
    except Exception as e:
        print(f"Error during resource generation: {e}")
        return 1
        
    return 0 if success else 0  # Return 0 even if we fall back to resource_simple.py

if __name__ == "__main__":
    sys.exit(main()) 
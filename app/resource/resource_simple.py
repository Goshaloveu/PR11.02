"""
Simple alternative to resource_rc.py for PyQt6 compatibility
"""
import os

# Get the resource directory
RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(RESOURCE_DIR, 'images')

# Create paths to common images
BACKGROUND_IMG = os.path.join(IMAGES_DIR, 'background.jpg')
LOGO_IMG = os.path.join(IMAGES_DIR, 'logo.png')

def get_image_path(image_name):
    """Get full path to an image in the resources folder"""
    return os.path.join(IMAGES_DIR, image_name) 
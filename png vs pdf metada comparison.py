# -*- coding: utf-8 -*-
"""Untitled1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1IEr1mKzZXBZOII9ODn7KkKFVmtEiI8z7
"""

#!/usr/bin/env python3
"""
Image Metadata Comparison Tool (PNG vs JPG)

This script compares the metadata of PNG and JPG image files and displays the differences.
Optimized for Google Colab environments with appropriate installation handling.
"""

!apt-get install -y libimage-exiftool-perl

### installs and imports
import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Dict, List, Any, Tuple, Optional
import warnings
from PIL import Image # Import Image here

# Suppress Pillow DecompressionBombWarning for large images
warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)

# Check and install dependencies for Colab
try:
    #from PIL import Image # No need to import again
    from PIL.ExifTags import TAGS
except ImportError:
    print("Installing Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image
    from PIL.ExifTags import TAGS

def setup_exiftool():
    """Check if exiftool is installed and attempt installation if not."""
    try:
        # Check if exiftool is in the system path
        subprocess.run(["exiftool", "-ver"], capture_output=True, check=True)
        return True  # Exiftool is installed
    except subprocess.CalledProcessError:
        print("exiftool not found. Attempting installation...")
        try:
            # Try to install exiftool using apt (common on Colab)
            subprocess.check_call(["apt-get", "install", "-y", "exiftool"])
            return True  # Installation successful
        except subprocess.CalledProcessError:
            print("exiftool installation failed. Using Pillow for basic metadata extraction.")
            return False  # Installation failed

def setup_exiftool():
    """Check if exiftool is installed and attempt installation if not."""
    try:
        # Check if exiftool is in the system path
        subprocess.run(["exiftool", "-ver"], capture_output=True, check=True)
        return True  # Exiftool is installed
    except subprocess.CalledProcessError:
        print("exiftool not found. Attempting installation...")
        try:
            # Try to install exiftool using apt (common on Colab)
            !apt-get install -y libimage-exiftool-perl  # Install the necessary package for exiftool
            # subprocess.check_call(["apt-get", "install", "-y", "exiftool"]) # This line might be causing issues, replace with above
            return True  # Installation successful
        except subprocess.CalledProcessError:
            print("exiftool installation failed. Using Pillow for basic metadata extraction.")
            return False  # Installation failed

# Extract metadata using Pillow (limited but no external dependencies)
def extract_metadata_pillow(image_path: str) -> Dict[str, Any]:
    try:
        with Image.open(image_path) as img:
            # Get file extension from path
            file_ext = os.path.splitext(image_path)[1].lower()

            metadata = {
                "basic": {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "filename": os.path.basename(image_path),
                    "file_size": os.path.getsize(image_path),
                    "file_extension": file_ext
                }
            }

            # Extract EXIF data if available (typically in JPG files)
            exif_data = {}
            if hasattr(img, '_getexif') and img._getexif():
                for tag_id, value in img._getexif().items():
                    tag = TAGS.get(tag_id, tag_id)
                    # Handle bytes data and complex structures
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8')
                        except UnicodeDecodeError:
                            value = str(value)
                    exif_data[tag] = str(value)

                metadata["exif"] = exif_data

            # Extract PNG-specific data if it's a PNG
            if img.format == 'PNG':
                png_data = {}
                # Extract PNG chunks
                if hasattr(img, 'info'):
                    for key, value in img.info.items():
                        # Convert bytes to string or representation
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8')
                            except UnicodeDecodeError:
                                # For binary data, just show its length
                                value = f"<binary data, {len(value)} bytes>"
                        png_data[key] = str(value)

                    if png_data:
                        metadata["png_info"] = png_data

            return metadata
    except Exception as e:
        print(f"Error extracting metadata from {image_path}: {str(e)}")
        return {"error": str(e)}

# Extract metadata using ExifTool (comprehensive)
def extract_metadata_exiftool(image_path: str) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            ["exiftool", "-json", "-a", "-u", "-g1", image_path],
            capture_output=True,
            check=True,
            text=True
        )
        # ExifTool returns a JSON array with one object
        metadata = json.loads(result.stdout)[0]

        # Add file extension explicitly
        file_ext = os.path.splitext(image_path)[1].lower()
        if 'File' not in metadata:
            metadata['File'] = {}
        metadata['File']['Extension'] = file_ext

        return metadata
    except subprocess.SubprocessError as e:
        print(f"Error running exiftool on {image_path}: {str(e)}")
        return {"error": str(e)}
    except json.JSONDecodeError as e:
        print(f"Error parsing exiftool output: {str(e)}")
        return {"error": str(e)}

image1_path = '/content/ChatGPT Image Apr 1, 2025, 04_53_46 PM.png'
image2_path = '/content/IMG_3332.jpg'

# Commented out IPython magic to ensure Python compatibility.

# Compare two metadata dictionaries and identify differences
def compare_metadata(metadata1: Dict[str, Any], metadata2: Dict[str, Any]) -> Dict[str, Any]:
    differences = {}

    # Combine all keys from both dictionaries
    all_keys = set(metadata1.keys()) | set(metadata2.keys())

    for key in all_keys:
        # If key exists in both dictionaries
        if key in metadata1 and key in metadata2:
            # If both values are dictionaries, recursively compare them
            if isinstance(metadata1[key], dict) and isinstance(metadata2[key], dict):
                nested_diff = compare_metadata(metadata1[key], metadata2[key])
                if nested_diff:
                    differences[key] = nested_diff
            # Otherwise compare the values directly
            elif metadata1[key] != metadata2[key]:
                differences[key] = (metadata1[key], metadata2[key])
        # If key exists only in metadata1
        elif key in metadata1:
            differences[key] = (metadata1[key], "Not present")
        # If key exists only in metadata2
        else:
            differences[key] = ("Not present", metadata2[key])

    return differences

# Format the differences for display
def format_differences(differences: Dict[str, Any], indent: int = 0, image1_name: str = "Image 1",
                      image2_name: str = "Image 2") -> str:
    result = []
    indent_str = " " * indent

    for key, value in differences.items():
        if isinstance(value, dict):
            result.append(f"{indent_str}{key}:")
            result.append(format_differences(value, indent + 2, image1_name, image2_name))
        else:
            val1, val2 = value
            result.append(f"{indent_str}{key}: {image1_name}={val1} | {image2_name}={val2}")

    return "\n".join(result)

# Save comparison to file
def save_comparison(differences: Dict[str, Any], output_file: str):
    with open(output_file, 'w') as f:
        if isinstance(differences, dict):
            json.dump(differences, f, indent=2)
        else:
            f.write(differences)
    print(f"Comparison saved to {output_file}")

# Function specifically for Google Colab usage
def compare_images_colab(image1_path, image2_path, format='text'):
    """
    Compare two images directly in Google Colab without CLI arguments.

    Args:
        image1_path: Path to first image (JPG or PNG)
        image2_path: Path to second image (PNG or JPG)
        format: Output format ('text' or 'json')

    Returns:
        Comparison results
    """
    # Ensure ExifTool is installed
    has_exiftool = setup_exiftool()

    print(f"Comparing metadata of:\n1: {image1_path}\n2: {image2_path}\n")

    # Extract metadata
    if has_exiftool:
        print("Using ExifTool for comprehensive metadata extraction")
        metadata1 = extract_metadata_exiftool(image1_path)
        metadata2 = extract_metadata_exiftool(image2_path)
    else:
        print("Using Pillow for basic metadata extraction")
        metadata1 = extract_metadata_pillow(image1_path)
        metadata2 = extract_metadata_pillow(image2_path)

    # Get file names for display
    image1_name = os.path.basename(image1_path)
    image2_name = os.path.basename(image2_path)

    # Compare metadata
    differences = compare_metadata(metadata1, metadata2)

    # Format and return results
    if not differences:
        return "No differences found in the metadata"

    if format == 'text':
        return "METADATA DIFFERENCES:\n" + format_differences(differences, 0, image1_name, image2_name)
    else:  # json format
        return json.dumps(differences, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Compare metadata of PNG and JPG images')
    parser.add_argument('image1', help='Path to first image (JPG or PNG)')
    parser.add_argument('image2', help='Path to second image (PNG or JPG)')
    parser.add_argument('--output', '-o', help='Save comparison to file')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                      help='Output format (default: text)')
    args = parser.parse_args()

    # Check if files exist
    if not os.path.isfile(args.image1):
        print(f"Error: File not found: {args.image1}")
        return 1
    if not os.path.isfile(args.image2):
        print(f"Error: File not found: {args.image2}")
        return 1

    # Check if files are images
    try:
        Image.open(args.image1).verify()
        Image.open(args.image2).verify()
    except:
        print("Error: One or both files are not valid images")
        return 1

    # Get file extensions
    ext1 = os.path.splitext(args.image1)[1].lower()
    ext2 = os.path.splitext(args.image2)[1].lower()

    # Check if one is PNG and one is JPG
    valid_exts = ['.jpg', '.jpeg', '.png']
    if ext1 not in valid_exts or ext2 not in valid_exts:
        print(f"Error: Both files must be either JPG or PNG. Found: {ext1} and {ext2}")
        return 1

    # Get image names for display
    image1_name = os.path.basename(args.image1)
    image2_name = os.path.basename(args.image2)

    print(f"Comparing metadata of:\n1: {args.image1}\n2: {args.image2}\n")

    # Choose metadata extraction method
    has_exiftool = setup_exiftool()
    if has_exiftool:
        print("Using ExifTool for comprehensive metadata extraction")
        metadata1 = extract_metadata_exiftool(args.image1)
        metadata2 = extract_metadata_exiftool(args.image2)
    else:
        print("Using Pillow for basic metadata extraction")
        metadata1 = extract_metadata_pillow(args.image1)
        metadata2 = extract_metadata_pillow(args.image2)

    # Compare metadata
    differences = compare_metadata(metadata1, metadata2)

    # Format and display results
    if not differences:
        print("No differences found in the metadata")
        return 0

    if args.format == 'text':
        output = "METADATA DIFFERENCES:\n" + format_differences(differences, 0, image1_name, image2_name)
        print(output)
    else:  # json format
        output = differences
        print(json.dumps(differences, indent=2))

    # Save to file if requested
    if args.output:
        save_comparison(output, args.output)

    return 0

# Example usage in Google Colab:
"""
# Import the script (assuming it's saved as image_metadata_compare.py)
# %run -i image_metadata_compare.py

# Use the Colab-specific function
result = compare_images_colab('/path/to/image.jpg', '/path/to/image.png')
print(result)

# Or upload files and compare
from google.colab import files
uploaded = files.upload()  # Upload multiple files

# Get the uploaded filenames
filenames = list(uploaded.keys())
if len(filenames) >= 2:
    result = compare_images_colab(filenames[0], filenames[1])
    print(result)
"""

if __name__ == "__main__":
    # If it seems we're in a notebook environment, don't run main()
    try:
        import google.colab
        # We're in Colab, don't run the CLI version
        print("Running in Google Colab environment")
        print("Use the compare_images_colab() function instead of command line arguments")
    except ImportError:
        # Not in Colab, run the normal CLI version
        sys.exit(main())

result = compare_images_colab(image1_path, image2_path)

print(result)


# Required Libraries
import os
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import fitz  # PyMuPDF
from tkinter import Tk
from tkinter.filedialog import askopenfilenames
import io

# Define directories for uploaded files and converted images
UPLOAD_DIR = Path("uploaded_files")
CONVERTED_DIR = Path("converted_images")

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
CONVERTED_DIR.mkdir(exist_ok=True)

# === Utility Functions for Upload and Conversion ===

def upload_files():
    """
    Allows the user to select and upload multiple image and PDF files.
    Saves them to the UPLOAD_DIR.
    """
    print("Please select your image and PDF files (PNG, JPG, JPEG, PDF).")
    
    # Hide the main Tkinter window
    Tk().withdraw()
    
    # Open file dialog to select multiple files
    filenames = askopenfilenames(
        title="Select Image and PDF Files",
        filetypes=[("Image and PDF Files", "*.png;*.jpg;*.jpeg;*.pdf")]
    )
    
    for filepath in filenames:
        file_path = UPLOAD_DIR / Path(filepath).name
        with open(filepath, 'rb') as f_src, open(file_path, 'wb') as f_dest:
            f_dest.write(f_src.read())
        print(f"Uploaded: {file_path.name}")

def convert_files_to_png():
    """
    Converts uploaded image and PDF files to PNG format.
    Saves all PNG images to the CONVERTED_DIR.
    Extracts every image from each page of the PDF separately.
    """
    print("Converting files to PNG format...")
    for file in tqdm(UPLOAD_DIR.iterdir(), desc="Converting files"):
        if file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            # Convert image to PNG
            try:
                img = Image.open(file).convert('RGB')
                png_path = CONVERTED_DIR / f"{file.stem}.png"
                img.save(png_path, 'PNG')
                print(f"Converted {file.name} to {png_path.name}")
            except Exception as e:
                print(f"Error converting {file.name}: {e}")
        elif file.suffix.lower() == '.pdf':
            # Extract and convert each image from a PDF page
            try:
                pdf_document = fitz.open(file)
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    images = page.get_images(full=True)

                    if images:
                        for img_index, img in enumerate(images):
                            xref = img[0]
                            base_image = pdf_document.extract_image(xref)
                            image_bytes = base_image["image"]
                            image = Image.open(io.BytesIO(image_bytes))
                            png_path = CONVERTED_DIR / f"{file.stem}_page_{page_num + 1}_image_{img_index + 1}.png"
                            image.save(png_path, 'PNG')
                            print(f"Extracted and saved {file.name} page {page_num + 1}, image {img_index + 1} to {png_path.name}")
                    else:
                        print(f"No images found on page {page_num + 1} of {file.name}")

                pdf_document.close()

            except Exception as e:
                print(f"Error extracting images from {file.name}: {e}")
        else:
            print(f"Unsupported file format for {file.name}. Skipping.")

# Optional: Organize Converted Files
def organize_converted_files():
    """
    (Optional) Organizes converted PNG files into subdirectories based on original file names.
    """
    # Example implementation if needed
    pass  # Implement as per your needs

# === Main Function for Upload and Conversion ===

def upload_and_convert():
    """
    Main function to handle file upload and conversion.
    """
    upload_files()
    convert_files_to_png()
    # organize_converted_files()  # Uncomment if organization is implemented

# === Execute the Upload and Conversion Process ===

if __name__ == "__main__":
    upload_and_convert()
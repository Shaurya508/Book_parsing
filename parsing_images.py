import cv2
import os
from pdf2image import convert_from_path
import pytesseract

# Define the path where the pages and extracted images will be saved
output_folder = 'extracted_pages'
image_output_folder = 'extracted_images'

# Create the folders if they don't exist
os.makedirs(output_folder, exist_ok=True)
os.makedirs(image_output_folder, exist_ok=True)

# Convert PDF to images
images = convert_from_path('The Smart Branding Book.pdf')

# Save each page as an image in the specified folder
for i, img in enumerate(images):
    page_path = os.path.join(output_folder, f'page_{i}.png')
    img.save(page_path)
    print(f'Saved {page_path}')

    # Read the saved page image using OpenCV
    image = cv2.imread(page_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply edge detection
    edges = cv2.Canny(gray, 100, 200)

    # Find contours based on the edges detected
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Iterate over contours to extract regions containing images
    for j, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)

        # Set size threshold to filter out non-image contours (like text regions)
        if w > 100 and h > 100:  # Adjust this threshold as needed
            # Extract the image region
            roi = image[y:y+h, x:x+w]
            
            # Save the extracted image
            image_save_path = os.path.join(image_output_folder, f'page_{i}_extracted_image_{j}.png')
            cv2.imwrite(image_save_path, roi)
            print(f'Saved {image_save_path}')

def extract_text_from_pdf(pdf_path):
    # Convert PDF to images
    pages = convert_from_path(pdf_path, 300)

    # Iterate through all the pages and extract text
    extracted_text = ''
    for page_number, page_data in enumerate(pages):
        # Perform OCR on the image
        text = pytesseract.image_to_string(page_data)
        extracted_text += f"Page {page_number + 1}:\n{text}\n"
        if(page_number == 28):
            break
    return extracted_text
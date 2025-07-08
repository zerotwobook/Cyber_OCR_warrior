import cv2
import pytesseract
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

# Set Tesseract OCR path (replace with your actual path)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def select_image():
    """Opens a file dialog to select an image and performs OCR."""
    filepath = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif")]
    )

    if filepath:
        try:
            # Perform OCR
            text = perform_ocr(filepath)

            # Update GUI with OCR results
            update_gui(filepath, text)

        except Exception as e:
            result_text.delete("1.0", tk.END)
            result_text.insert(tk.END, f"Error: {e}")

def perform_ocr(image_path):
    """Performs OCR on the given image and returns the extracted text."""
    try:
        # Load the image using OpenCV
        img = cv2.imread(image_path)

        # Convert to grayscale (optional, but often improves accuracy)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Use Tesseract to perform OCR with Thai and English language support
        custom_config = r'--oem 3 --psm 6 -l tha+eng'  # OEM 3 for LSTM engine, PSM 6 for single block of text
        text = pytesseract.image_to_string(gray, config=custom_config, lang='tha+eng')

        return text

    except Exception as e:
        raise Exception(f"OCR failed: {e}")

def update_gui(image_path, text):
    """Updates the GUI with the selected image and OCR results."""
    try:
        # Display the image
        img = Image.open(image_path)
        img.thumbnail((300, 300))  # Resize for display
        img_tk = ImageTk.PhotoImage(img)
        image_label.config(image=img_tk)
        image_label.image = img_tk  # Keep a reference!

        # Display the OCR text
        result_text.delete("1.0", tk.END)  # Clear previous text
        result_text.insert(tk.END, text)  # Insert new text

    except Exception as e:
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, f"Error displaying results: {e}")


# --- GUI Setup ---
root = tk.Tk()
root.title("Thai/English OCR Reader")

# Image display
image_label = tk.Label(root)
image_label.pack(pady=10)

# Button to select image
select_button = tk.Button(root, text="Select Image", command=select_image)
select_button.pack(pady=10)

# Text area to display OCR results
result_text = tk.Text(root, height=15, width=50)
result_text.pack(pady=10)

root.mainloop()
import cv2
import pytesseract
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import re
import os

# 🔧 Path ไปยัง Tesseract OCR (เปลี่ยนตามเครื่องคุณ)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 🔍 ดึงข้อมูลจากข้อความ OCR
def extract_info(text):
    # Match dates like 12/06/2024, 12-06-2024, 12.06.2024, 12 06 2024, etc.
    date = re.search(r'\d{2}[/\-\. ]\d{2}[/\-\. ]\d{4}', text)
    time = re.search(r'\d{2}:\d{2}', text)
    amount = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})', text)
    bank = re.search(r'(กสิกร|ไทยพาณิชย์|กรุงไทย|กรุงศรี|ออมสิน|ทหารไทย)', text)
    name = re.search(r'ชื่อ\s*:\s*([^\n]+)', text)
    if not name:
        name = re.search(r'ชื่อ\s*([^\n]+)', text)
    if not name:
        name = re.search(r'ผู้รับเงิน\s*:\s*([^\n]+)', text)
    if not name:
        name = re.search(r'ผู้โอน\s*:\s*([^\n]+)', text)
    if not name:
        name = re.search(r'ผู้รับ\s*:\s*([^\n]+)', text)


    return {
        'Date': date.group() if date else '',
        'Time': time.group() if time else '',
        'Amount': amount.group() if amount else '',
        'Bank': bank.group() if bank else '',
        'Name': name.group() if name else ''
    }

# 📤 บันทึกเป็น Excel
def export_to_excel(data_list):
    df = pd.DataFrame(data_list)
    df.to_excel("slip_results.xlsx", index=False)
    messagebox.showinfo("Success", "Data saved to slip_results.xlsx")

# 📤 บันทึกเป็น CSV
def export_to_csv(data_list):
    df = pd.DataFrame(data_list)
    df.to_csv("slip_results.csv", index=False, encoding="utf-8-sig")
    messagebox.showinfo("Success", "Data saved to slip_results.csv")

# 🖼 OCR และแสดงผล
def process_image(path):
    image = cv2.imread(path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, lang='tha+eng')
    result = extract_info(text)
    return result, text

# 📂 ฟังก์ชันเลือกไฟล์
def select_image():
    filepath = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.jpg *.png *.jpeg")]
    )
    if filepath:
        result, raw_text = process_image(filepath)
        results_list.append(result)

        # แสดงภาพ
        img = Image.open(filepath).resize((300, 400))
        img_tk = ImageTk.PhotoImage(img)
        panel.config(image=img_tk)
        panel.image = img_tk

        # แสดงข้อความ
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, raw_text)

        # แสดงผลลัพธ์ที่แยกได้
        extracted_text.set(f"""
📅 Date: {result['Date']}
⏰ Time: {result['Time']}
💸 Amount: {result['Amount']}
🏦 Bank: {result['Bank']}
👤 Name: {result['Name']}
        """)

# 🧠 ตัวแปรเก็บผล
results_list = []

# 🎨 สร้าง GUI
root = tk.Tk()
root.title("OCR สลิปเงิน → CSV")
root.state('zoomed')  # Maximize window to fit the screen
root.configure(bg="#f5f6fa")

def center_window(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

# --- Scrollable Frame Setup ---
container = tk.Frame(root, bg="#f5f6fa")
container.pack(fill="both", expand=True)

canvas = tk.Canvas(container, bg="#f5f6fa", highlightthickness=0)
scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

scrollable_frame = tk.Frame(canvas, bg="#f5f6fa")

# Update the width of the scrollable_frame when the canvas size changes
def on_canvas_configure(event):
    canvas.itemconfig('frame', width=event.width)

canvas.bind('<Configure>', on_canvas_configure)

window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags='frame')

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.configure(yscrollcommand=scrollbar.set)

# --- Place your main content in scrollable_frame instead of root/main_frame ---
tk.Label(scrollable_frame, text="OCR สลิปเงิน → CSV", font=("Arial Rounded MT Bold", 24), bg="#f5f6fa", fg="#273c75").pack(pady=(10, 20))

btn_frame = tk.Frame(scrollable_frame, bg="#f5f6fa")
btn_frame.pack(pady=5, fill="x", expand=True)  # Make the frame expand horizontally

# Center the buttons inside the frame
btn_inner = tk.Frame(btn_frame, bg="#f5f6fa")
btn_inner.pack(anchor="center")

tk.Button(btn_inner, text="📁 เลือกรูปภาพสลิป", command=select_image, font=("Arial", 14), bg="#00b894", fg="white", width=22).pack(side="left", padx=8)
tk.Button(btn_inner, text="💾 บันทึกเป็น CSV", command=lambda: export_to_csv(results_list), font=("Arial", 14), bg="#0984e3", fg="white", width=22).pack(side="left", padx=8)

panel = tk.Label(scrollable_frame, bg="#dfe6e9", width=400, height=500)
panel.pack(pady=20)

extracted_text = tk.StringVar()
tk.Label(scrollable_frame, text="📋 ข้อมูลที่แยกได้:", font=("Arial", 14, "bold"), bg="#f5f6fa", fg="#636e72").pack(anchor="w", padx=10)
tk.Label(scrollable_frame, textvariable=extracted_text, justify="left", font=("Arial", 13), fg="#00b894", bg="#f5f6fa").pack(pady=8, anchor="w", padx=10)

tk.Label(scrollable_frame, text="🔍 ข้อความที่อ่านได้ (OCR):", font=("Arial", 14, "bold"), bg="#f5f6fa", fg="#636e72").pack(anchor="w", padx=10)
text_frame = tk.Frame(scrollable_frame, bg="#f5f6fa")
text_frame.pack(fill="x", pady=8, padx=10)
result_text = tk.Text(text_frame, height=12, width=90, font=("Consolas", 12))
result_text.pack(side="left", fill="x", expand=True)
scrollbar_text = tk.Scrollbar(text_frame, command=result_text.yview)
scrollbar_text.pack(side="right", fill="y")
result_text.config(yscrollcommand=scrollbar_text.set)

# Optional: Allow mouse wheel scrolling on the canvas
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
canvas.bind_all("<MouseWheel>", _on_mousewheel)

center_window(root)

if __name__ == "__main__":
    root.mainloop()

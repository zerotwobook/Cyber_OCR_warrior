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
    date = re.search(r'\d{2}/\d{2}/\d{4}', text)
    time = re.search(r'\d{2}:\d{2}', text)
    amount = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})', text)
    bank = re.search(r'(กสิกร|ไทยพาณิชย์|กรุงไทย|กรุงศรี|ออมสิน|ทหารไทย)', text)
    name = re.search(r'นาย\s*\S+|\S+\s*ยาทิพย์|\S+\s*\S+', text)

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
root.title("OCR สลิปเงิน → Excel")
root.geometry("650x600")

tk.Button(root, text="📁 เลือกรูปภาพสลิป", command=select_image).pack(pady=10)

panel = tk.Label(root)
panel.pack()

extracted_text = tk.StringVar()
tk.Label(root, textvariable=extracted_text, justify="left", font=("Arial", 11), fg="green").pack(pady=5)

tk.Label(root, text="🔍 ข้อความที่อ่านได้ (OCR):").pack()
result_text = tk.Text(root, height=10, width=70)
result_text.pack(pady=5)

tk.Button(root, text="💾 บันทึกเป็น Excel", command=lambda: export_to_excel(results_list)).pack(pady=10)

root.mainloop()

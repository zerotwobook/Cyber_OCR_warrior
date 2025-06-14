import cv2
import pytesseract
import re
from PIL import Image

# โหลดภาพ
image = cv2.imread('/mnt/data/8115467a-63c5-4407-acb7-654e420b02dc.png')

# แปลงภาพเป็น grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# เพิ่มความคมชัดให้ภาพ
gray = cv2.bilateralFilter(gray, 11, 17, 17)

# แปลงภาพให้เป็นข้อความด้วย pytesseract
custom_config = r'--oem 3 --psm 6'
text = pytesseract.image_to_string(gray, lang='tha+eng', config=custom_config)

# พิมพ์ข้อความที่ OCR อ่านได้
print("ข้อความทั้งหมดจากภาพ:")
print(text)

# ใช้ regex แยกข้อมูล
date_time = re.search(r'(\d{2} \w+\. \d{4} - \d{2}:\d{2})', text)
ref_code = re.search(r'รหัสอ้างอิง[:\s]+([A-Z0-9]+)', text)
sender = re.search(r'จาก\s+(.*?)(\n|$)', text)
receiver = re.search(r'ไปยัง\s+(.*?)(\n|$)', text)
amount = re.search(r'จำนวนเงิน\s+([\d,]+\.\d{2})', text)

# แสดงผลลัพธ์ที่ได้
print("\nข้อมูลที่ดึงได้:")
if date_time: print(f"📅 วันที่และเวลา: {date_time.group(1)}")
if ref_code: print(f"🔢 รหัสอ้างอิง: {ref_code.group(1)}")
if sender: print(f"👤 จาก: {sender.group(1)}")
if receiver: print(f"👤 ไปยัง: {receiver.group(1)}")
if amount: print(f"💵 จำนวนเงิน: {amount.group(1)} บาท")

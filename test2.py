import cv2
import pytesseract
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import re
import os
import threading
from datetime import datetime
import numpy as np
from pathlib import Path
import logging
from openpyxl.styles import NamedStyle, PatternFill, Border, Side, Alignment, Font

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThaiOCRSlipProcessor:
    def __init__(self):
        self.tesseract_path = self._find_tesseract()
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        self.results_list = []
        self.current_image_path = None
        
        # Thai number mapping
        self.thai_numbers = {
            '๐': '0', '๑': '1', '๒': '2', '๓': '3', '๔': '4',
            '๕': '5', '๖': '6', '๗': '7', '๘': '8', '๙': '9'
        }
        
        # Thai month names
        self.thai_months = {
            'มกราคม': '01', 'กุมภาพันธ์': '02', 'มีนาคม': '03', 'เมษายน': '04',
            'พฤษภาคม': '05', 'มิถุนายน': '06', 'กรกฎาคม': '07', 'สิงหาคม': '08',
            'กันยายน': '09', 'ตุลาคม': '10', 'พฤศจิกายน': '11', 'ธันวาคม': '12',
            'ม.ค.': '01', 'ก.พ.': '02', 'มี.ค.': '03', 'เม.ย.': '04',
            'พ.ค.': '05', 'มิ.ย.': '06', 'ก.ค.': '07', 'ส.ค.': '08',
            'ก.ย.': '09', 'ต.ค.': '10', 'พ.ย.': '11', 'ธ.ค.': '12'
        }
        
        # Enhanced patterns for Thai banking
        self.patterns = {
            'date': [
                # Thai date formats
                r'(\d{1,2})\s*([ก-ฮ\.]+)\s*(\d{4})',  # 15 ม.ค. 2567
                r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})',  # 15/01/2567
                r'(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{4})',  # 15-01-2567
                r'(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{4})',  # 15.01.2567
                # Buddhist era years
                r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})',
                # Thai numbers
                r'([๐-๙]{1,2})[/\-\.]([๐-๙]{1,2})[/\-\.]([๐-๙]{4})',
            ],
            'time': [
                r'(\d{1,2}):(\d{2}):(\d{2})',  # 14:30:25
                r'(\d{1,2}):(\d{2})\s*น\.',  # 14:30 น.
                r'(\d{1,2}):(\d{2})',  # 14:30
                r'([๐-๙]{1,2}):([๐-๙]{2})',  # Thai numbers
                r'เวลา\s*(\d{1,2}):(\d{2})',  # เวลา 14:30
                r'TIME\s*(\d{1,2}):(\d{2})',
            ],
            'amount': [
                # Thai baht amounts
                r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*บาท',
                r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*THB',
                r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*฿',
                r'จำนวนเงิน\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)',
                r'ยอดเงิน\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)',
                r'Amount\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)',
                # Regular amount patterns
                r'(\d{1,3}(?:,\d{3})*\.\d{2})',
                r'(\d+\.\d{2})',
                # Thai number amounts
                r'([๐-๙,]+(?:\.[๐-๙]{2})?)\s*บาท',
            ],
            'bank': [
                # Thai bank names (full and abbreviated)
                r'(ธนาคารกสิกรไทย|กสิกร|KBANK|K-BANK)',
                r'(ธนาคารไทยพาณิชย์|ไทยพาณิชย์|SCB)',
                r'(ธนาคารกรุงไทย|กรุงไทย|KTB)',
                r'(ธนาคารกรุงศรีอยุธยา|กรุงศรี|BAY)',
                r'(ธนาคารออมสิน|ออมสิน|GSB)',
                r'(ธนาคารทหารไทย|ทหารไทย|TTB)',
                r'(ธนาคารกรุงเทพ|กรุงเทพ|BBL)',
                r'(ธนาคารยูโอบี|UOB)',
                r'(ธนาคารทิสโก้|TISCO)',
                r'(ธนาคารซีไอเอ็มบี|CIMB)',
                r'(ธนาคารแลนด์ แอนด์ เฮ้าส์|LH BANK)',
                r'(TMB|THANACHART)',
            ],
            'name': [
                # Thai name patterns
                r'ชื่อบัญชี\s*:?\s*([ก-ฮ\s]+)',
                r'ชื่อผู้รับ\s*:?\s*([ก-ฮ\s]+)',
                r'ชื่อผู้โอน\s*:?\s*([ก-ฮ\s]+)',
                r'ชื่อ\s*:?\s*([ก-ฮ\s]+)',
                r'ผู้รับเงิน\s*:?\s*([ก-ฮ\s]+)',
                r'ผู้โอน\s*:?\s*([ก-ฮ\s]+)',
                r'ผู้รับ\s*:?\s*([ก-ฮ\s]+)',
                r'TO\s*:?\s*([A-Za-z\s]+)',
                r'FROM\s*:?\s*([A-Za-z\s]+)',
                # Account holder patterns
                r'Account\s*Name\s*:?\s*([A-Za-z\s]+)',
                r'Receiver\s*:?\s*([A-Za-z\s]+)',
            ],
            'account_number': [
                r'เลขบัญชี\s*:?\s*([0-9\-]+)',
                r'บัญชีปลายทาง\s*:?\s*([0-9\-]+)',
                r'Account\s*No\s*:?\s*([0-9\-]+)',
                r'A/C\s*:?\s*([0-9\-]+)',
                r'(\d{3}-\d{1}-\d{5}-\d{1})',  # Thai account format
                r'(\d{10,15})',  # General account numbers
            ],
            'reference': [
                r'รหัสอ้างอิง\s*:?\s*([A-Za-z0-9]+)',
                r'Reference\s*:?\s*([A-Za-z0-9]+)',
                r'Ref\s*:?\s*([A-Za-z0-9]+)',
                r'Transaction\s*ID\s*:?\s*([A-Za-z0-9]+)',
                r'หมายเลขรายการ\s*:?\s*([A-Za-z0-9]+)',
            ],
            'transaction_type': [
                r'(โอนเงิน|Transfer)',
                r'(ถอนเงิน|Withdrawal)',
                r'(ฝากเงิน|Deposit)',
                r'(จ่ายบิล|Bill Payment)',
                r'(เติมเงิน|Top Up)',
                r'(ชำระเงิน|Payment)',
            ]
        }
        
        self.setup_gui()
    
    def _find_tesseract(self):
        """Automatically find Tesseract installation"""
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',  # macOS with Homebrew
            'tesseract'  # If in PATH
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or path == 'tesseract':
                try:
                    pytesseract.pytesseract.tesseract_cmd = path
                    pytesseract.get_tesseract_version()
                    logger.info(f"Found Tesseract at: {path}")
                    return path
                except:
                    continue
        
        logger.warning("Tesseract not found automatically. Please install Tesseract OCR.")
        return None
    
    def convert_thai_numbers(self, text):
        """Convert Thai numbers to Arabic numbers"""
        for thai, arabic in self.thai_numbers.items():
            text = text.replace(thai, arabic)
        return text
    
    def convert_buddhist_year(self, year_str):
        """Convert Buddhist Era year to Christian Era"""
        try:
            year = int(year_str)
            if year > 2400:  # Likely Buddhist Era
                return str(year - 543)
            return year_str
        except:
            return year_str
    
    def normalize_thai_date(self, date_str):
        """Normalize Thai date format"""
        # Convert Thai numbers
        date_str = self.convert_thai_numbers(date_str)
        
        # Handle Thai month names
        for thai_month, month_num in self.thai_months.items():
            if thai_month in date_str:
                date_str = date_str.replace(thai_month, month_num)
                break
        
        return date_str
    
    def extract_info(self, text):
        """Enhanced information extraction with Thai language support"""
        # Preprocess text
        text = self.convert_thai_numbers(text)
        
        result = {
            'Date': '',
            'Time': '',
            'Amount': '',
            'Bank': '',
            'Name': '',
            'Account_Number': '',
            'Reference': '',
            'Transaction_Type': '',
            'Confidence': 0
        }
        
        confidence_score = 0
        
        # Extract date with Thai support
        for pattern in self.patterns['date']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 3:
                    day, month, year = match.groups()[:3]
                    # Handle Thai month names
                    if month in self.thai_months:
                        month = self.thai_months[month]
                    elif not month.isdigit():
                        continue
                    
                    year = self.convert_buddhist_year(year)
                    result['Date'] = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                    confidence_score += 20
                    break
                else:
                    result['Date'] = match.group()
                    confidence_score += 15
                    break
            if result['Date']:
                break
        
        # Extract time
        for pattern in self.patterns['time']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:
                    hour, minute = match.groups()[:2]
                    result['Time'] = f"{hour.zfill(2)}:{minute.zfill(2)}"
                else:
                    result['Time'] = match.group()
                confidence_score += 15
                break
        
        # Extract amount with Thai baht support
        for pattern in self.patterns['amount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1) if match.groups() else match.group()
                # Clean amount
                amount = amount.replace(',', '').replace('฿', '').replace('บาท', '').strip()
                if amount and amount.replace('.', '').replace(',', '').isdigit():
                    result['Amount'] = amount
                    confidence_score += 25
                    break
        
        # Extract bank
        for pattern in self.patterns['bank']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['Bank'] = match.group(1)
                confidence_score += 20
                break
        
        # Extract name
        for pattern in self.patterns['name']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and not name.isdigit():
                    result['Name'] = name
                    confidence_score += 20
                    break
        
        # Extract account number
        for pattern in self.patterns['account_number']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                account = match.group(1) if match.groups() else match.group()
                if len(account) >= 10:
                    result['Account_Number'] = account
                    confidence_score += 15
                    break
        
        # Extract reference
        for pattern in self.patterns['reference']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ref = match.group(1) if match.groups() else match.group()
                if len(ref) > 3:
                    result['Reference'] = ref
                    confidence_score += 10
                    break
        
        # Extract transaction type
        for pattern in self.patterns['transaction_type']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['Transaction_Type'] = match.group(1)
                confidence_score += 10
                break
        
        result['Confidence'] = min(confidence_score, 100)
        return result
    
    def enhance_image_for_thai(self, image):
        """Enhanced image preprocessing specifically for Thai text"""
        try:
            # Convert to PIL Image if it's OpenCV format
            if isinstance(image, np.ndarray):
                image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Convert back to OpenCV format
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blur = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Apply dilation to make text thicker
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            dilated = cv2.dilate(cleaned, kernel, iterations=1)
            
            return dilated
            
        except Exception as e:
            logger.error(f"Error enhancing image for Thai: {e}")
            return image
    
    def preprocess_image(self, image_path):
        """Enhanced image preprocessing for better Thai OCR"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Could not load image")
            
            # Resize image if too small
            height, width = image.shape[:2]
            if height < 800 or width < 600:
                scale_factor = max(800/height, 600/width)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Apply Thai-specific enhancements
            enhanced = self.enhance_image_for_thai(image)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return None
    
    def process_image(self, path):
        """Process image with enhanced Thai OCR"""
        try:
            processed_image = self.preprocess_image(path)
            if processed_image is None:
                return None, ""
            
            # OCR configurations optimized for Thai
            configs = [
                '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzก-ฮ๐-๙:/-.,฿บาท ',
                '--oem 3 --psm 4 -c preserve_interword_spaces=1',
                '--oem 3 --psm 3',
                '--oem 3 --psm 6',
                '--oem 3 --psm 7',  # Single text line
                '--oem 3 --psm 8',  # Single word
            ]
            
            best_result = None
            best_text = ""
            highest_confidence = 0
            
            for config in configs:
                try:
                    # Use both Thai and English
                    text = pytesseract.image_to_string(
                        processed_image, 
                        lang='tha+eng', 
                        config=config
                    )
                    
                    # Clean the text
                    text = self.clean_ocr_text(text)
                    
                    result = self.extract_info(text)
                    
                    if result['Confidence'] > highest_confidence:
                        highest_confidence = result['Confidence']
                        best_result = result
                        best_text = text
                        
                except Exception as e:
                    logger.warning(f"OCR config failed: {config}, Error: {e}")
                    continue
            
            # If no good result, try with different preprocessing
            if not best_result or best_result['Confidence'] < 50:
                try:
                    # Try with original image
                    original = cv2.imread(path)
                    gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
                    text = pytesseract.image_to_string(gray, lang='tha+eng', config='--oem 3 --psm 6')
                    text = self.clean_ocr_text(text)
                    fallback_result = self.extract_info(text)
                    
                    if fallback_result['Confidence'] > highest_confidence:
                        best_result = fallback_result
                        best_text = text
                        
                except Exception as e:
                    logger.warning(f"Fallback OCR failed: {e}")
            
            return best_result, best_text
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            messagebox.showerror("Error", f"Failed to process image: {e}")
            return None, ""
    
    def clean_ocr_text(self, text):
        """Clean and normalize OCR text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[|\\]', '', text)
        
        # Fix common Thai OCR errors
        text = text.replace('กสิกร', 'กสิกร')
        text = text.replace('ไทยพาณิชย์', 'ไทยพาณิชย์')
        
        return text.strip()
    
    def process_image_async(self, path):
        """Process image in separate thread to prevent GUI freezing"""
        self.progress_bar.start()
        self.process_btn.config(state='disabled')
        self.status_label.config(text="🔄 Processing image...")
        
        def worker():
            try:
                result, raw_text = self.process_image(path)
                self.root.after(0, lambda: self.update_results(result, raw_text, path))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.root.after(0, self.processing_complete)
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def update_results(self, result, raw_text, image_path):
        """Update GUI with processing results"""
        if result:
            self.results_list.append({
                **result,
                'Image_Path': image_path,
                'Processed_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # Display image
            try:
                img = Image.open(image_path)
                img.thumbnail((350, 450), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                self.panel.config(image=img_tk, text="")
                self.panel.image = img_tk
            except Exception as e:
                logger.error(f"Error displaying image: {e}")
            
            # Display raw OCR text
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, raw_text)
            
            # Display extracted information with better formatting
            confidence_color = "#27ae60" if result['Confidence'] > 70 else "#f39c12" if result['Confidence'] > 40 else "#e74c3c"
            
            extracted_info = f"""📅 วันที่: {result['Date']}
⏰ เวลา: {result['Time']}
💰 จำนวนเงิน: {result['Amount']} บาท
🏦 ธนาคาร: {result['Bank']}
👤 ชื่อ: {result['Name']}
🔢 เลขบัญชี: {result['Account_Number']}
📝 รหัสอ้างอิง: {result['Reference']}
🔄 ประเภท: {result['Transaction_Type']}
📊 ความแม่นยำ: {result['Confidence']}%"""
            
            self.extracted_text.set(extracted_info)
            self.confidence_label.config(fg=confidence_color)
            
            self.update_results_count()
            self.status_label.config(text=f"✅ Processed successfully! Confidence: {result['Confidence']}%")
        else:
            self.status_label.config(text="❌ Failed to extract information")
    
    def processing_complete(self):
        """Called when processing is complete"""
        self.progress_bar.stop()
        self.process_btn.config(state='normal')
    
    def update_results_count(self):
        """Update the results counter"""
        count = len(self.results_list)
        total_confidence = sum(r['Confidence'] for r in self.results_list)
        avg_confidence = total_confidence / count if count > 0 else 0
        self.results_count.set(f"📊 ผลลัพธ์ทั้งหมด: {count} | ความแม่นยำเฉลี่ย: {avg_confidence:.1f}%")
    
    def select_image(self):
        """Select and process an image file"""
        filepath = filedialog.askopenfilename(
            title="เลือกรูปสลิป",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
                ("JPEG Files", "*.jpg *.jpeg"),
                ("PNG Files", "*.png"),
                ("All Files", "*.*")
            ]
        )
        if filepath:
            self.current_image_path = filepath
            self.process_image_async(filepath)
    
    def select_multiple_images(self):
        """Process multiple images at once"""
        filepaths = filedialog.askopenfilenames(
            title="เลือกหลายรูปสลิป",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
                ("All Files", "*.*")
            ]
        )
        
        if filepaths:
            total = len(filepaths)
            processed = 0
            
            for i, filepath in enumerate(filepaths, 1):
                self.root.title(f"กำลังประมวลผล {i}/{total} รูป...")
                self.status_label.config(text=f"กำลังประมวลผล {i}/{total}...")
                self.root.update()
                
                result, _ = self.process_image(filepath)
                if result:
                    self.results_list.append({
                        **result,
                        'Image_Path': filepath,
                        'Processed_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    processed += 1
            
            self.root.title("Thai OCR สลิปเงิน → CSV")
            self.update_results_count()
            self.status_label.config(text=f"✅ ประมวลผลเสร็จสิ้น: {processed}/{total} รูป")
            messagebox.showinfo("เสร็จสิ้น", f"ประมวลผลสำเร็จ {processed} จาก {total} รูป!")
    
    def export_to_excel(self):
        """Export results to Excel with Thai-friendly formatting"""
        if not self.results_list:
            messagebox.showwarning("แจ้งเตือน", "ไม่มีข้อมูลที่จะส่งออก")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
                title="บันทึกไฟล์ Excel"
            )
            
            if filename:
                df = pd.DataFrame(self.results_list)
                
                # Rename columns to Thai
                thai_columns = {
                    'Date': 'วันที่',
                    'Time': 'เวลา',
                    'Amount': 'จำนวนเงิน',
                    'Bank': 'ธนาคาร',
                    'Name': 'ชื่อ',
                    'Image': 'ไฟล์ภาพ'
                }
                df = df.rename(columns=thai_columns)
                
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='ผลการสแกนสลิป', index=False)
                    
                    workbook = writer.book
                    worksheet = writer.sheets['ผลการสแกนสลิป']
                    
                    # Define styles
                    header_style = NamedStyle(name='header')
                    header_style.font = Font(bold=True, size=12, name='Angsana New')
                    header_style.fill = PatternFill(start_color='CCE5FF', end_color='CCE5FF', fill_type='solid')
                    header_style.alignment = Alignment(horizontal='center', vertical='center')
                    header_style.border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )

                    # Apply header style
                    for cell in worksheet[1]:
                        cell.style = header_style

                    # Apply data styles
                    data_style = NamedStyle(name='data')
                    data_style.font = Font(size=11, name='Angsana New')
                    data_style.alignment = Alignment(horizontal='left', vertical='center')
                    data_style.border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )

                    # Format amount column
                    money_style = NamedStyle(name='money')
                    money_style.font = Font(size=11, name='Angsana New')
                    money_style.number_format = '#,##0.00'
                    money_style.alignment = Alignment(horizontal='right')
                    money_style.border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )

                    # Apply styles to data cells
                    for row in worksheet.iter_rows(min_row=2):
                        for cell in row:
                            if cell.column_letter == worksheet.cell(row=1, column=3).column_letter:  # Amount column
                                cell.style = money_style
                            else:
                                cell.style = data_style

                    # Auto-adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width

                    # Freeze top row
                    worksheet.freeze_panes = 'A2'
                    
                messagebox.showinfo("สำเร็จ", f"ส่งออกข้อมูลแล้ว: {filename}")
                
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการส่งออก: {str(e)}")
    
    def setup_gui(self):
        """Setup the GUI elements"""
        self.root = tk.Tk()
        self.root.title("Thai OCR สลิปเงิน → CSV")
        self.root.state('zoomed')
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x', pady=5)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="พร้อมสำหรับการประมวลผล")
        self.status_label.pack(pady=5)
        
        # Image panel
        self.panel = ttk.Label(main_frame)
        self.panel.pack(pady=10)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=5)
        
        self.process_btn = ttk.Button(btn_frame, text="เลือกรูปภาพ", command=self.select_image)
        self.process_btn.pack(side="left", padx=5)
        
        # Results text
        self.result_text = tk.Text(main_frame, height=10, width=50)
        self.result_text.pack(pady=5)
        
        # Extracted text
        self.extracted_text = tk.StringVar()
        self.confidence_label = ttk.Label(main_frame, textvariable=self.extracted_text)
        self.confidence_label.pack(pady=5)
        
        # Results count
        self.results_count = tk.StringVar(value="📊 ผลลัพธ์ทั้งหมด: 0")
        ttk.Label(main_frame, textvariable=self.results_count).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = ThaiOCRSlipProcessor()
    root.mainloop()

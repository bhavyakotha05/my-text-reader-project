# app.py (Displays PDF Text - NO AI NEEDED)

from flask import Flask, render_template, request, url_for
import os
from gtts import gTTS
from PIL import Image
import pytesseract
import PyPDF2
import shutil
import datetime
import glob


app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER

def cleanup_old_audio_files():
    try:
        mp3_files = glob.glob(os.path.join(app.config['STATIC_FOLDER'], '*.mp3'))
        for f in mp3_files:
            os.remove(f)
    except Exception as e:
        print(f"Error cleaning up old audio files: {e}")

def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text, None
    except Exception as e:
        return None, f"(OCR Error) {str(e)}"

def extract_text_from_pdf(pdf_path):
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
        
        if text.strip() == "":
            return None, "This seems to be a scanned PDF. This version only supports text-based PDFs."
        
        return text, None
            
    except Exception as e:
        return None, f"(PDF Error) {str(e)}"

def convert_text_to_speech(text):
    try:
        if not text or text.strip() == "":
            return None, "No text was extracted from the file to read."
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"speech_{timestamp}.mp3"
        audio_filepath = os.path.join(app.config['STATIC_FOLDER'], unique_filename)

        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(audio_filepath)
        
        return unique_filename, None
    
    except Exception as e:
        return None, f"(TTS Error) {str(e)}"

@app.route('/')
def index():
    # Kotta variables (is_description, description_text) ni add cheyyāli
    return render_template('index.html', audio_url=None, error=None, image_url=None, description_text=None, is_description=False)

@app.route('/upload', methods=['POST'])
def upload_file():
    
    cleanup_old_audio_files()

    if 'file' not in request.files:
        return render_template('index.html', error="No file selected. Please choose a file.", description_text=None, is_description=False)
    
    file = request.files['file']

    if file.filename == '':
        return render_template('index.html', error="No file selected. Please choose a file.", description_text=None, is_description=False)
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        extracted_text = None
        error_message = None
        image_url_for_template = None
        
        if file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                static_image_path = os.path.join(app.config['STATIC_FOLDER'], file.filename)
                shutil.copy(filepath, static_image_path)
                image_url_for_template = url_for('static', filename=file.filename)
            except Exception as e:
                print(f"Warning: Could not copy image. {e}")
            
            extracted_text, error_message = extract_text_from_image(filepath)

        elif file.filename.lower().endswith('.pdf'):
            extracted_text, error_message = extract_text_from_pdf(filepath)
            # Manam PDF image ni chūpiñchaṭlēdu, kābaṭṭi image_url_for_template 'None' gā uṇṭundi
            
        else:
            error_message = "Invalid file format. Only PDF, PNG, JPG are allowed."
            
        if error_message:
            return render_template('index.html', error=error_message, image_url=image_url_for_template, description_text=None, is_description=False) 
            
        audio_filename, error_message = convert_text_to_speech(extracted_text)
        
        if error_message:
            return render_template('index.html', error=error_message, image_url=image_url_for_template, description_text=extracted_text, is_description=False) 

        # Success! Ippuḍu text ni kūḍā HTML ki pampāli
        return render_template('index.html', 
                               audio_url=url_for('static', filename=audio_filename),
                               image_url=image_url_for_template,
                               description_text=extracted_text, # <-- KOTTAGĀ ADD CHESĀMU
                               is_description=False)          # <-- KOTTAGĀ ADD CHESĀMU

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(STATIC_FOLDER):
        os.makedirs(STATIC_FOLDER)
        

    app.run(host='0.0.0.0', port=5000, debug=True)

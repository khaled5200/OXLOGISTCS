from flask import Flask, request, jsonify, render_template
import pytesseract
from PIL import Image
import io
import qrcode

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process-image', methods=['POST'])
def process_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty file name"}), 400

    try:
        image = Image.open(file.stream)
        text = pytesseract.image_to_string(image)
        
        # Find the line containing "sptp"
        lines = text.splitlines()
        extracted_text = ""
        for line in lines:
            if "sptp" in line.lower():
                extracted_text = line.strip()
                break
        
        if not extracted_text:
            return jsonify({"error": "No text starting with 'sptp' found"}), 400

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(extracted_text)
        qr.make(fit=True)

        qr_image = qr.make_image(fill="black", back_color="white")
        qr_bytes = io.BytesIO()
        qr_image.save(qr_bytes, format="PNG")
        qr_bytes.seek(0)

        return jsonify({
            "text": extracted_text,
            "qr_code": qr_bytes.getvalue().hex()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, jsonify, render_template
import pytesseract
from PIL import Image
import io
import qrcode
import geoip2.database
import requests
import os

app = Flask(__name__)

# تحميل قاعدة البيانات من GitHub إذا لم تكن موجودة
geoip2_db_path = 'GeoLite2-Country.mmdb'
geoip2_db_url = 'https://github.com/khaled5200/OXLOGISTCS/raw/main/GeoLite2-Country.mmdb'

if not os.path.exists(geoip2_db_path):
    # تنزيل قاعدة البيانات إذا لم تكن موجودة محليًا
    response = requests.get(geoip2_db_url)
    if response.status_code == 200:
        with open(geoip2_db_path, 'wb') as f:
            f.write(response.content)
        print("GeoLite2-Country.mmdb file downloaded successfully.")
    else:
        print("Failed to download the GeoLite2-Country.mmdb file.")
        geoip2_db_path = None  # إذا فشل التحميل، لا نتابع

# إعداد قاعدة بيانات GeoIP إذا تم تحميل الملف بنجاح
reader = None
if geoip2_db_path:
    reader = geoip2.database.Reader(geoip2_db_path)

@app.route('/')
def index():
    country = "Unknown"

    # تحديد دولة الزائر بناءً على عنوان الـ IP
    if reader:
        try:
            ip_address = request.remote_addr
            response = reader.country(ip_address)
            country = response.country.name
        except Exception as e:
            country = "Unknown"

    # عرض الصفحة مع عدد الزوار ودولة الزوار
    return render_template('index.html', country=country)

@app.route('/process-image', methods=['POST'])
def process_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty file name"}), 400

    try:
        # استخراج النص من الصورة
        image = Image.open(file.stream)
        text = pytesseract.image_to_string(image)

        # البحث عن النص الذي يبدأ بـ "sptp"
        lines = text.splitlines()
        extracted_text = ""
        for line in lines:
            if "sptp" in line.lower():
                extracted_text = line.strip()
                break

        if not extracted_text:
            return jsonify({"error": "الصورة غلط"}), 400

        # إنشاء رمز QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(extracted_text)
        qr.make(fit=True)

        qr_image = qr.make_image(fill="black", back_color="white")
        qr_bytes = io.BytesIO()
        qr_image.save(qr_bytes, format="PNG")
        qr_bytes.seek(0)

        # تحويل الصورة إلى Base64 لإرسالها للمتصفح
        import base64
        qr_base64 = base64.b64encode(qr_bytes.getvalue()).decode("utf-8")

        return jsonify({"qr_code": qr_base64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)

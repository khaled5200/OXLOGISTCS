from flask import Flask, request, jsonify, render_template_string
import pytesseract
from PIL import Image
import io
import qrcode
import geoip2.database
import requests
import os

app = Flask(__name__)

# تحميل قاعدة البيانات GeoLite2-Country إذا لم تكن موجودة
geoip2_db_path = 'GeoLite2-Country.mmdb'
geoip2_db_url = 'https://github.com/khaled5200/OXLOGISTCS/raw/main/GeoLite2-Country.mmdb'

if not os.path.exists(geoip2_db_path):
    response = requests.get(geoip2_db_url)
    if response.status_code == 200:
        with open(geoip2_db_path, 'wb') as f:
            f.write(response.content)
        print("GeoLite2-Country.mmdb file downloaded successfully.")
    else:
        print("Failed to download the GeoLite2-Country.mmdb file.")
        geoip2_db_path = None

reader = geoip2.database.Reader(geoip2_db_path) if geoip2_db_path else None

@app.route('/')
def index():
    country = "Unknown"
    if reader:
        try:
            ip_address = request.remote_addr
            response = reader.country(ip_address)
            country = response.country.name
        except Exception as e:
            country = "Unknown"

    return render_template_string('''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>توليد رمز QR</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600&display=swap');


        body {
            font-family: 'Cairo', sans-serif;
            background-color: #f4f4f9;
            color: #333;
            padding-top: 50px;
            direction: rtl; /* يجعل النصوص من اليمين لليسار */
            text-align: right; /* يجعل المحاذاة تبدأ من اليمين */
        }
        .container {
            max-width: 700px;
            background-color: #fff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        }
        h1 {
            font-weight: 600;
            color: #2c3e50;
        }
        #result {
            margin-top: 20px;
            text-align: center;
        }
        footer {
            margin-top: 30px;
            font-size: 14px;
            color: #6c757d;
        }
    </style>
</head>
<body>
<div class="container text-center">
    <h1>مولد رمز الاستجابة السريعة</h1>
  <p style="font-family: 'Tajawal', sans-serif; font-size: 1.25rem; font-weight: bold; margin-top: 20px; color: #007bff;">
        تم تنفيذة لفريق OX LOGISTICS
    </p>
    <div class="input-group mb-3">
        <input type="file" id="fileInput" class="form-control" accept="image/*" onchange="uploadImage()">
    </div>
    <div id="result"></div>
    <footer>
        <p>بلد الزائر: <span id="visitor-country">{{ country }}</span></p>
    </footer>
</div>
<script>
    function uploadImage() {
        const formData = new FormData();
        const fileInput = document.getElementById("fileInput");
        formData.append("file", fileInput.files[0]);

        fetch("/process-image", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById("result").innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            } else {
                document.getElementById("result").innerHTML = `
                      <p class="text-success mt-2">تم انشاء الرمز بنجاح!</p>
                    <img src="data:image/png;base64,${data.qr_code}" alt="QR Code" class="img-fluid mt-3"><br>
        
     <div class="alert alert-success d-block w-100" role="alert" style="font-size: 1rem; font-weight: bold; font-family: 'Tajawal', sans-serif;">
  D E V E L O P E D  B Y :   <strong>K H A L E D</strong>
</div>



                `;
            }
        })
        .catch(error => {
            document.getElementById("result").innerHTML = `<div class="alert alert-danger">حدث خطأ أثناء معالجة الصورة.</div>`;
        });
    }
</script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    ''', country=country)

@app.route('/process-image', methods=['POST'])
def process_image():
    if 'file' not in request.files:
        return jsonify({"error": "لم يتم رفع أي ملف"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "اسم الملف فارغ"}), 400

    try:
        image = Image.open(file.stream)
        text = pytesseract.image_to_string(image)

        extracted_text = ""
        for line in text.splitlines():
            if "sptp" in line.lower():
                extracted_text = line.strip()
                break

        if not extracted_text:
            return jsonify({"error": "الصورة غير صحيحة، الرجاء إرسال الصورة الصحيحة."}), 400

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=4,
        )
        qr.add_data(extracted_text)
        qr.make(fit=True)

        qr_image = qr.make_image(fill="black", back_color="white")
        qr_bytes = io.BytesIO()
        qr_image.save(qr_bytes, format="PNG")
        qr_bytes.seek(0)

        import base64
        qr_base64 = base64.b64encode(qr_bytes.getvalue()).decode("utf-8")

        return jsonify({"qr_code": qr_base64})
    except Exception as e:
        return jsonify({"error": f"خطأ: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)

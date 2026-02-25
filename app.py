from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS # เพิ่มตัวนี้

app = Flask(__name__)
# อนุญาตให้ Flutter Web เชื่อมต่อได้
CORS(app, resources={r"/*": {"origins": "*"}}, expose_headers=["Content-Type", "Authorization"])
SLIP2GO_API_SECRET = 'QvCf0zm2AwStSwtufGk9xH_DoxWf0B4SIUfi5m28TRM=' 
SLIP2GO_ENDPOINT = 'https://connect.slip2go.com/api/verify-slip/qr-image/info'
@app.route('/')
def health_check():
    return "Slip2go API Service is Online!", 200

@app.route('/verify-slip', methods=['POST'])
def verify_slip():
    if 'slip_image' not in request.files:
        return jsonify({"success": False, "message": "Missing slip_image key"}), 400
    
    file = request.files['slip_image']
    image_data = file.read()

    # 2. แก้ไข Header เป็น Bearer Token
    headers = {
        'Authorization': f'Bearer {SLIP2GO_API_SECRET}',
        'Accept': 'application/json'
    }
    
    # 3. เปลี่ยนชื่อ Key จาก 'files' เป็น 'file' ตามคู่มือหน้า 12
    files = {
        'file': (file.filename, image_data, file.content_type)
    }
    # ส่งต่อให้ Slip2go โดยใช้ชื่อ 'files' ตาม Spec ของเขา
    try:
        response = requests.post(SLIP2GO_ENDPOINT, headers=headers, files=files)
        result = response.json()

        # ตรวจสอบว่า Slip2go ตรวจสำเร็จและพบข้อมูลสลิปหรือไม่
        # Slip2go จะส่งสถานะ success มาใน field 'status'
# 4. เช็คสถานะความสำเร็จ (เอกสารระบุว่าถ้าสำเร็จจะไม่มี Error และมีข้อมูลใน data)
        if response.status_code == 200 and result.get('success') == True:
            slip_info = result['data'] 
            return jsonify({
                "success": True,
                "data": {
                    "amount": slip_info['amount'],
                    "transRef": slip_info['transRef'],
                    # ปรับชื่อ field ตามตัวอย่าง Response ในหน้า 13-14
                    "receiver": slip_info['receiver']['account']['name'],
                    "sender": slip_info['sender']['account']['name']
                }
            }), 200
        else:
            return jsonify({
                "success": False, 
                "message": result.get('message', 'ตรวจสอบสลิปไม่สำเร็จ (สลิปอาจซ้ำหรือผิดประเภท)')
            }), 400

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS # เพิ่มตัวนี้

app = Flask(__name__)
# อนุญาตให้ Flutter Web เชื่อมต่อได้
CORS(app, resources={r"/*": {"origins": "*"}}, expose_headers=["Content-Type", "Authorization"])
SLIP2GO_API_SECRET = 'QvCf0zm2AwStSwtufGk9xH_DoxWf0B4SIUfi5m28TRM=' 
SLIP2GO_ENDPOINT = 'https://api.slip2go.com/api/v1/verify-slip/image/info'

@app.route('/')
def health_check():
    return "Slip2go API Service is Online!", 200

@app.route('/verify-slip', methods=['POST'])
def verify_slip():
    # 1. ตรวจสอบว่ามี Key ชื่อ 'slip_image' ส่งมาไหม
    if 'slip_image' not in request.files:
        return jsonify({"success": False, "message": "Missing slip_image key"}), 400
    
    file = request.files['slip_image']
    
    # 2. อ่านข้อมูลครั้งเดียวเก็บไว้
    image_data = file.read()
    if not image_data:
        return jsonify({"success": False, "message": "File is empty"}), 400

    headers = {'x-api-secret': SLIP2GO_API_SECRET}
    
    # 3. ส่งต่อให้ Slip2go (ใช้ Key 'files' ตาม Spec ของเขา)
    files = [('files', (file.filename, image_data, file.content_type))]
    try:
        response = requests.post(SLIP2GO_ENDPOINT, headers=headers, files=files)
        result = response.json()

        # ตรวจสอบว่า Slip2go ตรวจสำเร็จและพบข้อมูลสลิปหรือไม่
        # Slip2go จะส่งสถานะ success มาใน field 'status'
        if response.status_code == 200 and result.get('status') == 'success':
            # ดึงข้อมูลตัวแรกจาก list 'data' มาจัดรูปแบบใหม่ให้แอป Flutter เข้าใจง่าย
            slip_info = result['data'][0] 
            return jsonify({
                "success": True,
                "data": {
                    "amount": slip_info['amount'],
                    "transRef": slip_info['transRef'],
                    "receiver": slip_info['receiver']['displayName'],
                    "sender": slip_info['sender']['displayName']
                }
            }), 200
        else:
            # กรณีรูปภาพไม่ใช่สลิป หรือตรวจไม่ผ่าน
            return jsonify({
                "success": False, 
                "message": result.get('message', 'ตรวจสอบสลิปไม่สำเร็จ')
            }), 400

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, expose_headers=["Content-Type", "Authorization"])

# ตั้งค่า Config
SLIP2GO_API_SECRET = 'QvCf0zm2AwStSwtufGk9xH_DoxWf0B4SIUfi5m28TRM=' 
SLIP2GO_ENDPOINT = 'https://connect.slip2go.com/api/verify-slip/qr-image/info'

@app.route('/')
def health_check():
    return "Slip2go API Service is Online!", 200

@app.route('/verify-slip', methods=['POST'])
def verify_slip():
    # 1. ตรวจสอบว่า Client ส่งไฟล์มาในชื่อ Key ว่า 'file' หรือไม่
    # ปรับตรงนี้ให้รับ 'file' ตามที่คุณต้องการ
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Missing 'file' key in request"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"}), 400

    # 2. เตรียม Header
    # หมายเหตุ: บางกรณี Slip2go อาจใช้ x-api-key แทน Bearer โปรดเช็คคู่มืออีกครั้ง
    # แต่ถ้าคุณมั่นใจว่าเป็น Bearer ก็ใช้ตามนี้ได้เลยครับ
    headers = {
        'Authorization': f'Bearer {SLIP2GO_API_SECRET}',
        'Accept': 'application/json'
    }
    
    # 3. เตรียมไฟล์เพื่อส่งต่อ (ใช้ชื่อ Key ว่า 'file' ตาม Spec ของ Slip2Go)
    # เราส่ง stream ของไฟล์ไปโดยตรง ไม่ต้อง .read() เพื่อประหยัด Memory
    files = {
        'file': (file.filename, file.stream, file.content_type)
    }

    try:
        # 4. ส่ง Request ไปยัง Slip2Go
        response = requests.post(SLIP2GO_ENDPOINT, headers=headers, files=files)
        
        # ตรวจสอบว่า Response เป็น JSON หรือไม่
        try:
            result = response.json()
        except ValueError:
            return jsonify({"success": False, "message": "Invalid response from Slip2Go"}), 502

        # 5. จัดการผลลัพธ์ตามเอกสารหน้า 13-14
        if response.status_code == 200 and result.get('success') == True:
            slip_info = result.get('data', {})
            return jsonify({
                "success": True,
                "data": {
                    "amount": slip_info.get('amount'),
                    "transRef": slip_info.get('transRef'),
                    "receiver": slip_info.get('receiver', {}).get('account', {}).get('name'),
                    "sender": slip_info.get('sender', {}).get('account', {}).get('name'),
                    "transDate": slip_info.get('transDate'),
                    "transTime": slip_info.get('transTime')
                }
            }), 200
        else:
            # กรณี Error จาก Slip2Go
            return jsonify({
                "success": False, 
                "message": result.get('message', 'ตรวจสอบสลิปไม่สำเร็จ'),
                "error_code": result.get('code')
            }), response.status_code

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
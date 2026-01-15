import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from google import genai

app = Flask(__name__)

# --- ส่วนตั้งค่า ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ตั้งค่า Client ของ Google GenAI (แบบใหม่)
client = genai.Client(api_key=GEMINI_API_KEY)

# --- ข้อมูลความรู้ของบอท ---
CITCOMS_KNOWLEDGE = """
คุณคือผู้ช่วยอัจฉริยะประจำ CITCOMS (กองบริการเทคโนโลยีสารสนเทศและการสื่อสาร) มหาวิทยาลัยนเรศวร
หน้าที่ของคุณคือตอบคำถามนิสิตและบุคลากรด้วยภาษาที่สุภาพ เป็นกันเอง และกระชับ
ข้อมูลบริการมีดังนี้:
1. บริการ NU Mail: นิสิตและบุคลากรขอได้ฟรี ที่เคาน์เตอร์บริการ ชั้น 1 หรือสมัครออนไลน์
2. บริการ Microsoft 365: ดาวน์โหลดฟรีที่ portal.office.com ใช้รหัสเดียวกับ NU Mail
3. บริการซ่อมคอมพิวเตอร์: รับปรึกษาปัญหา Software เบื้องต้นฟรี! (ไม่รับซ่อม Hardware เช่น จอแตก)
4. เวลาทำการ: จันทร์-ศุกร์ 08.30 - 16.30 น. (เว้นวันหยุดราชการ)
5. เบอร์ติดต่อ: 0-5596-15xx
"""

@app.route("/", methods=['GET'])
def home():
    return "CITCOMS Bot is Running!", 200

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()
    print(f"User asking: {user_msg}")

    reply_text = "" # สร้างตัวแปรมารอรับคำตอบ

    try:
        # เตรียมคำสั่ง (Prompt)
        prompt = f"{CITCOMS_KNOWLEDGE}\n\nUser ถามว่า: {user_msg}\nตอบสั้นๆ และสุภาพ:"
        
        # ส่งให้ Gemini 3 ประมวลผล
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt  # แก้จาก msg เป็น prompt
        )
        reply_text = response.text # แก้จาก reply เป็น reply_text
        
    except Exception as e:
        reply_text = "ขออภัย ระบบขัดข้องชั่วคราว (Gemini Error)"
        print(f"Error: {e}")

    # ส่งข้อความกลับเข้า LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run()

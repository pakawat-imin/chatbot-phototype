import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# --- ส่วนตั้งค่า (ดึง Key จาก Render) ---
# ไม่ต้องแก้ตรงนี้ครับ เดี๋ยวเราไปกรอกรหัสจริงในเว็บ Render
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- ข้อมูลความรู้ของบอท (แก้ไขข้อมูลตรงนี้ได้เลย) ---
CITCOMS_KNOWLEDGE = """
คุณคือผู้ช่วยอัจฉริยะประจำ CITCOMS (กองบริการเทคโนโลยีสารสนเทศและการสื่อสาร) มหาวิทยาลัยนเรศวร
หน้าที่ของคุณคือตอบคำถามนิสิตและบุคลากรด้วยภาษาที่สุภาพ เป็นกันเอง และกระชับ
ข้อมูลบริการมีดังนี้:
1. บริการ NU Mail: นิสิตและบุคลากรขอได้ฟรี ที่เคาน์เตอร์บริการ ชั้น 1 หรือสมัครออนไลน์
2. บริการ Microsoft 365: ดาวน์โหลดฟรีที่ portal.office.com ใช้รหัสเดียวกับ NU Mail
3. บริการซ่อมคอมพิวเตอร์: รับปรึกษาปัญหา Software เบื้องต้นฟรี! (ไม่รับซ่อม Hardware เช่น จอแตก)
4. เวลาทำการ: จันทร์-ศุกร์ 08.30 - 16.30 น. (เว้นวันหยุดราชการ)
5. เบอร์ติดต่อ: 0-5596-15xx
(คุณสามารถเพิ่มข้อมูลอื่นๆ ได้ที่นี่...)
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

    try:
        # ส่งข้อมูลให้ Gemini ประมวลผล
        prompt = f"{CITCOMS_KNOWLEDGE}\n\nUser ถามว่า: {user_msg}\nตอบสั้นๆ และสุภาพ:"
        response = model.generate_content(prompt)
        reply_text = response.text
    except Exception as e:
        reply_text = "ขออภัย ระบบขัดข้องชั่วคราว"
        print(f"Error: {e}")

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run()

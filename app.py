import os
from flask import Flask, request, render_template_string, send_file
from fpdf import FPDF
import datetime

app = Flask(__name__)

# 安全讀取環境變數 (稍後在 Render 設定)
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

@app.route('/')
def index():
    # 這裡先放一個極簡的測試介面
    return "<h1>蕨積：碳中和系統測試中</h1><p>GitHub to Render 自動化測試成功！</p>"

if __name__ == '__main__':
    # 這裡讓本地測試也能跑
    app.run(debug=True)

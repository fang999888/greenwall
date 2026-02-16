import os
import io
import requests
from flask import Flask, request, render_template_string, send_file
from fpdf import FPDF
import datetime

app = Flask(__name__)

# --- 專業數據配置 ---
TRANSPORT_FACTOR = 0.25  # 貨車排放係數 (kg CO2e/km)
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

PLANT_DETAILS = {
    "succulent": {"name": "多肉植物 (2-3吋盆)", "sink": 0.1, "desc": "依據多肉年生長率估算。"},
    "potted": {"name": "觀葉盆栽 (5吋盆)", "sink": 0.5, "desc": "依據環境部室內淨化空氣植物數據。"},
    "seedling": {"name": "原生樹苗 (30-50cm)", "sink": 2.0, "desc": "依據林業署造林固碳量表。"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蕨積 | 永續物流提案系統</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f0f4f0; padding: 20px; color: #1b4332; }
        .card { max-width: 500px; margin: auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #2d6a4f; margin-bottom: 25px; }
        .input-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; font-size: 0.9em; }
        input, select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #2d6a4f; color: white; border: none; border-radius: 10px; font-size: 18px; cursor: pointer; margin-top: 20px; font-weight: bold; }
        .footer-note { font-size: 0.75em; color: #888; text-align: center; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>蕨積 - 碳中和專案系統</h2>
        <form action="/download" method="post">
            <div class="input-group">
                <label>專案名稱</label>
                <input type="text" name="event_name" placeholder="例如：2026 綠色論壇" required>
            </div>
            <div class="input-group">
                <label>出貨起點 (苗圃或辦公室)</label>
                <input type="text" name="start_location" placeholder="例如：彰化縣田尾鄉" required>
            </div>
            <div class="input-group">
                <label>活動目的地 (會場地址)</label>
                <input type="text" name="destination" placeholder="例如：台北世貿一館" required>
            </div>
            <div class="input-group">
                <label>參與人數</label>
                <input type="number" name="guests" value="100">
            </div>
            <div class="input-group">
                <label>活動時數 (小時)</label>
                <input type="number" name="hours" value="3">
            </div>
            <div class="input-group">
                <label>選擇抵銷植物</label>
                <select name="p_type">
                    <option value="succulent">多肉植物 (0.1kg/年)</option>
                    <option value="potted" selected>觀葉盆栽 (0.5kg/年)</option>
                    <option value="seedling">原生樹苗 (2.0kg/年)</option>
                </select>
            </div>
            <button type="submit">產出專業 PDF 提案</button>
        </form>
        <div class="footer-note">Powered by 蕨積 - 數位碳中和顧問模組</div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    try:
        # 讀取表單
        name = request.form.get('event_name')
        start_loc = request.form.get('start_location')
        dest = request.form.get('destination')
        guests = int(request.form.get('guests'))
        hours = int(request.form.get('hours'))
        p_type = request.form.get('p_type')

        # Google Maps 里程計算
        dist_km, trans_em = 0, 0
        if GOOGLE_MAPS_KEY:
            api_url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={start_loc}&destinations={dest}&key={GOOGLE_MAPS_KEY}&language=zh-TW"
            res = requests.get(api_url).json()
            if res['status'] == 'OK' and res['rows'][0]['elements'][0].get('status') == 'OK':
                dist_km = res['rows'][0]['elements'][0]['distance']['value'] / 1000
                trans_em = dist_km * TRANSPORT_FACTOR

        # 碳排計算
        act_em = guests * hours * 0.5
        total_em = act_em + trans_em
        plant = PLANT_DETAILS[p_type]
        count = int(total_em / plant['sink']) + 1

        # PDF 生成
        pdf = FPDF()
        pdf.add_page()
        font_path = os.path.join(os.getcwd(), 'font.ttf')
        f_name = 'Chinese' if os.path.exists(font_path) else 'Arial'
        if os.path.exists(font_path): pdf.add_font(f_name, '', font_path)

        # 標題
        pdf.set_font(f_name, size=18)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(0, 15, "綠色活動碳中和提案報告", ln=True, align='C')
        pdf.ln(5)

        # 專案資訊
        pdf.set_font(f_name, size=11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"專案名稱：{name}", ln=True)
        pdf.cell(0, 8, f"運輸路徑：{start_loc} ⮕ {dest}", ln=True)
        pdf.cell(0, 8, f"運輸總里程：{dist_km:.1f} km", ln=True)
        pdf.ln(5)

        # 數據區
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(0, 10, " 【預估排碳細節】", ln=True, fill=True)
        pdf.cell(0, 8, f" 1. 活動人為排碳：{act_em:.2f} kg CO2e", ln=True)
        pdf.cell(0, 8, f" 2. 物流運輸排碳：{trans_em:.2f} kg CO2e", ln=True)
        pdf.cell(0, 10, f" ⮕ 總計排放總量：{total_em:.2f} kg CO2e", ln=True)
        pdf.ln(5)

        # 補償方案
        pdf.set_fill_color(232, 245, 233)
        pdf.cell(0, 10, " 【碳補償建議方案】", ln=True, fill=True)
        pdf.cell(0, 8, f" ● 建議抵銷植物：{plant['name']}", ln=True)
        pdf.cell(0, 8, f" ● 建議贈送數量：{count} 盆", ln=True)
        pdf.ln(10)

        # 註腳
        pdf.set_font(f_name, size=9)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 6, f"數據聲明：\n{plant['desc']}\n運輸計算採用 Google Maps API 實測里程，係數對標 3.5 噸貨車標準。本報告由蕨積系統自動產出，僅供 CSR 提案參考。")

        # 輸出
        pdf_bytes = pdf.output()
        return send_file(io.BytesIO(pdf_bytes), as_attachment=True, download_name=f"Proposal_{datetime.date.today()}.pdf", mimetype='application/pdf')

    except Exception as e:
        return f"系統錯誤：{str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

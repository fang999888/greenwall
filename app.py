import os
import io
import requests
from flask import Flask, request, render_template_string, send_file
from fpdf import FPDF
import datetime

app = Flask(__name__)

# --- 配置區 ---
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
BASE_LOCATION = "台北車站"  # 請改為您的苗圃或辦公室地址
TRANSPORT_FACTOR = 0.25    # 貨車排放係數 (kg CO2e/km)

PLANT_DETAILS = {
    "succulent": {"name": "多肉植物 (2-3吋盆)", "sink": 0.1, "desc": "依據多肉年生長率估算。"},
    "potted": {"name": "觀葉盆栽 (5吋盆)", "sink": 0.5, "desc": "依據環境部室內淨化空氣植物數據。"},
    "seedling": {"name": "原生樹苗 (30-50cm)", "sink": 2.0, "desc": "依據林業署造林固碳量表。"}
}

# --- 前端介面 ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蕨積 | 專業綠色提案系統</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f0f4f0; padding: 20px; color: #1b4332; }
        .card { max-width: 500px; margin: auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #2d6a4f; margin-bottom: 25px; }
        .input-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; font-size: 0.9em; }
        input, select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; box-sizing: border-box; }
        .hint { font-size: 0.8em; color: #666; margin-top: 4px; }
        button { width: 100%; padding: 15px; background: #2d6a4f; color: white; border: none; border-radius: 10px; font-size: 18px; cursor: pointer; margin-top: 20px; font-weight: bold; }
        .result-box { background: #e8f5e9; padding: 15px; border-radius: 10px; margin-top: 20px; font-size: 0.95em; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="card">
        <h2>蕨積 - 綠色活動專家</h2>
        <form action="/download" method="post">
            <div class="input-group">
                <label>活動專案名稱</label>
                <input type="text" name="event_name" placeholder="例如：永續金融論壇" required>
            </div>
            <div class="input-group">
                <label>活動詳細地點 (計算運輸碳排)</label>
                <input type="text" name="destination" placeholder="例如：台北市信義路五段7號" required>
                <div class="hint">起點：基地 ({base})</div>
            </div>
            <div class="input-group">
                <label>參與人數</label>
                <input type="number" name="guests" value="100">
            </div>
            <div class="input-group">
                <label>活動時數</label>
                <input type="number" name="hours" value="3">
            </div>
            <div class="input-group">
                <label>選擇植物</label>
                <select name="p_type">
                    <option value="succulent">精緻多肉 (0.1kg/年)</option>
                    <option value="potted" selected>觀葉盆栽 (0.5kg/年)</option>
                    <option value="seedling">原生樹苗 (2.0kg/年)</option>
                </select>
            </div>
            <button type="submit">生成並下載專業提案 PDF</button>
        </form>
    </div>
</body>
</html>
""".replace("{base}", BASE_LOCATION)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    try:
        # 1. 取得基本數據
        name = request.form.get('event_name')
        dest = request.form.get('destination')
        guests = int(request.form.get('guests'))
        hours = int(request.form.get('hours'))
        p_type = request.form.get('p_type')
        
        # 2. 計算運輸距離 (Google Maps)
        dist_km, trans_em = 0, 0
        if GOOGLE_MAPS_KEY:
            map_url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={BASE_LOCATION}&destinations={dest}&key={GOOGLE_MAPS_KEY}"
            res = requests.get(map_url).json()
            if res['status'] == 'OK' and res['rows'][0]['elements'][0].get('distance'):
                dist_km = res['rows'][0]['elements'][0]['distance']['value'] / 1000
                trans_em = dist_km * TRANSPORT_FACTOR

        # 3. 計算活動碳排與植物抵銷
        act_em = guests * hours * 0.5
        total_em = act_em + trans_em
        plant = PLANT_DETAILS[p_type]
        count = int(total_em / plant['sink']) + 1

        # 4. 產出 PDF
        pdf = FPDF()
        pdf.add_page()
        font_path = os.path.join(os.getcwd(), 'font.ttf')
        font_name = 'Chinese' if os.path.exists(font_path) else 'Arial'
        if os.path.exists(font_path): pdf.add_font(font_name, '', font_path)

        pdf.set_font(font_name, size=18)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(0, 15, "碳中和活動提案報告書", ln=True, align='C')
        
        pdf.set_font(font_name, size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        pdf.cell(0, 10, f"專案名稱：{name}", ln=True)
        pdf.cell(0, 10, f"運輸距離：{dist_km:.1f} km (起點：{BASE_LOCATION})", ln=True)
        pdf.ln(5)

        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, " 【碳排細節】", ln=True, fill=True)
        pdf.cell(0, 10, f" - 活動人為排放：{act_em:.2f} kg CO2e", ln=True)
        pdf.cell(0, 10, f" - 運輸里程排放：{trans_em:.2f} kg CO2e", ln=True)
        pdf.set_font(font_name, 'B', 12)
        pdf.cell(0, 10, f" - 總計預估排放：{total_em:.2f} kg CO2e", ln=True)
        
        pdf.ln(5)
        pdf.set_font(font_name, size=12)
        pdf.set_fill_color(232, 245, 233)
        pdf.cell(0, 10, " 【碳補償建議】", ln=True, fill=True)
        pdf.cell(0, 10, f" - 建議贈送數量：{count} 盆", ln=True)
        pdf.cell(0, 10, f" - 指定植物規格：{plant['name']}", ln=True)

        pdf.set_y(-40)
        pdf.set_font(font_name, size=9)
        pdf.multi_cell(0, 5, f"資料來源：{plant['desc']}\\n運輸係數採用 0.25kg/km (3.5噸貨車)。\\n蕨積 - 為您打造精準的永續生活提案。")

        output = io.BytesIO()
        output.write(pdf.output())
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="Proposal.pdf", mimetype='application/pdf')

    except Exception as e:
        return f"系統錯誤：{str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

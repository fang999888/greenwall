import os
import io
from flask import Flask, request, render_template_string, send_file
from fpdf import FPDF
import datetime

app = Flask(__name__)

# --- 係數配置 ---
VENUE_FACTORS = {"indoor": 0.5, "outdoor": 0.2}
FREIGHT_FACTORS = {"small_truck": 0.20, "large_truck": 0.35, "scooter": 0.05}
TRAVEL_FACTORS = {"car": 0.173, "shuttle": 0.045, "mrt": 0.035, "scooter": 0.055, "walk": 0.0}

PLANT_DETAILS = {
    "succulent": {"name": "多肉植物", "sink": 0.1, "desc": "多肉植物平均年生長率估算。"},
    "potted": {"name": "觀葉盆栽", "sink": 0.5, "desc": "環境部公告室內淨化空氣植物數據。"},
    "seedling": {"name": "原生樹苗", "sink": 2.0, "desc": "林業署常用造林樹種固碳量表。"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蕨積 | 碳中和提案系統</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f4f7f4; padding: 20px; color: #1b4332; }
        .card { max-width: 550px; margin: auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #2d6a4f; margin-bottom: 25px; }
        .section-title { background: #2d6a4f; color: white; padding: 8px 15px; border-radius: 5px; font-size: 1em; margin-top: 25px; }
        .input-group { margin-top: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; font-size: 0.85em; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 15px; box-sizing: border-box; }
        .row { display: flex; gap: 10px; }
        .row div { flex: 1; }
        button { width: 100%; padding: 15px; background: #e67e22; color: white; border: none; border-radius: 10px; font-size: 18px; cursor: pointer; margin-top: 30px; font-weight: bold; }
        button:hover { background: #d35400; }
        .footer-note { font-size: 0.75em; color: #888; text-align: center; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>蕨積 - 綠色轉型顧問</h2>
        <form action="/download" method="post">
            <div class="input-group">
                <label>專案/活動名稱</label>
                <input type="text" name="event_name" placeholder="例如：2026 企業永續家庭日" required>
            </div>

            <div class="section-title">第一階段：碳排總量計算</div>
            <div class="row">
                <div class="input-group">
                    <label>場域類型</label>
                    <select name="venue_mode">
                        <option value="indoor">室內 (空調/照明)</option>
                        <option value="outdoor">室外 (通風空間)</option>
                    </select>
                </div>
                <div class="input-group">
                    <label>預計人數</label>
                    <input type="number" name="guests" value="100">
                </div>
            </div>
            
            <div class="input-group">
                <label>物流與交通 (單程公里數)</label>
                <div class="row">
                    <input type="number" name="log_km" placeholder="植物運輸 km" value="20">
                    <input type="number" name="tra_km" placeholder="人員交通 km" value="10">
                </div>
            </div>

            <div class="section-title">第二階段：植物補救方案</div>
            <div class="input-group">
                <label>選擇您想贈送/佈置的植物</label>
                <select name="p_type">
                    <option value="succulent">精緻多肉 (抵銷 0.1kg/年)</option>
                    <option value="potted" selected>觀葉盆栽 (抵銷 0.5kg/年)</option>
                    <option value="seedling">原生樹苗 (抵銷 2.0kg/年)</option>
                </select>
            </div>

            <button type="submit">計算碳債並下載補救提案</button>
        </form>
        <div class="footer-note">※ 先告知排放，再提供綠色解決方案</div>
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
        # 1. 取得數據
        name = request.form.get('event_name')
        guests = int(request.form.get('guests', 0))
        venue_mode = request.form.get('venue_mode')
        log_km = float(request.form.get('log_km', 0))
        tra_km = float(request.form.get('tra_km', 0))
        p_type = request.form.get('p_type')

        # 2. 計算碳排 (上半部)
        act_em = guests * 3 * VENUE_FACTORS[venue_mode] # 預設3小時
        log_em = log_km * FREIGHT_FACTORS["large_truck"] * 2 
        peo_em = guests * tra_km * TRAVEL_FACTORS["mrt"] * 2
        total_em = act_em + log_em + peo_em

        # 3. 計算補救 (下半部)
        plant = PLANT_DETAILS[p_type]
        count = int(total_em / plant['sink']) + 1

        # 4. 生成 PDF
        pdf = FPDF()
        pdf.add_page()
        font_path = os.path.join(os.getcwd(), 'font.ttf')
        f_name = 'Chinese' if os.path.exists(font_path) else 'Arial'
        if os.path.exists(font_path): pdf.add_font(f_name, '', font_path)

        # PDF - 上半部：告知排放
        pdf.set_font(f_name, size=18)
        pdf.set_text_color(200, 50, 50) # 紅色警示
        pdf.cell(0, 15, f"【{name}】碳排預估報告", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font(f_name, size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "一、活動預期排放總量（碳負債）：", ln=True)
        pdf.set_fill_color(255, 235, 235)
        pdf.cell(0, 10, f"    ● 總排放量：{total_em:.2f} kg CO2e", ln=True, fill=True)
        pdf.set_font(f_name, size=10)
        pdf.cell(0, 7, f"      (含場域用電: {act_em:.1f}kg, 物流運輸: {log_em:.1f}kg, 人員交通: {peo_em:.1f}kg)", ln=True)
        pdf.ln(10)

        # PDF - 下半部：補救方案
        pdf.set_font(f_name, size=14)
        pdf.set_text_color(45, 106, 79) # 綠色希望
        pdf.cell(0, 10, "二、蕨積綠色補救建議方案：", ln=True)
        pdf.set_fill_color(232, 245, 233)
        pdf.set_font(f_name, size=12)
        pdf.cell(0, 12, f"    透過贈送 {count} 盆【{plant['name']}】來抵銷本次排放", ln=True, fill=True)
        
        pdf.ln(10)
        pdf.set_font(f_name, size=9)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 6, f"補救原理：\n{plant['desc']}\n我們建議將植物作為活動贈禮，讓碳中和行動從會場延續到與會者的日常生活中。")

        # 頁尾
        pdf.set_y(-30)
        pdf.set_font(f_name, size=10)
        pdf.cell(0, 10, "蕨積 - 讓每一場活動都與自然共生", align='C', ln=True)

        return send_file(io.BytesIO(pdf.output()), as_attachment=True, download_name="Green_Action.pdf")
    except Exception as e:
        return f"錯誤：{str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

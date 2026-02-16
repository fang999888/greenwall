import os
import io
from flask import Flask, request, render_template_string, send_file
from fpdf import FPDF
import datetime

app = Flask(__name__)

# --- 科學係數配置 (單位: kg CO2e) ---
VENUE_FACTORS = {"indoor": 0.5, "outdoor": 0.2} # 包含電力與廢棄物
FREIGHT_FACTOR = 0.35  # 3.5噸柴油貨車
TRAVEL_FACTOR = 0.035  # 複合式大眾運輸平均值 (IPCC/環境部)

PLANT_DETAILS = {
    "succulent": {"name": "多肉植物", "sink": 0.1, "desc": "CAM代謝植物，生長緩慢但環境適應力強。"},
    "potted": {"name": "觀葉盆栽", "sink": 0.5, "desc": "C3植物，具備高葉面積比，淨化空氣效能佳。"},
    "seedling": {"name": "原生樹苗", "sink": 2.0, "desc": "木本植物，具備長期生物量儲存潛力。"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蕨積 | ESG 專業試算系統</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #ecefe9; padding: 20px; color: #1b4332; }
        .card { max-width: 600px; margin: auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        h2 { border-bottom: 2px solid #2d6a4f; padding-bottom: 10px; color: #2d6a4f; }
        .input-group { margin-top: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; }
        input, select { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; }
        button { width: 100%; padding: 18px; background: #2d6a4f; color: white; border: none; border-radius: 6px; font-size: 18px; cursor: pointer; margin-top: 30px; font-weight: bold; transition: 0.3s; }
        button:hover { background: #1b4332; }
    </style>
</head>
<body>
    <div class="card">
        <h2>蕨積 - 綠色活動專業試算</h2>
        <form action="/download" method="post">
            <div class="input-group">
                <label>活動專案名稱 (用於報告抬頭)</label>
                <input type="text" name="event_name" placeholder="例如：2026 企業永續家庭日" required>
            </div>
            <div class="input-group">
                <label>活動屬性與規模</label>
                <div style="display:flex; gap:10px;">
                    <select name="venue_mode">
                        <option value="indoor">室內場域 (電力負載較高)</option>
                        <option value="outdoor">半戶外/室外 (自然通風)</option>
                    </select>
                    <input type="number" name="guests" value="100" placeholder="與會人數">
                </div>
            </div>
            <div class="input-group">
                <label>與會人員平均單程通勤 (km)</label>
                <input type="number" name="tra_km" value="10">
            </div>
            <div class="input-group">
                <label>物流基地至會場距離 (km)</label>
                <input type="number" name="log_km" value="50">
            </div>
            <div class="input-group">
                <label>選定抵銷植物類型</label>
                <select name="p_type">
                    <option value="succulent">精緻多肉植物</option>
                    <option value="potted" selected>景觀觀葉盆栽</option>
                    <option value="seedling">原生造林樹苗</option>
                </select>
            </div>
            <button type="submit">生成專業 ESG 碳中和報告</button>
        </form>
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
        name = request.form.get('event_name')
        guests = int(request.form.get('guests', 0))
        venue_mode = request.form.get('venue_mode')
        tra_km = float(request.form.get('tra_km', 0))
        log_km = float(request.form.get('log_km', 0))
        p_type = request.form.get('p_type')

        # --- 科學計算邏輯 ---
        # 1. 範疇二：電力排放 (活動3hr)
        scope2_em = guests * 3 * VENUE_FACTORS[venue_mode]
        # 2. 範疇三：商務旅行與上游運輸
        scope3_travel = guests * tra_km * TRAVEL_FACTOR * 2 # 來回
        scope3_logistics = log_km * FREIGHT_FACTOR * 2 # 來回
        
        grand_total = scope2_em + scope3_travel + scope3_logistics
        plant = PLANT_DETAILS[p_type]
        count = int(grand_total / plant['sink']) + 1

        # --- PDF 生成 ---
        pdf = FPDF()
        pdf.add_page()
        font_path = os.path.join(os.getcwd(), 'font.ttf')
        f_name = 'Chinese' if os.path.exists(font_path) else 'Arial'
        if os.path.exists(font_path): pdf.add_font(f_name, '', font_path)

        # 頁首標題
        pdf.set_font(f_name, size=22)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(0, 20, "活動全生命週期碳足跡與中和報告", ln=True, align='C')
        pdf.set_font(f_name, size=10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"報告編號：JUEJI-{datetime.datetime.now().strftime('%Y%m%d%H%M')}", ln=True, align='C')
        pdf.ln(10)

        # 1. 活動基本資訊
        pdf.set_font(f_name, size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(240, 245, 240)
        pdf.cell(0, 10, f"  專案名稱：{name}", ln=True, fill=True)
        pdf.cell(0, 10, f"  評估日期：{datetime.date.today()}", ln=True)
        pdf.ln(5)

        # 2. 碳排放分析 (科學數據)
        pdf.set_font(f_name, size=14)
        pdf.set_text_color(180, 50, 50)
        pdf.cell(0, 10, "第一部分：排放足跡分析 (Emissions Inventory)", ln=True)
        
        pdf.set_font(f_name, size=10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 8, f"● 範疇二 (電力與設施)：{scope2_em:.2f} kg CO2e (場域類型: {venue_mode})", ln=True)
        pdf.cell(0, 8, f"● 範疇三 (與會者交通)：{scope3_travel:.2f} kg CO2e (基於平均 {tra_km}km 通勤)", ln=True)
        pdf.cell(0, 8, f"● 範疇三 (植栽上游物流)：{scope3_logistics:.2f} kg CO2e (基於貨運 {log_km}km 里程)", ln=True)
        
        pdf.set_font(f_name, size=13)
        pdf.set_text_color(0, 0, 0)
        pdf.set_draw_color(180, 50, 50)
        pdf.cell(0, 12, f"➤ 總預估排放負債 (Total Carbon Debt)：{grand_total:.2f} kg CO2e", border="B", ln=True)
        pdf.ln(10)

        # 3. 補償與抵銷方案
        pdf.set_font(f_name, size=14)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(0, 10, "第二部分：綠色抵銷方案 (Offset Strategy)", ln=True)
        
        pdf.set_font(f_name, size=11)
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(232, 245, 233)
        pdf.multi_cell(0, 10, 
            f"  選用植栽：{plant['name']}\\n"
            f"  抵銷路徑：透過植物光合作用之固碳能力進行實質吸收。\\n"
            f"  建議數量：{count} 盆\\n"
            f"  中和結果：本方案已涵蓋物流排碳，實現【淨減碳效益】。", fill=True)
        pdf.ln(5)

        # 4. 科學原理說明
        pdf.set_font(f_name, size=9)
        pdf.set_text_color(120, 120, 120)
        pdf.multi_cell(0, 6, 
            "【科學依據與聲明】\\n"
            "1. 本報告依據 GHG Protocol 溫室氣體核算體系標準進行試算。\\n"
            "2. 交通與電力係數參考環境部(MOENV)最新公告之係數值。\\n"
            "3. 植物固碳係數係基於一年期之平均生物量增量進行估算。\\n"
            "4. 物流計算包含 3.5 噸貨車之移動排放，旨在消除抵銷行動本身之排碳風險。")

        # 頁尾簽署
        pdf.set_y(-30)
        pdf.set_font(f_name, size=10)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(0, 10, "蕨積 | 永續活動顧問服務領航者", align='R', ln=True)

        return send_file(io.BytesIO(pdf.output()), as_attachment=True, download_name="ESG_Carbon_Report.pdf")
    except Exception as e:
        return f"錯誤：{str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

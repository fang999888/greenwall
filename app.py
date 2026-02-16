import os
import io
from flask import Flask, request, render_template_string, send_file
from fpdf import FPDF
import datetime

app = Flask(__name__)

# --- 係數配置 ---
VENUE_FACTORS = {"indoor": 0.5, "outdoor": 0.2}
FREIGHT_FACTOR = 0.35  # 3.5噸貨車 (kg/km)
TRAVEL_FACTOR = 0.035  # 預設捷運係數 (kg/人/km)

PLANT_DETAILS = {
    "succulent": {"name": "多肉植物", "sink": 0.1, "desc": "多肉植物固碳率。"},
    "potted": {"name": "觀葉盆栽", "sink": 0.5, "desc": "室內淨化空氣植物數據。"},
    "seedling": {"name": "原生樹苗", "sink": 2.0, "desc": "造林樹種固碳量表。"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蕨積 | 真實碳足跡試算</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f4f7f4; padding: 20px; color: #1b4332; line-height: 1.6; }
        .card { max-width: 550px; margin: auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #2d6a4f; }
        .section { background: #fff3f3; padding: 20px; border-radius: 10px; border-left: 5px solid #c0392b; margin-top: 20px; }
        .section.green { background: #f0fff0; border-left-color: #27ae60; }
        h3 { margin-top: 0; color: #333; font-size: 1.1em; }
        .input-group { margin-top: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; font-size: 0.9em; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #2d6a4f; color: white; border: none; border-radius: 10px; font-size: 18px; cursor: pointer; margin-top: 30px; font-weight: bold; }
        .warning { color: #c0392b; font-size: 0.85em; margin-top: 10px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>蕨積 - 永續提案系統</h2>
        <form action="/download" method="post">
            <div class="input-group">
                <label>專案名稱</label>
                <input type="text" name="event_name" placeholder="例如：2026 永續論壇" required>
            </div>

            <div class="section">
                <h3>第一階段：計算原始碳負債</h3>
                <div class="input-group">
                    <label>場域與人數</label>
                    <div style="display:flex; gap:10px;">
                        <select name="venue_mode">
                            <option value="indoor">室內 (空調)</option>
                            <option value="outdoor">室外 (自然通風)</option>
                        </select>
                        <input type="number" name="guests" value="100" placeholder="出席人數">
                    </div>
                </div>
                <div class="input-group">
                    <label>與會人員出席總里程 (km)</label>
                    <input type="number" name="tra_km" value="10">
                    <p style="font-size:0.8em; color:#666;">* 所有來賓前往會場的平均交通排碳</p>
                </div>
            </div>

            <div class="section green">
                <h3>第二階段：綠色抵銷方案 (含物流排碳)</h3>
                <div class="input-group">
                    <label>選擇抵銷植物</label>
                    <select name="p_type">
                        <option value="succulent">精緻多肉 (0.1kg/年)</option>
                        <option value="potted" selected>觀葉盆栽 (0.5kg/年)</option>
                        <option value="seedling">原生樹苗 (2.0kg/年)</option>
                    </select>
                </div>
                <div class="input-group">
                    <label>植物送貨里程 (km)</label>
                    <input type="number" name="log_km" value="50">
                    <div class="warning">⚠️ 注意：送貨過程亦會產生碳排，系統將自動加計。</div>
                </div>
            </div>

            <button type="submit">產出「淨減碳」提案報告</button>
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

        # 1. 原始負債：活動(3hr) + 人員交通
        act_em = guests * 3 * VENUE_FACTORS[venue_mode]
        peo_em = guests * tra_km * TRAVEL_FACTOR * 2
        original_debt = act_em + peo_em

        # 2. 抵銷產生的新負債：植物運送
        delivery_em = log_km * FREIGHT_FACTOR * 2 # 來回計算
        
        # 3. 總計需要被抵銷的量
        grand_total = original_debt + delivery_em
        
        plant = PLANT_DETAILS[p_type]
        count = int(grand_total / plant['sink']) + 1

        # PDF 生成
        pdf = FPDF()
        pdf.add_page()
        font_path = os.path.join(os.getcwd(), 'font.ttf')
        f_name = 'Chinese' if os.path.exists(font_path) else 'Arial'
        if os.path.exists(font_path): pdf.add_font(f_name, '', font_path)

        # 上半部：告知碳債
        pdf.set_font(f_name, size=18)
        pdf.set_text_color(180, 0, 0)
        pdf.cell(0, 15, "活動原始碳負債報告", ln=True, align='C')
        pdf.set_font(f_name, size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"專案：{name}", ln=True)
        pdf.cell(0, 10, f"原始碳債：{original_debt:.2f} kg CO2e (含人員交通與場域)", ln=True)
        pdf.ln(5)

        # 中間：揭露運送排碳
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, f"加上「植物物流運送」產生之排碳：+ {delivery_em:.2f} kg CO2e", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(f_name, size=13)
        pdf.cell(0, 10, f"最終應抵銷總量：{grand_total:.2f} kg CO2e", ln=True)
        pdf.ln(10)

        # 下半部：綠色解決方案
        pdf.set_font(f_name, size=16)
        pdf.set_text_color(45, 106, 79)
        pdf.cell(0, 12, "【蕨積】淨減碳補救方案", ln=True, fill=False)
        pdf.set_font(f_name, size=12)
        pdf.set_fill_color(232, 245, 233)
        pdf.multi_cell(0, 10, f" 建議採用 {count} 盆【{plant['name']}】\\n 此數量已完整覆蓋活動、交通及『物流本身』的碳排放。", fill=True)

        pdf.set_y(-30)
        pdf.set_font(f_name, size=9)
        pdf.cell(0, 10, "追求真實的淨零，而不僅僅是數字的遊戲。 - 蕨積", align='C', ln=True)

        return send_file(io.BytesIO(pdf.output()), as_attachment=True, download_name="True_Green_Proposal.pdf")
    except Exception as e:
        return f"錯誤：{str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

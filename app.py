import os
import io
from flask import Flask, request, render_template_string, send_file
from fpdf import FPDF
import datetime

app = Flask(__name__)

# --- 專業數據字典 ---
PLANT_DETAILS = {
    "succulent": {"name": "多肉植物 (2-3吋盆)", "sink": 0.1, "desc": "依據多肉植物平均年生長率估算。"},
    "potted": {"name": "觀葉盆栽 (5吋盆)", "sink": 0.5, "desc": "依據環境部公告之室內淨化空氣植物固碳數據。"},
    "seedling": {"name": "原生樹苗 (30-50cm)", "sink": 2.0, "desc": "依據農業部林業署常用造林樹種固碳量表。"}
}

# --- 前端介面 ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蕨積 | 綠色活動提案系統</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f0f4f0; padding: 20px; color: #1b4332; }
        .card { max-width: 500px; margin: auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #2d6a4f; margin-bottom: 25px; }
        .input-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; font-size: 0.9em; }
        input, select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; box-sizing: border-box; }
        .desc-box { background: #f9f9f9; padding: 12px; border-radius: 8px; font-size: 0.85em; color: #666; margin-top: 8px; border: 1px solid #eee; line-height: 1.4; }
        .result { margin-top: 20px; padding: 15px; background: #e8f5e9; border-radius: 10px; border-left: 5px solid #2d6a4f; }
        button { width: 100%; padding: 15px; background: #2d6a4f; color: white; border: none; border-radius: 10px; font-size: 18px; cursor: pointer; margin-top: 20px; font-weight: bold; }
        button:hover { background: #1b4332; }
    </style>
</head>
<body>
    <div class="card">
        <h2>蕨積 - 綠色提案系統</h2>
        <form action="/download" method="post">
            <div class="input-group">
                <label>活動/專案名稱</label>
                <input type="text" name="event_name" placeholder="例如：2026 企業家庭日" required>
            </div>
            <div class="input-group">
                <label>參與人數</label>
                <input type="number" name="guests" id="guests" value="100" oninput="updateUI()">
            </div>
            <div class="input-group">
                <label>活動時數 (小時)</label>
                <input type="number" name="hours" id="hours" value="3" oninput="updateUI()">
            </div>
            <div class="input-group">
                <label>贈送植物類型</label>
                <select name="p_type" id="p_type" onchange="updateUI()">
                    <option value="succulent">精緻多肉 (0.1kg CO2e/年)</option>
                    <option value="potted" selected>觀葉盆栽 (0.5kg CO2e/年)</option>
                    <option value="seedling">原生樹苗 (2.0kg CO2e/年)</option>
                </select>
                <div id="p_desc" class="desc-box"></div>
            </div>
            
            <div class="result">
                預計排碳：<strong id="em">150</strong> kg CO2e<br>
                建議抵銷數量：<strong id="cnt">300</strong> 盆
            </div>
            <button type="submit">下載 PDF 專業提案書</button>
        </form>
    </div>

    <script>
        const specs = {
            succulent: "規格：2-3吋盆。數據：參考沙漠植物平均固碳率。",
            potted: "規格：5吋盆觀葉植物。數據：參考環境部室內空氣淨化資料。",
            seedling: "規格：30-50cm 樹苗。數據：對標林業署造林固碳量表。"
        };
        function updateUI() {
            let g = document.getElementById('guests').value || 0;
            let h = document.getElementById('hours').value || 0;
            let t = document.getElementById('p_type').value;
            let factor = {succulent: 0.1, potted: 0.5, seedling: 2.0}[t];
            
            let em = (g * h * 0.5).toFixed(1);
            let cnt = Math.ceil(em / factor);
            
            document.getElementById('em').innerText = em;
            document.getElementById('cnt').innerText = cnt;
            document.getElementById('p_desc').innerText = specs[t];
        }
        window.onload = updateUI;
    </script>
</body>
</html>
"""

# --- 後端路由 ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    try:
        # 取得表單數據
        name = request.form.get('event_name', '未命名活動')
        guests = int(request.form.get('guests', 0))
        hours = int(request.form.get('hours', 0))
        p_type = request.form.get('p_type')
        
        plant = PLANT_DETAILS[p_type]
        emission = guests * hours * 0.5
        count = int(emission / plant['sink']) + 1

        # 初始化 PDF
        pdf = FPDF()
        pdf.add_page()
        
        # 載入字體 (請確保 font.ttf 存在於根目錄)
        font_path = os.path.join(os.getcwd(), 'font.ttf')
        if os.path.exists(font_path):
            pdf.add_font('Chinese', '', font_path)
            main_font = 'Chinese'
        else:
            main_font = 'Arial'

        # PDF 內容設計
        pdf.set_font(main_font, size=20)
        pdf.set_text_color(45, 106, 79) # 蕨積綠
        pdf.cell(0, 20, "綠色活動碳中和提案報告", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font(main_font, size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"專案名稱：{name}", ln=True)
        pdf.cell(0, 10, f"報告日期：{datetime.date.today()}", ln=True)
        pdf.ln(5)

        # 數據區
        pdf.set_fill_color(232, 245, 233)
        pdf.cell(0, 10, " [ 碳足跡試算結果 ]", ln=True, fill=True)
        pdf.cell(0, 10, f" 1. 預估活動總排放量：{emission} kg CO2e", ln=True)
        pdf.cell(0, 10, f" 2. 建議贈送植物數量：{count} 盆", ln=True)
        pdf.cell(0, 10, f" 3. 選用植物規格：{plant['name']}", ln=True)
        pdf.ln(10)

        # 顧問說明區
        pdf.set_font(main_font, size=10)
        pdf.set_text_color(85, 85, 85)
        pdf.multi_cell(0, 7, f"【數據來源與公信力說明】\n{plant['desc']}\n活動排放係數參考自環境部《活動碳足跡資訊揭露指引》。\n\n本報告由「蕨積 - 綠色排放顧問系統」產出，旨在協助企業落實 ESG 永續行動，將活動碳排透過綠色植栽進行補償預估。")

        # 頁尾
        pdf.set_y(-30)
        pdf.set_font(main_font, size=8)
        pdf.cell(0, 10, "蕨積 | 植生牆景觀與碳中和專家", align='C', ln=True)

        # 輸出 PDF
        pdf_bytes = pdf.output()
        return send_file(
            io.BytesIO(pdf_bytes),
            as_attachment=True,
            download_name=f"{name}_Proposal.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return f"系統錯誤：{str(e)}", 500

if __name__ == '__main__':
    # 針對 Render 部署建議關閉 debug
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

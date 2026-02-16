import os
import io  # io 是獨立 import 的
from flask import Flask, request, render_template, render_template_string, send_file
import datetime
from fpdf import FPDF
app = Flask(__name__)

# 模擬官方係數 (未來可連動資料庫)
FACTORS = {
    "electric": float(os.getenv('TW_ELEC_FACTOR', 0.495)), # 經濟部能源署
    "activity": 0.5, # 環境部活動指引：人均小時排碳
    "plants": {
        "succulent": 0.1,  # 多肉
        "potted": 0.5,     # 室內盆栽
        "seedling": 2.0    # 樹苗 (林業署數據估算)
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>蕨積 | 綠色活動提案系統</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f0f4f0; padding: 20px; color: #2d3436; }
        .card { max-width: 500px; margin: auto; background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #2d6a4f; text-align: center; }
        .input-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #2d6a4f; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .result { margin-top: 20px; padding: 15px; background: #e8f5e9; border-left: 5px solid #2d6a4f; display: none; }
    </style>
</head>
<body>
    <div class="card">
        <h2>蕨積 - 活動碳中和試算</h2>
        <div class="input-group">
            <label>活動參與人數</label>
            <input type="number" id="guests" value="100">
        </div>
        <div class="input-group">
            <label>活動時數 (小時)</label>
            <input type="number" id="hours" value="3">
        </div>
        <div class="input-group">
            <label>贈送植物類型</label>
            <select id="p_type">
                <option value="succulent">精緻多肉 (0.1kg/年)</option>
                <option value="potted">觀葉盆栽 (0.5kg/年)</option>
                <option value="seedling">原生樹苗 (2.0kg/年)</option>
            </select>
        </div>
        <button onclick="calculate()">生成提案數據</button>

        <div id="result" class="result">
            <p>活動預估排碳：<strong id="em"></strong> kg</p>
            <p>建議贈送量：<strong id="cnt"></strong> 盆</p>
            <p style="font-size: 0.8em; color: #666;">*數據引用：環境部活動碳足跡指引 & 林業署固碳量表</p>
        </div>
    </div>

    <script>
        function calculate() {
            let g = document.getElementById('guests').value;
            let h = document.getElementById('hours').value;
            let t = document.getElementById('p_type').value;
            let factor = {succulent: 0.1, potted: 0.5, seedling: 2.0}[t];
            
            let em = g * h * 0.5;
            let cnt = Math.ceil(em / factor);
            
            document.getElementById('em').innerText = em;
            document.getElementById('cnt').innerText = cnt;
            document.getElementById('result').style.display = 'block';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True)

import os
from flask import Flask, request, render_template_string
import datetime

app = Flask(__name__)

# --- 科學係數配置 ---
VENUE_FACTORS = {"indoor": 0.5, "outdoor": 0.2}
FREIGHT_FACTOR = 0.35  # 3.5噸貨車
TRAVEL_FACTOR = 0.035  # 複合交通係數

PLANT_DETAILS = {
    "succulent": {"name": "多肉植物", "sink": 0.1, "desc": "CAM代謝植物，生長緩慢但耐旱抗壓。"},
    "potted": {"name": "觀葉盆栽", "sink": 0.5, "desc": "C3植物，具高葉面積比，淨化空氣效能優異。"},
    "seedling": {"name": "原生樹苗", "sink": 2.0, "desc": "木本植物，具備長期生物量儲存潛力。"}
}

# --- 整合版網頁範本 ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蕨積 | ESG 永續碳中和試算</title>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #f0f2f0; padding: 20px; color: #1b4332; line-height: 1.6; }
        .container { max-width: 650px; margin: auto; }
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); margin-bottom: 20px; }
        h2 { border-bottom: 2px solid #2d6a4f; padding-bottom: 10px; color: #2d6a4f; margin-top: 0; }
        .input-group { margin-top: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; font-size: 0.9em; }
        input, select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #2d6a4f; color: white; border: none; border-radius: 8px; font-size: 18px; cursor: pointer; font-weight: bold; transition: 0.3s; margin-top: 20px; }
        
        /* 結果區樣式 */
        .result-area { border-top: 5px solid #2d6a4f; animation: fadeIn 0.5s ease-in; }
        .debt-box { background: #fff5f5; border-radius: 10px; padding: 20px; margin-top: 15px; border: 1px solid #feb2b2; }
        .offset-box { background: #f0fff4; border-radius: 10px; padding: 20px; margin-top: 15px; border: 1px solid #9ae6b4; }
        .data-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.95em; }
        .total-em { font-size: 1.3em; color: #c53030; font-weight: bold; }
        .total-plant { font-size: 1.3em; color: #2d6a4f; font-weight: bold; }
        .scientific-note { font-size: 0.8em; color: #666; background: #f9f9f9; padding: 15px; border-radius: 8px; margin-top: 20px; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 綠色活動試算顧問</h2>
            <form method="POST">
                <div class="input-group">
                    <label>活動名稱</label>
                    <input type="text" name="event_name" value="{{ data.event_name or '' }}" required>
                </div>
                <div class="row" style="display:flex; gap:10px; margin-top:15px;">
                    <div style="flex:1">
                        <label>場域類型</label>
                        <select name="venue_mode">
                            <option value="indoor" {% if data.venue_mode == 'indoor' %}selected{% endif %}>室內 (空調電力)</option>
                            <option value="outdoor" {% if data.venue_mode == 'outdoor' %}selected{% endif %}>室外 (自然通風)</option>
                        </select>
                    </div>
                    <div style="flex:1">
                        <label>參與人數</label>
                        <input type="number" name="guests" value="{{ data.guests or 100 }}">
                    </div>
                </div>
                <div class="row" style="display:flex; gap:10px; margin-top:15px;">
                    <div style="flex:1">
                        <label>人員交通里程 (km)</label>
                        <input type="number" name="tra_km" value="{{ data.tra_km or 10 }}">
                    </div>
                    <div style="flex:1">
                        <label>植栽送貨里程 (km)</label>
                        <input type="number" name="log_km" value="{{ data.log_km or 50 }}">
                    </div>
                </div>
                <div class="input-group">
                    <label>選用抵銷植栽</label>
                    <select name="p_type">
                        <option value="succulent" {% if data.p_type == 'succulent' %}selected{% endif %}>精緻多肉植物</option>
                        <option value="potted" {% if data.p_type == 'potted' or not data.p_type %}selected{% endif %}>景觀觀葉盆栽</option>
                        <option value="seedling" {% if data.p_type == 'seedling' %}selected{% endif %}>原生造林樹苗</option>
                    </select>
                </div>
                <button type="submit">立即執行碳中和分析</button>
            </form>
        </div>

        {% if result %}
        <div class="card result-area">
            <h2>分析結果：{{ result.event_name }}</h2>
            
            <div class="debt-box">
                <h3>1. 原始碳負債分析</h3>
                <div class="data-row"><span>範疇二 (電力與設施)</span> <span>{{ result.scope2 }} kg</span></div>
                <div class="data-row"><span>範疇三 (來賓交通)</span> <span>{{ result.scope3_t }} kg</span></div>
                <div class="data-row"><span>範疇三 (物流運輸)</span> <span>{{ result.scope3_l }} kg</span></div>
                <hr style="border:0; border-top:1px solid #feb2b2">
                <div class="data-row"><strong>預估排放總量 (A + B + C)</strong> <span class="total-em">{{ result.total }} kg CO2e</span></div>
            </div>

            

            <div class="offset-box">
                <h3>2. 蕨積綠色補救方案</h3>
                <p>選用 <strong>{{ result.p_name }}</strong> 透過光合作用進行實質吸收。</p>
                <div class="data-row"><strong>建議抵銷數量</strong> <span class="total-plant">{{ result.count }} 盆</span></div>
                <p style="font-size:0.9em; color:#276749;">✅ 此數量已完整覆蓋活動、交通及物流本身之排碳，實現【淨減碳效益】。</p>
            </div>

            

            <div class="scientific-note">
                <strong>【科學依據與聲明】</strong><br>
                1. 依據 <strong>GHG Protocol</strong> 溫室氣體核算體系標準試算。<br>
                2. 交通與電力係數參考環境部(MOENV)最新公告之係數值。<br>
                3. 植物固碳係數係基於一年期之平均生物量增量進行估算。<br>
                4. 本報告已將「抵銷行動」產生的二次物流碳排納入計算，確保結果真實性。
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    data = {}
    result = None
    if request.method == 'POST':
        # 讀取數據
        event_name = request.form.get('event_name')
        guests = int(request.form.get('guests', 0))
        venue_mode = request.form.get('venue_mode')
        tra_km = float(request.form.get('tra_km', 0))
        log_km = float(request.form.get('log_km', 0))
        p_type = request.form.get('p_type')

        data = request.form # 為了讓頁面記住填寫的內容

        # 計算邏輯
        s2 = round(guests * 3 * VENUE_FACTORS[venue_mode], 2)
        s3_t = round(guests * tra_km * TRAVEL_FACTOR * 2, 2)
        s3_l = round(log_km * FREIGHT_FACTOR * 2, 2)
        total = round(s2 + s3_t + s3_l, 2)
        
        plant = PLANT_DETAILS[p_type]
        count = int(total / plant['sink']) + 1

        result = {
            "event_name": event_name,
            "scope2": s2,
            "scope3_t": s3_t,
            "scope3_l": s3_l,
            "total": total,
            "p_name": plant['name'],
            "count": count
        }

    return render_template_string(HTML_TEMPLATE, data=data, result=result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

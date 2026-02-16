import os
from flask import Flask, request, render_template_string
import datetime

app = Flask(__name__)

# --- 科學數據設定 ---
FACTORS = {
    "venue": {"indoor": 0.5, "outdoor": 0.2},
    "transport": 0.035, # 人員交通 (kg/人/km)
    "logistics": 0.35,  # 植物物流 (kg/km)
}

PLANTS = {
    "succulent": {"name": "多肉植物", "sink": 0.1, "type": "小型禮品"},
    "potted": {"name": "觀葉盆栽", "sink": 0.5, "type": "空間佈置"},
    "seedling": {"name": "原生樹苗", "sink": 2.0, "type": "高效固碳"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蕨積 | 永續碳中和顧問系統</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f8faf8; padding: 20px; color: #1b4332; }
        .container { max-width: 700px; margin: auto; }
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 25px; }
        .step-title { background: #2d6a4f; color: white; padding: 10px 15px; border-radius: 8px; font-size: 1.1em; margin: 20px 0; }
        .result-box { padding: 20px; border-radius: 12px; margin-top: 15px; border: 1px solid #ddd; }
        .debt-red { background: #fff5f5; border-color: #feb2b2; }
        .offset-green { background: #f0fff4; border-color: #9ae6b4; }
        .highlight { font-size: 1.4em; font-weight: bold; color: #c53030; }
        .green-highlight { font-size: 1.4em; font-weight: bold; color: #2d6a4f; }
        label { display: block; margin-top: 12px; font-weight: bold; font-size: 0.9em; }
        input, select { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 6px; }
        button { width: 100%; padding: 18px; background: #2d6a4f; color: white; border: none; border-radius: 8px; font-size: 1.1em; cursor: pointer; margin-top: 20px; }
        .consult-text { font-size: 0.9em; color: #4a5568; line-height: 1.8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 綠色活動永續顧問單</h2>
            <form method="POST">
                <div class="step-title">STEP 1. 估算活動碳負債</div>
                <div style="display:flex; gap:10px;">
                    <div style="flex:1">
                        <label>場域類型</label>
                        <select name="venue_mode">
                            <option value="indoor">室內 (空調電力)</option>
                            <option value="outdoor">室外 (自然通風)</option>
                        </select>
                    </div>
                    <div style="flex:1">
                        <label>參與人數</label>
                        <input type="number" name="guests" value="100">
                    </div>
                </div>
                <label>人員出席平均單程里程 (km)</label>
                <input type="number" name="tra_km" value="10">

                <div class="step-title">STEP 2. 選擇抵銷植物與物流</div>
                <div style="display:flex; gap:10px;">
                    <div style="flex:1">
                        <label>選擇植物</label>
                        <select name="p_type">
                            {% for k, v in plants.items() %}
                            <option value="{{ k }}">{{ v.name }} ({{ v.sink }}kg/年)</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div style="flex:1">
                        <label>送貨里程 (km)</label>
                        <input type="number" name="log_km" value="50">
                    </div>
                </div>

                <div class="step-title">STEP 3. 設定抵銷策略</div>
                <label>計畫抵銷年限 (建議 3-5 年)</label>
                <select name="years">
                    <option value="1">1 年 (急迫中和)</option>
                    <option value="3" selected>3 年 (標準永續)</option>
                    <option value="5">5 年 (長期認養)</option>
                </select>

                <button type="submit">產出專業碳中和評估報告</button>
            </form>
        </div>

        {% if res %}
        <div class="card">
            <h2>碳中和分析報告書</h2>
            
            <div class="result-box debt-red">
                <h3 style="margin-top:0; color:#c53030;">1. 活動原始碳負債</h3>
                <p class="consult-text">依據 GHG Protocol 核算，本次活動（場域及人員交通）預估產生：</p>
                <span class="highlight">{{ res.debt }} kg CO2e</span>
                <p class="consult-text" style="font-size:0.8em;">*包含場域電力排放及範疇三人員通勤排放。</p>
            </div>

            <div class="result-box">
                <h3 style="margin-top:0;">2. 淨效益評估 (Net Benefit)</h3>
                <p class="consult-text">為抵銷上述碳債，運送植物本身將產生 <strong style="color:#c53030;">{{ res.delivery_em }} kg</strong> 排放。<br>
                因此，本次行動必須抵銷總量為：</p>
                <span class="green-highlight">{{ res.grand_total }} kg CO2e</span>
            </div>

            

            <div class="result-box offset-green">
                <h3 style="margin-top:0; color:#2d6a4f;">3. 蕨積永續抵銷策略</h3>
                <p class="consult-text">考慮到植物生長規律與活動合理性，建議方案如下：</p>
                <ul class="consult-text">
                    <li><strong>選用植栽：</strong> {{ res.p_name }}</li>
                    <li><strong>抵銷計畫：</strong> 分 {{ res.years }} 年持續固碳</li>
                    <li><strong>建議採購數量：</strong> <span class="green-highlight">{{ res.count }} 盆</span></li>
                </ul>
                <hr>
                <p class="consult-text" style="background:#fff; padding:10px; border-radius:5px;">
                    <strong>💡 顧問建議：</strong><br>
                    如果您希望進一步降低採購數量，建議組合 <strong>{{ res.seedling_mix }} 盆原生樹苗</strong> 搭配 
                    <strong>{{ res.succulent_mix }} 盆多肉植物</strong>。樹苗具備長期碳匯價值，能更有效分擔活動碳債。
                </p>
            </div>

            <div class="consult-text" style="font-size:0.8em; margin-top:20px; border-top:1px solid #eee; padding-top:10px;">
                <strong>【科學依據】</strong> 植物碳中和是跨年度的生命週期承諾。我們計算的是植物在設定年限內，
                扣除物流排碳後的「淨固碳量」。建議將此報告納入企業 ESG 範疇三揭露資料。
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    res = None
    if request.method == 'POST':
        # 讀取
        venue_mode = request.form.get('venue_mode')
        guests = int(request.form.get('guests', 0))
        tra_km = float(request.form.get('tra_km', 0))
        log_km = float(request.form.get('log_km', 0))
        p_type = request.form.get('p_type')
        years = int(request.form.get('years', 3))

        # 計算
        debt = round((guests * 3 * FACTORS["venue"][venue_mode]) + (guests * tra_km * FACTORS["transport"] * 2), 2)
        delivery_em = round(log_km * FACTORS["logistics"] * 2, 2)
        grand_total = debt + delivery_em
        
        plant = PLANTS[p_type]
        # 計算公式： 總量 / (單盆年固碳 * 年限)
        count = int(grand_total / (plant['sink'] * years)) + 1
        
        # 組合建議試算 (假設 1/3 碳債由樹苗負擔)
        seedling_mix = int((grand_total * 0.4) / (PLANTS['seedling']['sink'] * years)) + 1
        succulent_mix = int((grand_total * 0.6) / (PLANTS['succulent']['sink'] * years)) + 1

        res = {
            "debt": debt,
            "delivery_em": delivery_em,
            "grand_total": grand_total,
            "p_name": plant['name'],
            "years": years,
            "count": count,
            "seedling_mix": seedling_mix,
            "succulent_mix": succulent_mix
        }

    return render_template_string(HTML_TEMPLATE, plants=PLANTS, res=res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

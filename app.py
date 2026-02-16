import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- 專業係數 ---
FACTORS = {
    "venue": {"indoor": 0.5, "outdoor": 0.2},
    "transport": 0.035, # 人員交通
    "logistics": 0.35   # 貨車物流
}

PLANTS = {
    "none": {"name": "--- 暫不選擇 (僅計算原始碳債) ---", "sink": 0},
    "succulent": {"name": "多肉植物 (0.1kg/年)", "sink": 0.1},
    "potted": {"name": "觀葉盆栽 (0.5kg/年)", "sink": 0.5},
    "seedling": {"name": "原生樹苗 (2.0kg/年)", "sink": 2.0}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蕨積 | 碳中和顧問系統</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f4f6f4; padding: 20px; color: #1b4332; }
        .container { max-width: 650px; margin: auto; }
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .step-tag { background: #2d6a4f; color: white; padding: 5px 12px; border-radius: 4px; font-size: 0.9em; }
        .debt-display { background: #fff5f5; color: #c53030; padding: 20px; border-radius: 10px; border: 1px solid #feb2b2; text-align: center; }
        .debt-val { font-size: 2.5em; font-weight: bold; display: block; }
        .offset-display { background: #f0fff4; color: #2d6a4f; padding: 20px; border-radius: 10px; border: 1px solid #9ae6b4; margin-top: 20px; }
        label { font-weight: bold; font-size: 0.9em; display: block; margin-top: 15px; }
        input, select { width: 100%; padding: 12px; margin-top: 5px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #2d6a4f; color: white; border: none; border-radius: 8px; font-size: 1.1em; cursor: pointer; margin-top: 25px; font-weight: bold; }
        .info-text { font-size: 0.85em; color: #666; margin-top: 10px; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 綠色活動試算顧問</h2>
            <form method="POST">
                <span class="step-tag">1. 活動規模</span>
                <div style="display:flex; gap:10px;">
                    <div style="flex:1"><label>場域</label><select name="venue_mode">
                        <option value="indoor">室內 (空調)</option><option value="outdoor">室外 (自然通風)</option>
                    </select></div>
                    <div style="flex:1"><label>出席人數</label><input type="number" name="guests" value="100"></div>
                </div>
                <label>人員交通平均單程里程 (km)</label>
                <input type="number" name="tra_km" value="10">

                <span class="step-tag" style="margin-top:25px; display:inline-block;">2. 抵銷方案</span>
                <label>選擇植物 (選「不選擇」可看原始碳債)</label>
                <select name="p_type">
                    {% for k, v in plants.items() %}
                    <option value="{{ k }}">{{ v.name }}</option>
                    {% endfor %}
                </select>
                <label>植物送貨里程 (km)</label>
                <input type="number" name="log_km" value="50">
                
                <label>規劃抵銷年限</label>
                <select name="years">
                    <option value="1">1 年 (快速中和)</option>
                    <option value="3" selected>3 年 (永續計畫)</option>
                    <option value="5">5 年 (長期認養)</option>
                </select>

                <button type="submit">執行數據分析</button>
            </form>
        </div>

        {% if res %}
        <div class="card">
            <h3>活動排碳分析報告</h3>
            <div class="debt-display">
                <span>預估活動原始碳負債</span>
                <span class="debt-val">{{ res.debt }} <small>kg CO2e</small></span>
                <p style="margin: 5px 0 0; font-size: 0.9em;">這是活動本身、用電及人員交通產生的環境成本。</p>
            </div>

            {% if res.p_type != 'none' %}
            <div class="offset-display">
                <h4 style="margin-top:0;">🌱 蕨積淨減碳方案</h4>
                <p>為抵銷上述碳債，並加計送貨物流排碳 ({{ res.log_em }} kg)，<br>
                   在 <strong>{{ res.years }} 年</strong> 的持續固碳計畫下：</p>
                <p style="font-size: 1.2em;">建議採購數量：<strong>{{ res.count }} 盆</strong> {{ res.p_name }}</p>
                <div class="info-text">
                    * 透過長期的植物生長，將活動碳債轉化為綠色資產。<br>
                    * 組合建議：{{ res.s_mix }} 盆樹苗 + {{ res.succ_mix }} 盆多肉，可達更高固碳效益。
                </div>
            </div>
            {% else %}
            <div style="margin-top:20px; text-align:center; color:#666; font-style:italic;">
                ( 尚未選擇抵銷方案，請於上方選單選取植物種類以查看補救建議 )
            </div>
            {% endif %}
            
            <div class="info-text" style="border-top:1px solid #eee; padding-top:15px; margin-top:20px;">
                <strong>科學依據：</strong> 碳中和並非一蹴可幾。蕨積倡導將一次性的排碳，透過長年期的植物生命進行「實質吸收」。本試算扣除物流排碳，確保數據不漂綠。
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
        v_mode = request.form.get('venue_mode')
        guests = int(request.form.get('guests', 0))
        tra_km = float(request.form.get('tra_km', 0))
        log_km = float(request.form.get('log_km', 0))
        p_type = request.form.get('p_type')
        years = int(request.form.get('years', 3))

        # 1. 原始負債 (活動 + 人員)
        debt = round((guests * 3 * FACTORS["venue"][v_mode]) + (guests * tra_km * FACTORS["transport"] * 2), 2)
        
        # 2. 只有在選了植物時才計算物流與抵銷
        if p_type != 'none':
            log_em = round(log_km * FACTORS["logistics"] * 2, 2)
            grand_total = debt + log_em
            plant = PLANTS[p_type]
            count = int(grand_total / (plant['sink'] * years)) + 1
            s_mix = int((grand_total * 0.4) / (2.0 * years)) + 1
            succ_mix = int((grand_total * 0.6) / (0.1 * years)) + 1
            
            res = {
                "debt": debt, "log_em": log_em, "p_type": p_type,
                "p_name": plant['name'], "years": years, "count": count,
                "s_mix": s_mix, "succ_mix": succ_mix
            }
        else:
            res = {"debt": debt, "p_type": 'none'}

    return render_template_string(HTML_TEMPLATE, plants=PLANTS, res=res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

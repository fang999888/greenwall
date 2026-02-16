import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- 專業科學係數設定 ---
COEFFICIENTS = {
    "venue": {"low": 0.2, "standard": 0.5, "high": 0.8},
    "transport": {"mass": 0.035, "mixed": 0.12, "car": 0.173},
    "logistics": 0.35
}

PLANTS = {
    "none": {"name": "--- 暫不選擇 ---", "sink": 0},
    "succulent": {"name": "多肉植物 (0.1kg/年)", "sink": 0.1},
    "potted": {"name": "觀葉盆栽 (0.5kg/年)", "sink": 0.5},
    "seedling": {"name": "原生樹苗 (2.0kg/年)", "sink": 2.0}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>蕨積 | 永續活動碳顧問系統</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #f4f7f4; padding: 15px; color: #1b4332; line-height: 1.6; margin: 0; }
        .container { max-width: 720px; margin: auto; }
        .card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-bottom: 20px; }
        h2 { color: #2d6a4f; border-left: 5px solid #2d6a4f; padding-left: 15px; font-size: 1.4em; }
        .step-label { background: #2d6a4f; color: white; padding: 4px 12px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
        label { display: block; margin-top: 15px; font-weight: bold; font-size: 0.85em; }
        select, input { width: 100%; padding: 14px; margin-top: 6px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; background-color: white; -webkit-appearance: none; }
        .flex-row { display: flex; gap: 15px; }
        @media (max-width: 600px) { .flex-row { flex-direction: column; gap: 0; } }
        .debt-box { background: #fff5f5; color: #c53030; padding: 20px; border-radius: 12px; border: 1px solid #feb2b2; text-align: center; }
        .debt-val { font-size: 2.8em; font-weight: 900; display: block; line-height: 1.2; }
        .offset-box { background: #f0fff4; color: #2d6a4f; padding: 20px; border-radius: 12px; border: 1px solid #9ae6b4; margin-top: 20px; }
        
        /* 專業補充區塊 */
        .pro-section { background: #f8f9fa; padding: 20px; border-radius: 12px; font-size: 0.85em; color: #444; margin-top: 30px; border-left: 5px solid #2d6a4f; }
        .pro-section h3 { color: #1b4332; margin-top: 0; font-size: 1.1em; border-bottom: 1px solid #ddd; padding-bottom: 8px; }
        .warning { color: #c53030; font-weight: bold; }
        button { width: 100%; padding: 18px; background: #2d6a4f; color: white; border: none; border-radius: 10px; font-size: 1.1em; cursor: pointer; margin-top: 25px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 專業碳足跡試算系統</h2>
            <form method="POST">
                <span class="step-label">1. 場域與規模</span>
                <select name="v_level">
                    <option value="low">低耗能 (綠建築 / 自然通風)</option>
                    <option value="standard" selected>標準耗能 (一般商辦空調)</option>
                    <option value="high">高耗能 (具大型燈光電力)</option>
                </select>
                <div class="flex-row">
                    <div style="flex:1"><label>人數</label><input type="number" name="guests" value="100"></div>
                    <div style="flex:1"><label>時數 (hr)</label><input type="number" name="hours" value="3"></div>
                </div>

                <span class="step-label" style="margin-top:20px; display:inline-block;">2. 交通模型</span>
                <select name="t_mode">
                    <option value="mass">大眾運輸</option><option value="mixed" selected>混合運輸</option><option value="car">自駕為主</option>
                </select>
                <label>平均單程里程 (km)</label><input type="number" name="tra_km" value="15">

                <span class="step-label" style="margin-top:20px; display:inline-block;">3. 植物與物流里程</span>
                <select name="p_type">
                    {% for k, v in plants.items() %}
                    <option value="{{ k }}">{{ v.name }}</option>
                    {% endfor %}
                </select>
                <div class="flex-row">
                    <div style="flex:1"><label>抵銷年限</label><select name="years"><option value="3" selected>3 年</option><option value="5">5 年</option></select></div>
                    <div style="flex:1"><label>物流里程(km)</label><input type="number" name="log_km" value="50"></div>
                </div>
                <button type="submit">產出科學分析報告</button>
            </form>
        </div>

        {% if res %}
        <div class="card">
            <div class="debt-box"><span class="debt-val">{{ res.debt }} <small style="font-size:0.4em;">kg</small></span>原始碳負債</div>
            {% if res.p_type != 'none' %}
            <div class="offset-box">
                <p>物流排碳：<strong>{{ res.log_em }} kg</strong> (來回里程: {{ res.l_km*2 }} km)</p>
                <p>建議採購：<strong style="font-size:1.3em;">{{ res.count }} 盆</strong> {{ res.p_name }}</p>
                <p style="font-size:0.85em; opacity:0.8;">💡 建議組合：{{ res.s_mix }} 盆原生樹苗 + {{ res.succ_mix }} 盆多肉植物。</p>
            </div>
            {% endif %}
        </div>
        {% endif %}

        

[Image of the greenhouse gas protocol scope 1 2 and 3]


        <div class="pro-section">
            <h3>⚠️ 估算侷限性與專業聲明</h3>
            <ul>
                <li class="warning">本試算未計入餐飲、物料印刷、廢棄物處理及住宿，實際排放量可能更高。</li>
                <li>「標準耗能」為統計均值，實際數據須依場域電表為準。</li>
            </ul>
        </div>

        <div class="pro-section">
            <h3>📈 正式盤查指引 (符合 ISO 標準)</h3>
            <p>若需對外宣告，應依 <strong>ISO 14067</strong> 執行正式盤查：</p>
            <ul>
                <li><strong>數據收集：</strong> 索取場地電費單、發放交通問卷及統計物料重量。</li>
                <li><strong>係數選用：</strong> 優先採用環境部(MOENV)最新係數或 Ecoinvent 資料庫。</li>
                <li><strong>系統邊界：</strong> 應明確定義報告範圍、關鍵假設與數據品質評估。</li>
            </ul>
            <p style="background:#eef; padding:10px; border-radius:5px; border-left:3px solid #1b4332;">
                「蕨積」提供符合國際標準的<b>活動碳中和計畫書</b>，歡迎聯繫我們進行深度盤查。
            </p>
        </div>
        <div style="height:40px;"></div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    res = None
    if request.method == 'POST':
        v_l, gs, hrs = request.form.get('v_level'), int(request.form.get('guests', 0)), int(request.form.get('hours', 3))
        t_m, t_km = request.form.get('t_mode'), float(request.form.get('tra_km', 0))
        p_t, yrs, l_km = request.form.get('p_type'), int(request.form.get('years', 3)), float(request.form.get('log_km', 50))
        debt = round((gs * hrs * COEFFICIENTS["venue"][v_l]) + (gs * t_km * COEFFICIENTS["transport"][t_m] * 2), 2)
        if p_t != 'none':
            log_em = round(l_km * COEFFICIENTS["logistics"] * 2, 2)
            total = debt + log_em
            count = int(total / (PLANTS[p_t]['sink'] * yrs)) + 1
            s_mix, succ_mix = int((total*0.4)/(2.0*yrs))+1, int((total*0.6)/(0.1*yrs))+1
            res = {"debt": debt, "log_em": log_em, "l_km": l_km, "p_name": PLANTS[p_t]['name'], "years": yrs, "count": count, "s_mix": s_mix, "succ_mix": succ_mix, "p_type": p_t}
        else: res = {"debt": debt, "p_type": 'none'}
    return render_template_string(HTML_TEMPLATE, plants=PLANTS, res=res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

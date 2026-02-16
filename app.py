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
    "none": {"name": "--- 暫不選擇 ---", "sink": 0, "desc": "純計算原始排放。"},
    "succulent": {"name": "多肉植物 (0.1kg/年)", "sink": 0.1, "desc": "適合桌上型贈禮。"},
    "potted": {"name": "觀葉盆栽 (0.5kg/年)", "sink": 0.5, "desc": "室內美化首選。"},
    "seedling": {"name": "原生樹苗 (2.0kg/年)", "sink": 2.0, "desc": "最具永續價值。"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蕨積 | 專業 ESG 永續活動試算</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f4f7f4; padding: 15px; color: #1b4332; line-height: 1.5; margin: 0; }
        .container { max-width: 600px; margin: auto; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; }
        h2 { color: #2d6a4f; font-size: 1.4em; border-left: 4px solid #2d6a4f; padding-left: 10px; margin: 10px 0; }
        .step-label { background: #2d6a4f; color: white; padding: 3px 10px; border-radius: 4px; font-size: 0.8em; font-weight: bold; display: inline-block; margin-bottom: 5px; }
        label { display: block; margin-top: 12px; font-weight: bold; font-size: 0.9em; }
        select, input { width: 100%; padding: 12px; margin-top: 5px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; box-sizing: border-box; }
        
        /* 手機版自動切換單欄 */
        .flex-row { display: flex; gap: 10px; }
        @media (max-width: 480px) { .flex-row { flex-direction: column; gap: 0; } }

        .debt-box { background: #fff5f5; color: #c53030; padding: 20px; border-radius: 10px; text-align: center; }
        .debt-val { font-size: 2.2em; font-weight: 900; display: block; }
        .offset-box { background: #f0fff4; color: #2d6a4f; padding: 20px; border-radius: 10px; border: 1px solid #9ae6b4; margin-top: 15px; }
        .transparency-box { background: #f8f9fa; padding: 15px; border-radius: 10px; font-size: 0.8em; color: #666; margin-top: 25px; border-left: 4px solid #adb5bd; }
        button { width: 100%; padding: 15px; background: #2d6a4f; color: white; border: none; border-radius: 8px; font-size: 1.1em; cursor: pointer; margin-top: 20px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 碳足跡試算</h2>
            <form method="POST">
                <span class="step-label">1. 場域能效</span>
                <select name="v_level">
                    <option value="low">低耗能 (綠建築/自然通風)</option>
                    <option value="standard" selected>標準耗能 (一般中央空調)</option>
                    <option value="high">高耗能 (大型舞台/機具)</option>
                </select>
                
                <div class="flex-row">
                    <div style="flex:1">
                        <label>參與人數</label>
                        <input type="number" name="guests" value="100">
                    </div>
                    <div style="flex:1">
                        <label>活動時數 (hr)</label>
                        <input type="number" name="hours" value="3">
                    </div>
                </div>

                <span class="step-label" style="margin-top:20px;">2. 交通與里程</span>
                <select name="t_mode">
                    <option value="mass">大眾運輸為主</option>
                    <option value="mixed" selected>混合運輸</option>
                    <option value="car">自駕為主</option>
                </select>
                <label>平均單程里程 (km)</label>
                <input type="number" name="tra_km" value="15">

                <span class="step-label" style="margin-top:20px;">3. 補救方案</span>
                <select name="p_type">
                    {% for k, v in plants.items() %}
                    <option value="{{ k }}">{{ v.name }}</option>
                    {% endfor %}
                </select>
                <label>抵銷年限</label>
                <select name="years">
                    <option value="1">1 年 (快速補救)</option>
                    <option value="3" selected>3 年 (標準永續)</option>
                    <option value="5">5 年 (長期計畫)</option>
                </select>

                <button type="submit">開始計算分析</button>
            </form>
        </div>

        {% if res %}
        <div class="card">
            <div class="debt-box">
                <span style="font-weight:bold;">活動原始碳負債</span>
                <span class="debt-val">{{ res.debt }} <small style="font-size:0.4em;">kg CO2e</small></span>
            </div>

            {% if res.p_type != 'none' %}
            <div class="offset-box">
                <h4 style="margin:0 0 10px 0; border-bottom:1px solid #9ae6b4;">🌱 淨減碳建議</h4>
                <p style="font-size:0.95em;">為達成 <strong>{{ res.years }} 年</strong> 實質中和：</p>
                <p>建議採購：<strong style="font-size:1.2em;">{{ res.count }} 盆</strong> {{ res.p_name }}</p>
                <p style="font-size:0.85em; background:rgba(255,255,255,0.5); padding:10px; border-radius:5px;">
                    💡 組合推薦：{{ res.s_mix }} 盆樹苗 + {{ res.succ_mix }} 盆多肉。
                </p>
            </div>
            {% endif %}
        </div>
        {% endif %}

        <div class="transparency-box">
            <strong>📊 科學依據：</strong><br>
            1. 電力：$0.495\text{ kg CO2e/度}$<br>
            2. 交通：環境部(MOENV)公告係數<br>
            3. 植物：林業署生物量增量均值
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
        v_l = request.form.get('v_level')
        gs = int(request.form.get('guests', 0))
        hrs = int(request.form.get('hours', 3))
        t_m = request.form.get('t_mode')
        t_km = float(request.form.get('tra_km', 0))
        p_t = request.form.get('p_type')
        yrs = int(request.form.get('years', 3))

        debt = round((gs * hrs * COEFFICIENTS["venue"][v_l]) + (gs * t_km * COEFFICIENTS["transport"][t_m] * 2), 2)
        
        if p_t != 'none':
            log_em = round(100 * COEFFICIENTS["logistics"], 2)
            total_target = debt + log_em
            count = int(total_target / (PLANTS[p_t]['sink'] * yrs)) + 1
            s_mix = int((total_target * 0.4) / (2.0 * yrs)) + 1
            succ_mix = int((total_target * 0.6) / (0.1 * yrs)) + 1
            res = {"debt": debt, "p_type": p_t, "p_name": PLANTS[p_t]['name'], "years": yrs, "count": count, "s_mix": s_mix, "succ_mix": succ_mix}
        else:
            res = {"debt": debt, "p_type": 'none'}

    return render_template_string(HTML_TEMPLATE, plants=PLANTS, res=res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

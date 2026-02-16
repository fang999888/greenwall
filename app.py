import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- 專業科學係數設定 (絕對保留) ---
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
    <title>蕨積 | 永續活動碳中和顧問系統</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #f4f7f4; padding: 15px; color: #1b4332; line-height: 1.6; margin: 0; }
        .container { max-width: 720px; margin: auto; }
        .card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin-bottom: 20px; }
        h2 { color: #2d6a4f; border-left: 5px solid #2d6a4f; padding-left: 15px; font-size: 1.3em; margin-top: 0; }
        .step-label { background: #2d6a4f; color: white; padding: 4px 12px; border-radius: 4px; font-size: 0.85em; font-weight: bold; display: inline-block; }
        label { display: block; margin-top: 15px; font-weight: bold; font-size: 0.9em; }
        input, select { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; background-color: white; -webkit-appearance: none; }
        .flex-row { display: flex; gap: 15px; }
        @media (max-width: 600px) { .flex-row { flex-direction: column; gap: 0; } }
        button { width: 100%; padding: 18px; background: #2d6a4f; color: white; border: none; border-radius: 10px; font-size: 1.1em; cursor: pointer; margin-top: 25px; font-weight: bold; }
        
        /* 結果呈現 */
        .res-box { text-align: center; padding: 20px; border-radius: 12px; margin-top: 10px; }
        .debt-style { background: #fff5f5; color: #c53030; border: 1px solid #feb2b2; }
        .gain-style { background: #f0fff4; color: #2d6a4f; border: 1px solid #9ae6b4; margin-top: 15px; }
        .val { font-size: 2.5em; font-weight: 900; display: block; }

        /* 專業內容區塊 */
        .pro-section { background: #f8f9fa; padding: 20px; border-radius: 12px; font-size: 0.85em; color: #444; border-left: 5px solid #adb5bd; margin-top: 25px; }
        .pro-section h3 { color: #1b4332; margin-top: 0; font-size: 1.1em; border-bottom: 1px solid #ddd; padding-bottom: 8px; }
        .letter-box { background: #fff; border: 1px dashed #2d6a4f; padding: 25px; margin-top: 30px; border-radius: 12px; }
        .warning { color: #c53030; font-weight: bold; }
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
                    <option value="high">高耗能 (具大型機具電力)</option>
                </select>
                <div class="flex-row">
                    <div style="flex:1"><label>人數</label><input type="number" name="guests" value="100"></div>
                    <div style="flex:1"><label>時數 (hr)</label><input type="number" name="hours" value="3"></div>
                </div>

                <span class="step-label" style="margin-top:20px;">2. 交通與物流</span>
                <select name="t_mode">
                    <option value="mass">大眾運輸</option>
                    <option value="mixed" selected>混合運輸</option>
                    <option value="car">自駕為主</option>
                </select>
                <div class="flex-row">
                    <div style="flex:1"><label>單程里程(km)</label><input type="number" name="tra_km" value="15"></div>
                    <div style="flex:1"><label>植物運送(km)</label><input type="number" name="log_km" value="50"></div>
                </div>

                <span class="step-label" style="margin-top:20px;">3. 抵銷計畫</span>
                <select name="p_type">
                    {% for k, v in plants.items() %}
                    <option value="{{ k }}">{{ v.name }}</option>
                    {% endfor %}
                </select>
                <label>抵銷年限</label>
                <select name="years"><option value="3" selected>3 年</option><option value="5">5 年</option></select>

                <button type="submit">執行科學分析報告</button>
            </form>
        </div>

        {% if res %}
        <div class="card">
            <div class="res-box debt-style"><span class="val">{{ res.debt }} kg</span>活動原始碳負債</div>
            {% if res.p_type != 'none' %}
            <div class="res-box gain-style">
                <h4 style="margin:0;">🌱 淨中和建議：<strong>{{ res.count }} 盆</strong> {{ res.p_name }}</h4>
                <p style="font-size:0.85em; margin:5px 0;">(含物流排碳 {{ res.log_em }} kg)</p>
                <p style="font-size:0.85em; color:#666;">策略建議：{{ res.s_mix }} 盆樹苗 + {{ res.succ_mix }} 盆多肉</p>
            </div>
            {% endif %}
        </div>
        {% endif %}

        

[Image of the greenhouse gas protocol scope 1 2 and 3]


        <div class="pro-section">
            <h3>📊 數據透明度與係數說明</h3>
            1. <b>電力排放：</b> 參考能源署 $0.495\text{ kg CO2e/度}$，依場域等級動態計算。<br>
            2. <b>交通係數：</b> 參考環境部公告，大眾運輸 $0.035\text{ kg/km}$，小客車 $0.173\text{ kg/km}$。<br>
            3. <b>植物固碳：</b> 參考林業署常用樹種固碳量表均值計算。
        </div>

        <div class="pro-section">
            <h3>⚠️ 此估算的嚴重局限性</h3>
            <ul>
                <li class="warning">未計入餐飲（尤其肉類）、印刷品、住宿與廢棄物處理。</li>
                <li>「標準耗能」不等於實際耗能，實際應以電費單為準。</li>
            </ul>
        </div>

        <div class="pro-section">
            <h3>📈 正式 ISO 盤查指引</h3>
            依 <b>ISO 14067</b> 標準，建議對參與者進行<b>交通問卷調查</b>，並統計物料材質與重量，以獲得具公信力之數據品質。
        </div>

        <div class="letter-box">
            <h3 style="color: #2d6a4f; margin-top:0; font-size:1.1em;">致企業專案負責人：</h3>
            <div style="font-size: 0.9em; color: #333;">
                <p>在推動 ESG 時，係數的準確性決定了報告的公信力。「蕨積」提供可經科學檢驗的抵銷計畫，透過物流里程的誠實揭露，協助您將碳債轉化為品牌資產。若需要正式盤查服務，歡迎聯繫顧問團隊。</p>
                <p style="text-align: right; font-weight: bold; color: #2d6a4f;">蕨積 顧問團隊 敬啟</p>
            </div>
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
            res = {"debt": debt, "log_em": log_em, "p_name": PLANTS[p_t]['name'], "years": yrs, "count": count, "s_mix": s_mix, "succ_mix": succ_mix, "p_type": p_t}
        else: res = {"debt": debt, "p_type": 'none'}
    return render_template_string(HTML_TEMPLATE, plants=PLANTS, res=res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

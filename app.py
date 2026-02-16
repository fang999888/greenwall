import os
from Flask import Flask, request, render_template_string

app = Flask(__name__)

# --- 專業科學係數設定 ---
COEFFICIENTS = {
    "venue": {"low": 0.2, "standard": 0.5, "high": 0.8},
    "transport": {"mass": 0.035, "mixed": 0.12, "car": 0.173},
    "logistics": 0.35,
    "survival_rate": 0.8  # 預估植物存活率 (80%)，用以保守計算所需盆數
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
        h2 { color: #2d6a4f; border-left: 5px solid #2d6a4f; padding-left: 15px; font-size: 1.3em; margin-top: 0; margin-bottom: 8px; }
        .disclaimer { font-size: 0.8em; color: #666; background: #eee; padding: 10px; border-radius: 8px; margin-bottom: 20px; line-height: 1.4; }
        .step-label { background: #2d6a4f; color: white; padding: 4px 12px; border-radius: 4px; font-size: 0.85em; font-weight: bold; display: inline-block; }
        label { display: block; margin-top: 15px; font-weight: bold; font-size: 0.9em; }
        input, select { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; background-color: white; -webkit-appearance: none; }
        .flex-row { display: flex; gap: 15px; }
        @media (max-width: 600px) { .flex-row { flex-direction: column; gap: 0; } }
        button { width: 100%; padding: 18px; background: #2d6a4f; color: white; border: none; border-radius: 10px; font-size: 1.1em; cursor: pointer; margin-top: 25px; font-weight: bold; }
        .res-box { text-align: center; padding: 20px; border-radius: 12px; margin-top: 10px; }
        .debt-style { background: #fff5f5; color: #c53030; border: 1px solid #feb2b2; }
        .gain-style { background: #f0fff4; color: #2d6a4f; border: 1px solid #9ae6b4; margin-top: 15px; }
        .val { font-size: 2.5em; font-weight: 900; display: block; }
        .pro-section { background: #f8f9fa; padding: 20px; border-radius: 12px; font-size: 0.85em; color: #444; border-left: 5px solid #adb5bd; margin-top: 25px; }
        .letter-box { background: #fff; border: 1px dashed #2d6a4f; padding: 25px; margin-top: 30px; border-radius: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 專業碳足跡試算系統</h2>
            <div class="disclaimer">
                本網頁提供活動碳排放初步估計，僅供了解碳排放與綠色植物之碳中和概念。正式報告需經由第三方認證或詳細現場盤查。
            </div>
            
            <form method="POST">
                <span class="step-label">1. 活動與規模</span>
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
                <div class="flex-row">
                    <div style="flex:1"><label>平均單程里程(km)</label><input type="number" name="tra_km" value="15"></div>
                    <div style="flex:1"><label>植物運送里程(km)</label><input type="number" name="log_km" value="50"></div>
                </div>

                <span class="step-label" style="margin-top:20px;">3. 抵銷計畫參數</span>
                <select name="p_type">
                    {% for k, v in plants.items() %}
                    <option value="{{ k }}">{{ v.name }}</option>
                    {% endfor %}
                </select>
                <div class="flex-row">
                    <div style="flex:1"><label>抵銷年限</label>
                        <select name="years">
                            <option value="1">1 年 (快速中和)</option>
                            <option value="3" selected>3 年 (標準永續)</option>
                            <option value="5">5 年 (長期計畫)</option>
                        </select>
                    </div>
                    <div style="flex:1"><label>預估植物存活率</label><input type="text" value="80%" disabled style="background:#f9f9f9;"></div>
                </div>

                <button type="submit">產出科學分析報告</button>
            </form>
        </div>

        {% if res %}
        <div class="card">
            <div class="res-box debt-style"><span class="val">{{ res.debt }} kg</span>活動原始碳負債</div>
            {% if res.p_type != 'none' %}
            <div class="res-box gain-style">
                <h4 style="margin:0;">🌱 建議中和方案</h4>
                <p>建議採購：<strong style="font-size:1.4em;">{{ res.count }} 盆</strong> {{ res.p_name }}</p>
                <p style="font-size:0.85em; opacity:0.8;">(已考量物流排碳與 {{ res.surv_rate }}% 存活風險係數)</p>
            </div>
            {% endif %}
        </div>
        {% endif %}

        <div class="pro-section">
            <h3>📊 數據透明度與係數說明</h3>
            1. <b>電力排放：</b> 參考能源署 $0.495\text{ kg CO2e/度}$ 之電力係數。<br>
            2. <b>交通與物流：</b> 參考環境部公告，並計入來回運輸里程。<br>
            3. <b>存活修正：</b> 計算已自動增加盆數，以補償預期中 20% 之自然淘汰率。
        </div>

        <div class="pro-section">
            <h3>⚠️ 此估算的嚴重局限性</h3>
            <ul>
                <li>未計入餐飲、物料印刷、住宿與廢棄物處理。</li>
                <li>交通與場地數據為統計均值，非實際盤查數據。</li>
                <li>依 ISO 14067 標準，建議對參與者進行交通問卷調查，並統計物料材質與重量，以獲得具公信力之數據品質。</li>
            </ul>
        </div>

        <div class="letter-box">
            <h3 style="color: #2d6a4f; margin-top:0;">致企業專案負責人：</h3>
            <div style="font-size: 0.9em; color: #333;">
                <p>「蕨積」協助您將活動排碳誠實轉化為永續行動。考量到生物成長的不確定性，我們在計算中加入了<b>存活率風險係數</b>，這能讓您的碳中和計畫更具防禦力與真實感。若需 ISO 級別盤查，請聯繫我們。</p>
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
        t_km, l_km = float(request.form.get('tra_km', 0)), float(request.form.get('log_km', 50))
        p_t, yrs = request.form.get('p_type'), int(request.form.get('years', 3))
        
        # 碳負債計算
        debt = round((gs * hrs * COEFFICIENTS["venue"][v_level]) + (gs * t_km * 0.12 * 2), 2)
        
        if p_t != 'none':
            log_em = round(l_km * COEFFICIENTS["logistics"] * 2, 2)
            total = debt + log_em
            # 引入存活率計算：總需求 / (單株固碳 * 年限 * 存活率)
            survival_rate = COEFFICIENTS["survival_rate"]
            count = int(total / (PLANTS[p_t]['sink'] * yrs * survival_rate)) + 1
            res = {"debt": debt, "log_em": log_em, "p_name": PLANTS[p_t]['name'], "years": yrs, "count": count, "surv_rate": int(survival_rate*100), "p_type": p_t}
        else: res = {"debt": debt, "p_type": 'none'}
    return render_template_string(HTML_TEMPLATE, plants=PLANTS, res=res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

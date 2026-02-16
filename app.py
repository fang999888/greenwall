import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- 專業科學係數設定 (嚴格保留) ---
COEFFICIENTS = {
    "venue": {
        "low": 0.2,       # 綠建築標章 / 自然通風空間
        "standard": 0.5,  # 一般商務大樓
        "high": 0.8       # 具備大型機具 / 舞台燈光電力
    },
    "transport": {
        "mass": 0.035,    # 大眾運輸複合權重
        "mixed": 0.12,     # 混合通勤
        "car": 0.173       # 燃油小客車
    },
    "logistics": 0.35      # 3.5噸柴油貨車每公里排碳 (kg CO2e)
}

PLANTS = {
    "none": {"name": "--- 暫不選擇 (僅產生活動碳負債) ---", "sink": 0, "desc": "純計算原始排放。"},
    "succulent": {"name": "多肉植物 (0.1kg/年)", "sink": 0.1, "desc": "適合桌上型贈禮。"},
    "potted": {"name": "觀葉盆栽 (0.5kg/年)", "sink": 0.5, "desc": "室內美化首選。"},
    "seedling": {"name": "原生樹苗 (2.0kg/年)", "sink": 2.0, "desc": "最具永續價值。"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>蕨積 | 專業 ESG 永續活動試算系統</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f4f7f4; padding: 15px; color: #1b4332; line-height: 1.6; margin: 0; }
        .container { max-width: 720px; margin: auto; }
        .card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-bottom: 20px; }
        h2 { color: #2d6a4f; margin-top: 0; border-left: 5px solid #2d6a4f; padding-left: 15px; font-size: 1.4em; }
        .step-label { background: #2d6a4f; color: white; padding: 4px 12px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
        label { display: block; margin-top: 15px; font-weight: bold; font-size: 0.85em; }
        select, input { width: 100%; padding: 14px; margin-top: 6px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 16px; background-color: white; -webkit-appearance: none; }
        .flex-row { display: flex; gap: 15px; }
        @media (max-width: 600px) {
            .flex-row { flex-direction: column; gap: 0; }
            .card { padding: 20px; }
            h2 { font-size: 1.2em; }
        }
        .debt-box { background: #fff5f5; color: #c53030; padding: 20px; border-radius: 12px; border: 1px solid #feb2b2; text-align: center; }
        .debt-val { font-size: 2.8em; font-weight: 900; display: block; line-height: 1.2; }
        .offset-box { background: #f0fff4; color: #2d6a4f; padding: 20px; border-radius: 12px; border: 1px solid #9ae6b4; margin-top: 20px; }
        .transparency-box { background: #f8f9fa; padding: 20px; border-radius: 12px; font-size: 0.8em; color: #555; margin-top: 30px; border-left: 5px solid #adb5bd; }
        .letter-box { background: #fff; border: 1px dashed #2d6a4f; padding: 20px; margin-top: 30px; border-radius: 12px; }
        button { width: 100%; padding: 18px; background: #2d6a4f; color: white; border: none; border-radius: 10px; font-size: 1.1em; cursor: pointer; margin-top: 25px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 專業碳足跡試算系統</h2>
            <form method="POST">
                <span class="step-label">1. 場域能效等級</span>
                <select name="v_level">
                    <option value="low">低耗能 (綠建築標章 / 自然通風)</option>
                    <option value="standard" selected>標準耗能 (一般大樓中央空調)</option>
                    <option value="high">高耗能 (具大型機具 / 舞台燈光電力)</option>
                </select>
                <div class="flex-row">
                    <div style="flex:1"><label>活動參與人數</label><input type="number" name="guests" value="100"></div>
                    <div style="flex:1"><label>活動總時數 (hr)</label><input type="number" name="hours" value="3"></div>
                </div>

                <span class="step-label" style="margin-top:20px; display:inline-block;">2. 交通排放模型</span>
                <select name="t_mode">
                    <option value="mass">大眾運輸為主</option><option value="mixed" selected>混合運輸 (一般比例)</option><option value="car">自駕為主</option>
                </select>
                <label>人員出席平均單程里程 (km)</label><input type="number" name="tra_km" value="15">

                <span class="step-label" style="margin-top:20px; display:inline-block;">3. 植物補救與物流</span>
                <label>選擇植物類型</label>
                <select name="p_type">
                    {% for k, v in plants.items() %}
                    <option value="{{ k }}">{{ v.name }}</option>
                    {% endfor %}
                </select>
                <div class="flex-row">
                    <div style="flex:1"><label>抵銷年限</label>
                        <select name="years"><option value="3" selected>3 年</option><option value="5">5 年</option></select>
                    </div>
                    <div style="flex:1"><label>植物運送里程(km)</label><input type="number" name="log_km" value="50"></div>
                </div>

                <button type="submit">產出科學分析結果</button>
            </form>
        </div>

        {% if res %}
        <div class="card">
            <div class="debt-box">
                <span style="font-weight:bold; font-size:0.9em;">活動原始碳負債</span>
                <span class="debt-val">{{ res.debt }} <small style="font-size:0.4em;">kg CO2e</small></span>
            </div>
            {% if res.p_type != 'none' %}
            <div class="offset-box">
                <h4 style="margin:0; border-bottom:1px solid #9ae6b4; padding-bottom:8px; font-size:1em;">🌱 蕨積「淨減碳」方案建議</h4>
                <p style="font-size:0.9em;">動態物流排碳：<strong>{{ res.log_em }} kg</strong> (里程: {{ res.l_km }} km)</p>
                <p style="font-size:1em;">建議採購：<strong style="font-size:1.3em;">{{ res.count }} 盆</strong> {{ res.p_name }}</p>
                <p style="font-size:0.8em; color:#444;">💡 組合建議：{{ res.s_mix }} 盆原生樹苗 + {{ res.succ_mix }} 盆多肉植物。</p>
            </div>
            {% endif %}
        </div>
        {% endif %}

        

        <div class="transparency-box">
            <strong>📊 數據透明度與科學依據 (Transparency Statement)：</strong><br><br>
            1. <strong>電力排放：</strong> 參考經濟部能源署 $0.495\text{ kg CO2e/度}$ 之電力係數。<br>
            2. <strong>交通係數：</strong> 參考環境部(MOENV)最新公告。大眾運輸 $0.035\text{ kg/km}$；燃油小客車 $0.173\text{ kg/km}$。<br>
            3. <strong>植物固碳：</strong> 依據林業署常用樹種固碳量表均值計算。<br>
            4. <strong>物流抵銷：</strong> 依據輸入里程計算 3.5 噸貨車之運輸足跡，確保抵銷行動之嚴謹性。
        </div>

        <div class="letter-box">
            <h3 style="color: #2d6a4f; margin-top:0; font-size:1.1em;">致企業專案負責人：</h3>
            <div style="font-size: 0.9em; color: #333;">
                <p>「蕨積」提供可經科學檢驗的抵銷計畫。透過物流里程的誠實揭露，貴司能更真實地反映碳足跡。若需要認證報告，歡迎聯繫團隊。</p>
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
            log_em = round(l_km * COEFFICIENTS["logistics"] * 2, 2) # 動態里程來回
            total_target = debt + log_em
            count = int(total_target / (PLANTS[p_t]['sink'] * yrs)) + 1
            s_mix = int((total_target * 0.4) / (2.0 * yrs)) + 1
            succ_mix = int((total_target * 0.6) / (0.1 * yrs)) + 1
            res = {"debt": debt, "log_em": log_em, "l_km": l_km, "p_name": PLANTS[p_t]['name'], "years": yrs, "count": count, "s_mix": s_mix, "succ_mix": succ_mix, "p_type": p_t}
        else:
            res = {"debt": debt, "p_type": 'none'}

    return render_template_string(HTML_TEMPLATE, plants=PLANTS, res=res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

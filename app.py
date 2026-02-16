import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- 專業科學係數庫 ---
FACTORS = {
    "venue": {
        "low": 0.2,       # 綠建築/自然通風 (kg/人/hr)
        "standard": 0.5,  # 標準商辦/中央空調
        "high": 0.8       # 高耗能展場/大型舞台燈光
    },
    "transport": 0.035,   # kg/人/km (大眾與混合通勤權重)
    "logistics": 0.35     # kg/km (3.5噸貨車)
}

PLANTS = {
    "none": {"name": "--- 暫不選擇 (僅產生活動碳負債) ---", "sink": 0},
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
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f4f7f4; padding: 15px; color: #1b4332; line-height: 1.6; margin: 0; }
        .container { max-width: 700px; margin: auto; }
        .card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin-bottom: 25px; }
        
        h2 { color: #2d6a4f; border-left: 5px solid #2d6a4f; padding-left: 15px; margin-top: 0; font-size: 1.4em; }
        .step-label { background: #2d6a4f; color: white; padding: 4px 12px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
        
        label { display: block; margin-top: 18px; font-weight: bold; font-size: 0.9em; }
        input, select { width: 100%; padding: 14px; margin-top: 6px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; background-color: white; -webkit-appearance: none; }
        
        .flex-row { display: flex; gap: 15px; }
        @media (max-width: 600px) {
            .flex-row { flex-direction: column; gap: 0; }
            .card { padding: 20px; }
            h2 { font-size: 1.25em; }
        }

        button { width: 100%; padding: 18px; background: #2d6a4f; color: white; border: none; border-radius: 12px; font-size: 1.1em; cursor: pointer; margin-top: 30px; font-weight: bold; }
        
        .debt-box { background: #fff5f5; color: #c53030; padding: 25px; border-radius: 12px; border: 1px solid #feb2b2; text-align: center; }
        .debt-val { font-size: 2.8em; font-weight: 900; display: block; line-height: 1; margin: 10px 0; }
        .offset-box { background: #f0fff4; color: #2d6a4f; padding: 25px; border-radius: 12px; border: 1px solid #9ae6b4; margin-top: 20px; }
        
        .source-box { background: #f8f9fa; padding: 20px; border-radius: 12px; font-size: 0.85em; color: #555; border-left: 4px solid #adb5bd; margin-top: 40px; }
        .letter-box { background: #fdfdfd; border: 1px dashed #2d6a4f; padding: 25px; margin-top: 40px; border-radius: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 綠色活動試算顧問</h2>
            <form method="POST">
                <span class="step-label">1. 場地能效等級</span>
                <select name="v_mode">
                    <option value="low">低耗能 (綠建築標章 / 自然通風)</option>
                    <option value="standard" selected>標準耗能 (一般商辦中央空調)</option>
                    <option value="high">高耗能 (大型展場 / 具舞台燈光)</option>
                </select>
                
                <div class="flex-row">
                    <div style="flex:1;"><label>出席人數</label><input type="number" name="guests" value="100"></div>
                    <div style="flex:1;"><label>單程里程(km)</label><input type="number" name="tra_km" value="15"></div>
                </div>

                <span class="step-label" style="margin-top:25px; display:inline-block;">2. 抵銷計畫方案</span>
                <label>選擇植物類型</label>
                <select name="p_type">
                    {% for k, v in plants.items() %}
                    <option value="{{ k }}">{{ v.name }}</option>
                    {% endfor %}
                </select>
                <label>預計抵銷年限</label>
                <select name="years">
                    <option value="3" selected>3 年計畫</option>
                    <option value="5">5 年計畫</option>
                </select>

                <button type="submit">產出分析報告</button>
            </form>
        </div>

        {% if res %}
        <div class="card">
            <div class="debt-box">
                <span style="font-size:0.9em; font-weight:bold;">活動原始碳負債</span>
                <span class="debt-val">{{ res.debt }} <small style="font-size:0.4em;">kg</small></span>
                <p style="font-size:0.75em; margin:0;">(含場域電力與人員交通)</p>
            </div>
            {% if res.p_type != 'none' %}
            <div class="offset-box">
                <h4 style="margin:0;">🌱 補救建議：</h4>
                <p>為達成中和，建議採購：<strong style="font-size:1.3em;">{{ res.count }} 盆</strong> {{ res.p_name }}</p>
            </div>
            {% endif %}
        </div>
        {% endif %}

        

        <div class="letter-box">
            <h3 style="color: #2d6a4f; margin-top:0;">致企業負責人：</h3>
            <div style="font-size:0.95em;">
                <p>「蕨積」致力於打破「擺放植物即中和」的迷思。「蕨積」不只是提供植物，更是提供一個**可經科學檢驗的抵銷計畫*我們主動揭露真實數據來源，協助您將碳債轉化為品牌長期的綠色資產。</p>
                <p style="text-align: right; font-weight: bold; color: #2d6a4f;">蕨積 顧問團隊 敬啟</p>
            </div>
        </div>

        <div class="source-box">
            <strong>📊 數據透明度與科學依據聲明：</strong><br><br>
            1. <strong>電力排放：</strong> 參考經濟部能源署最新公告 $0.495\text{ kg CO2e/度}$，並依據活動空間空調與照明基礎瓦數進行加權分攤。<br>
            2. <strong>場地係數：</strong> 依據場域等級設定 $0.2 \sim 0.8\text{ kg/人/hr}$，涵蓋 HVAC 空調系統與電子設備耗能。<br>
            3. <strong>交通係數：</strong> 參考環境部(MOENV)最新公告。設定大眾與混合通勤之單人每公里碳排均值為 $0.035\text{ kg/km}$。<br>
            4. <strong>植物固碳：</strong> 參考林業署常用樹種固碳量表，基於一年期之平均生物量增量進行估算。
            5. <strong>物流抵銷：</strong> 已包含生產基地至活動會場之運輸足跡，旨在確保抵銷行動本身不造成環境負擔。<br>

            <em>註：人類活動產生之自然碳排遠低於工業活動與能源轉換。本系統僅說明碳源發生及補救辦法，旨在推廣永續轉型意識。</em>
        </div>
        <div style="height:50px;"></div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    res = None
    if request.method == 'POST':
        v_m = request.form.get('v_mode')
        gs = int(request.form.get('guests', 0))
        t_km = float(request.form.get('tra_km', 0))
        p_t = request.form.get('p_type')
        yrs = int(request.form.get('years', 3))
        
        # 公式：(人數 * 3小時 * 場地係數) + (人數 * 里程 * 交通 * 2來回)
        debt = round((gs * 3 * FACTORS["venue"][v_m]) + (gs * t_km * FACTORS["transport"] * 2), 2)
        
        if p_t != 'none':
            count = int((debt + 35) / (PLANTS[p_t]['sink'] * yrs)) + 1
            res = {"debt": debt, "p_name": PLANTS[p_t]['name'], "years": yrs, "count": count, "p_type": p_t}
        else:
            res = {"debt": debt, "p_type": 'none'}
            
    return render_template_string(HTML_TEMPLATE, plants=PLANTS, res=res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

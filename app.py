import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- 專業碳排與植栽係數 ---
FACTORS = {
    "venue": {"indoor": 0.5, "outdoor": 0.2},
    "transport": 0.035, # kg/人/km
    "logistics": 0.35   # kg/km (3.5噸貨車)
}

PLANTS = {
    "none": {"name": "--- 暫不選擇 (僅產生活動碳負債) ---", "sink": 0, "id": "N"},
    "succulent": {"name": "多肉植物 (0.1kg/年)", "sink": 0.1, "id": "S"},
    "potted": {"name": "觀葉盆栽 (0.5kg/年)", "sink": 0.5, "id": "P"},
    "seedling": {"name": "原生樹苗 (2.0kg/年)", "sink": 2.0, "id": "T"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>蕨積 | 永續活動碳中和顧問系統</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f7f4; padding: 20px; color: #1b4332; line-height: 1.6; }
        .container { max-width: 700px; margin: auto; }
        .card { background: white; padding: 35px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-bottom: 25px; }
        h2 { color: #2d6a4f; border-left: 5px solid #2d6a4f; padding-left: 15px; margin-top: 0; }
        .step-label { background: #2d6a4f; color: white; padding: 4px 12px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
        label { display: block; margin-top: 18px; font-weight: bold; font-size: 0.9em; }
        input, select { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 18px; background: #2d6a4f; color: white; border: none; border-radius: 8px; font-size: 1.1em; cursor: pointer; margin-top: 30px; font-weight: bold; transition: 0.3s; }
        button:hover { background: #1b4332; transform: translateY(-1px); }
        
        /* 結果呈現區 */
        .debt-box { background: #fff5f5; color: #c53030; padding: 25px; border-radius: 12px; border: 1px solid #feb2b2; text-align: center; }
        .debt-val { font-size: 3em; font-weight: 900; display: block; }
        .offset-box { background: #f0fff4; color: #2d6a4f; padding: 25px; border-radius: 12px; border: 1px solid #9ae6b4; margin-top: 20px; }
        
        /* 顧問信件區 */
        .letter-box { background: #fdfdfd; border: 1px dashed #2d6a4f; padding: 30px; margin-top: 50px; border-radius: 12px; }
        .letter-content { font-size: 0.95em; color: #2d3436; }
        .disclaimer { text-align: center; color: #95a5a6; font-size: 0.75em; margin-top: 30px; padding-bottom: 50px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 綠色活動試算顧問</h2>
            <p style="color:#666; font-size:0.9em;">我們不只是提供植物，更致力於推廣對土地的科學責任。</p>
            
            <form method="POST">
                <span class="step-label">STEP 1. 活動碳債核算</span>
                <div style="display:flex; gap:15px;">
                    <div style="flex:1">
                        <label>場域類型</label>
                        <select name="v_mode">
                            <option value="indoor">室內 (空調負載)</option>
                            <option value="outdoor">室外 (自然通風)</option>
                        </select>
                    </div>
                    <div style="flex:1">
                        <label>出席人數</label>
                        <input type="number" name="guests" value="100">
                    </div>
                </div>
                <label>人員交通平均里程 (單程 km)</label>
                <input type="number" name="tra_km" value="10">

                <span class="step-label" style="margin-top:30px; display:inline-block;">STEP 2. 抵銷與物流規劃</span>
                <label>選擇抵銷植物 (選「暫不選擇」可見原始碳債)</label>
                <select name="p_type">
                    {% for k, v in plants.items() %}
                    <option value="{{ k }}">{{ v.name }}</option>
                    {% endfor %}
                </select>
                <label>預計抵銷年限 (植物生長週期)</label>
                <select name="years">
                    <option value="3" selected>3 年 (標準永續計畫)</option>
                    <option value="5">5 年 (長期認養承諾)</option>
                </select>
                <label>植物送貨里程 (基地至會場 km)</label>
                <input type="number" name="log_km" value="50">

                <button type="submit">執行專業數據分析</button>
            </form>
        </div>

        {% if res %}
        <div class="card" id="result">
            <h3 style="text-align:center; color:#2d6a4f;">碳中和試算分析報告</h3>
            <div class="debt-box">
                <span style="font-size:0.9em; font-weight:bold;">活動原始碳負債 (A+B)</span>
                <span class="debt-val">{{ res.debt }} <small style="font-size:0.4em;">kg CO2e</small></span>
                <p style="margin:5px 0 0; font-size:0.85em;">此為場域電力及人員交通衍生之環境負擔</p>
            </div>

            {% if res.p_type != 'none' %}
            <div class="offset-box">
                <h4 style="margin-top:0; border-bottom:1px solid #9ae6b4; padding-bottom:10px;">🌱 蕨積「淨減碳」方案</h4>
                <p>經加計送貨物流排碳 ({{ res.log_em }} kg)，為達成實質中和：</p>
                <p style="font-size:1.1em;">建議在 <strong>{{ res.years }} 年</strong> 計畫中採購：<br>
                   <strong style="font-size:1.4em;">{{ res.count }} 盆</strong> {{ res.p_name }}</p>
                <p style="font-size:0.85em; color:#4a5568;">💡 組合建議：{{ res.s_mix }} 盆樹苗 + {{ res.succ_mix }} 盆多肉，能達更高之固碳與教育效益。</p>
            </div>
            {% else %}
            <p style="text-align:center; color:#95a5a6; font-style:italic; margin-top:20px;">
                ( 尚未選擇抵銷方案，上方選單選取植物後將顯示補救建議 )
            </p>
            {% endif %}
        </div>
        {% endif %}

        

        <div class="letter-box">
            <h3 style="color: #2d6a4f; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-top:0;">
                致企業 ESG 與活動策劃負責人：
            </h3>
            <div class="letter-content">
                <p>在推動綠色轉型的過程中，我們經常面對一個真實的挑戰：<strong>如何證明一場活動是真正的「綠色」？</strong></p>
                <p>「蕨積」的成立，是為了打破傳統「擺放植物即是中和」的行銷迷思。透過這套顧問試算，我們希望與您達成三個共識：</p>
                <ul>
                    <li><strong>真實性 (Authenticity)：</strong> 我們主動揭露為了抵銷而產生的「物流排碳」，確保數據不漂綠。</li>
                    <li><strong>長期價值 (Long-term Impact)：</strong> 植物並非一次性消耗品，它是為期 3-5 年的固碳資產，是企業對土地的長遠承諾。</li>
                    <li><strong>科學定位：</strong> 我們理解人類活動之自然碳排遠低於工業活動，但每一場活動的轉型，都是品牌 ESG 文化的實質表率。</li>
                </ul>
                <p style="background: #f0fff4; padding: 15px; border-radius: 8px; font-style: italic;">
                    「我們不只是在計算碳排，我們在共同定義永續活動的新標準。」
                </p>
                <p>如果您在試算後需要更詳盡的「組合建議」或「認證報告」，歡迎直接聯繫我們，讓我們協助您將碳債轉化為品牌的綠色資產。</p>
                <p style="text-align: right; font-weight: bold; color: #2d6a4f; margin-top:20px;">
                    蕨積 永續活動顧問團隊 敬啟
                </p>
            </div>
        </div>

        <div class="disclaimer">
            <strong>【科學聲明與依據】</strong><br>
            本系統係基於環境部(MOENV)最新係數與 GHG Protocol 規範開發。網頁僅說明碳源發生及生物固碳補救辦法。<br>
            人類活動產生之自然碳排遠低於工業活動，本工具旨在推廣綠色轉型意識。
        </div>
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
        l_km = float(request.form.get('log_km', 0))
        p_t = request.form.get('p_type')
        yrs = int(request.form.get('years', 3))

        # 1. 原始負債
        debt = round((gs * 3 * FACTORS["venue"][v_m]) + (gs * t_km * FACTORS["transport"] * 2), 2)
        
        # 2. 補救分析
        if p_t != 'none':
            log_em = round(l_km * FACTORS["logistics"] * 2, 2)
            total_target = debt + log_em
            count = int(total_target / (PLANTS[p_t]['sink'] * yrs)) + 1
            # 顧問建議組合比例
            s_mix = int((total_target * 0.4) / (2.0 * yrs)) + 1
            succ_mix = int((total_target * 0.6) / (0.1 * yrs)) + 1
            
            res = {
                "debt": debt, "log_em": log_em, "p_type": p_t, 
                "p_name": PLANTS[p_t]['name'], "years": yrs, "count": count,
                "s_mix": s_mix, "succ_mix": succ_mix
            }
        else:
            res = {"debt": debt, "p_type": 'none'}

    return render_template_string(HTML_TEMPLATE, plants=PLANTS, res=res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

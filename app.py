import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- 核心科學係數庫 ---
FACTORS = {
    "event": {
        "venue": {"low": 0.2, "standard": 0.5, "high": 0.8},
        "transport": {"mass": 0.035, "mixed": 0.12, "car": 0.173},
        "logistics": 0.35
    },
    "landscape": {
        "pavement": {"concrete": 25.0, "stone": 12.0, "gravel": 4.5, "wood": -2.0},
        "green_wall_struct": 8.5,
        "gain": {"tree_large": 20.0, "tree_small": 3.5, "shrub": 0.8, "gw_total": 10.0},
        "maint": {"gw": -1.2, "plant": -0.15}
    }
}

PLANTS = {
    "succulent": {"name": "多肉植物 (0.1kg/年)", "sink": 0.1},
    "potted": {"name": "觀葉盆栽 (0.5kg/年)", "sink": 0.5},
    "seedling": {"name": "原生樹苗 (2.0kg/年)", "sink": 2.0}
}

# --- 手機優化 CSS ---
CSS = """
<style>
    /* 基礎樣式與 RWD 設置 */
    * { box-sizing: border-box; }
    body { font-family: -apple-system, sans-serif; background: #f4f7f4; margin: 0; color: #1b4332; line-height: 1.5; }
    
    /* 導覽列：手機端自動適應 */
    .nav { background: #1b4332; padding: 15px; text-align: center; position: sticky; top: 0; z-index: 100; display: flex; justify-content: center; gap: 15px; }
    .nav a { color: white; text-decoration: none; font-weight: bold; font-size: 0.95em; padding: 5px 10px; border-radius: 5px; }
    .nav a:active { background: #2d6a4f; }

    .container { max-width: 800px; margin: 20px auto; padding: 0 15px; }
    .card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin-bottom: 20px; }
    
    h2 { font-size: 1.4em; margin-top: 0; color: #2d6a4f; border-left: 4px solid #2d6a4f; padding-left: 10px; }
    .step-label { background: #2d6a4f; color: white; padding: 3px 10px; border-radius: 4px; font-size: 0.8em; font-weight: bold; display: inline-block; }
    
    label { display: block; margin-top: 15px; font-weight: bold; font-size: 0.85em; }
    input, select { width: 100%; padding: 14px; margin-top: 5px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; /* 防止 iOS 自動放大 */ -webkit-appearance: none; }
    
    /* 手機版自動垂直排列 */
    .flex-row { display: flex; gap: 10px; }
    @media (max-width: 600px) {
        .flex-row { flex-direction: column; gap: 0; }
        .val { font-size: 2em; }
    }

    button { width: 100%; padding: 18px; background: #2d6a4f; color: white; border: none; border-radius: 12px; font-size: 1.1em; cursor: pointer; margin-top: 25px; font-weight: bold; }
    
    /* 結果呈現區 */
    .res-box { padding: 20px; border-radius: 12px; margin-top: 15px; text-align: center; }
    .debt { background: #fff5f5; color: #c53030; border: 1px solid #feb2b2; }
    .gain { background: #f0fff4; color: #2d6a4f; border: 1px solid #9ae6b4; }
    .val { font-size: 2.2em; font-weight: 900; display: block; }
    
    .footer-letter { border-top: 1px solid #eee; margin-top: 30px; padding-top: 20px; font-size: 0.8em; color: #666; }
</style>
"""

@app.route('/', methods=['GET', 'POST'])
def event():
    res = None
    if request.method == 'POST':
        v_l, gs, hrs = request.form.get('v_l'), int(request.form.get('gs',0)), int(request.form.get('hrs',0))
        t_m, t_km = request.form.get('t_m'), float(request.form.get('t_km',0))
        p_t, yrs = request.form.get('p_t'), int(request.form.get('yrs',3))
        debt = round((gs * hrs * FACTORS["event"]["venue"][v_l]) + (gs * t_km * FACTORS["event"]["transport"][t_m] * 2), 2)
        count = int((debt + 35) / (PLANTS[p_t]['sink'] * yrs)) + 1 if p_t in PLANTS else 0
        res = {"debt": debt, "p_name": PLANTS[p_t]['name'] if p_t in PLANTS else "N/A", "count": count, "yrs": yrs}

    return render_template_string(CSS + """
    <div class="nav"><a href="/">活動試算</a><a href="/landscape">園藝景觀</a></div>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 綠色活動顧問</h2>
            <form method="POST">
                <span class="step-label">1. 場域環境</span>
                <select name="v_l"><option value="standard">標準商辦</option><option value="low">綠建築</option><option value="high">高耗能展場</option></select>
                <div class="flex-row">
                    <div style="flex:1;"><label>出席人數</label><input type="number" name="gs" value="100"></div>
                    <div style="flex:1;"><label>時數(hr)</label><input type="number" name="hrs" value="3"></div>
                </div>
                <label>交通模式</label>
                <select name="t_m"><option value="mixed">混合通勤</option><option value="mass">大眾運輸</option><option value="car">自駕為主</option></select>
                <label>平均單程里程 (km)</label><input type="number" name="t_km" value="15">
                <span class="step-label" style="margin-top:20px;">2. 抵銷方案</span>
                <label>選擇植物</label>
                <select name="p_t"><option value="none">不選擇植物</option>{% for k,v in pts.items() %}<option value="{{k}}">{{v.name}}</option>{% endfor %}</select>
                <label>抵銷年限</label>
                <select name="yrs"><option value="3">3 年計</option><option value="5">5 年計</option></select>
                <button type="submit">執行顧問分析</button>
            </form>
        </div>
        {% if res %}<div class="card res-box debt"><span class="val">{{res.debt}} kg</span>活動碳負債</div>
        {% if res.count > 0 %}<div class="card res-box gain">建議採購 <b>{{res.count}} 盆</b><br>{{res.p_name}}</div>{% endif %}{% endif %}
    </div>
    """, pts=PLANTS, res=res)

@app.route('/landscape', methods=['GET', 'POST'])
def landscape():
    res = None
    if request.method == 'POST':
        p_m, p_a = request.form.get('p_m'), float(request.form.get('p_a', 0))
        gw_a = float(request.form.get('gw_a', 0))
        tl, ts, shr = int(request.form.get('tl', 0)), int(request.form.get('ts', 0)), int(request.form.get('shr', 0))
        debt = round((p_a * FACTORS["landscape"]["pavement"][p_m]) + (gw_a * FACTORS["landscape"]["green_wall_struct"]) + 35, 2)
        gain_raw = (tl * 20) + (ts * 3.5) + (shr * 0.8) + (gw_a * 10.0)
        maint = abs((gw_a * FACTORS["landscape"]["maint"]["gw"]) + ((tl+ts+shr) * FACTORS["landscape"]["maint"]["plant"]))
        net_gain = round(gain_raw - maint, 2)
        payback = round(debt / net_gain, 1) if net_gain > 0 else 99
        res = {"debt": debt, "net": net_gain, "pay": payback}

    return render_template_string(CSS + """
    <div class="nav"><a href="/">活動試算</a><a href="/landscape">園藝景觀</a></div>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 園藝景觀顧問</h2>
            <form method="POST">
                <span class="step-label">1. 資材與植生牆</span>
                <label>鋪面資材</label>
                <select name="p_m"><option value="gravel">低碳碎石</option><option value="concrete">混凝土</option><option value="wood">再生木材</option></select>
                <label>鋪面面積 (m²)</label><input type="number" name="p_a" value="20">
                <label>垂直植生牆面積 (m²)</label><input type="number" name="gw_a" value="10">
                <span class="step-label" style="margin-top:20px;">2. 植栽配置</span>
                <div class="flex-row">
                    <div style="flex:1;"><label>大樹(株)</label><input type="number" name="tl" value="0"></div>
                    <div style="flex:1;"><label>樹苗(株)</label><input type="number" name="ts" value="0"></div>
                    <div style="flex:1;"><label>灌木(株)</label><input type="number" name="shr" value="0"></div>
                </div>
                <button type="submit">產出生命週期報告</button>
            </form>
        </div>
        {% if res %}<div class="card res-box debt">工程碳負債 <span class="val">{{res.debt}} kg</span></div>
        <div class="card res-box gain">淨年收益 <span class="val">{{res.net}} kg/年</span>預計 <b>{{res.pay}} 年</b> 回本</div>{% endif %}
    </div>
    """, res=res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- 景觀科學係數 (kg CO2e) ---
# 工程負債 (一次性)
CONSTRUCTION_FACTORS = {
    "pavement": {"concrete": 25.0, "stone": 12.0, "gravel": 4.5, "wood": -2.0},
    "green_wall_struct": 8.5, 
    "logistics": 0.35          
}

# 年度效益與維護成本 (持續性)
# 收益為正，維護為負
ANNUAL_DATA = {
    "tree_large": 20.0,    
    "tree_small": 3.5,     
    "shrub": 0.8,          
    "green_wall_gain": 10.0, # 固碳 2.0 + 隔熱 8.0
    "maintenance_cost": {
        "green_wall": -1.2,  # 每平方米每年(水電、更換苗木)
        "tree_shrub": -0.15  # 每株每年(修剪與有機肥)
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>蕨積 | 永續景觀生命週期試算</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f8fafc; padding: 20px; color: #1e293b; line-height: 1.6; }
        .container { max-width: 750px; margin: auto; }
        .card { background: white; padding: 35px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 25px; }
        .step-label { background: #1b4332; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
        .result-card { background: #f1f5f9; border-radius: 15px; padding: 25px; margin-top: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 20px; }
        .stat-box { background: white; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #e2e8f0; }
        .val { display: block; font-size: 1.8em; font-weight: 800; color: #1b4332; }
        .red-val { color: #e11d48; }
        .letter { border-top: 2px solid #1b4332; margin-top: 40px; padding-top: 20px; font-size: 0.9em; color: #475569; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>蕨積 - 景觀生命週期評估 (LCA)</h2>
            <form method="POST">
                <span class="step-label">1. 資材配置</span>
                <div style="display:flex; gap:10px;">
                    <select name="p_material" style="flex:2;">
                        <option value="concrete">傳統混凝土</option><option value="stone">天然石材</option>
                        <option value="gravel" selected>低碳碎石</option><option value="wood">再生木材</option>
                    </select>
                    <input type="number" name="p_area" value="30" placeholder="鋪面面積(m²)" style="flex:1;">
                </div>

                <label>垂直植生牆面積 (m²)</label>
                <input type="number" name="gw_area" value="15">

                <span class="step-label" style="margin-top:25px; display:inline-block;">2. 植栽數量</span>
                <div class="grid">
                    <input type="number" name="t_l" value="2" placeholder="大喬木">
                    <input type="number" name="t_s" value="5" placeholder="樹苗">
                    <input type="number" name="shr" value="20" placeholder="灌木">
                </div>
                <button type="submit" style="width:100%; padding:15px; background:#1b4332; color:white; border:none; border-radius:8px; margin-top:30px; cursor:pointer; font-weight:bold;">分析完整生命週期碳排</button>
            </form>
        </div>

        {% if res %}
        <div class="card result-card">
            <h3>生命週期數據摘要</h3>
            <div class="grid">
                <div class="stat-box"><span>工程碳排</span><span class="val red-val">{{ res.total_debt }}</span><small>kg (一次性)</small></div>
                <div class="stat-box"><span>年度收益</span><span class="val">{{ res.gross_gain }}</span><small>kg/年</small></div>
                <div class="stat-box"><span>維護支出</span><span class="val red-val">{{ res.maint }}</span><small>kg/年</small></div>
            </div>

            <div style="background:#fff; padding:20px; border-radius:12px; margin-top:20px; border-left:6px solid #1b4332;">
                <p><strong>淨年度收益 (扣除維護)：</strong> <span style="font-size:1.5em; font-weight:bold; color:#1b4332;">{{ res.net_gain }} kg/年</span></p>
                <p>本計畫預計於 <strong>{{ res.payback }} 年</strong> 達成碳中和回收。</p>
            </div>
        </div>
        {% endif %}

        

        <div class="letter">
            <strong>顧問筆記：</strong><br>
            這份報告已細緻化考慮了植生牆的年度維護足跡（含自動灌溉耗能與資材更新）。我們不只談論植物固碳的「表面」，更誠實揭露養護過程的「碳代價」。這正是企業 ESG 報告中所需的最嚴謹真實數據。
            <br><br>
            <strong>蕨積 永續景觀顧問團隊</strong>
        </div>
    </div>
</body>
</html>

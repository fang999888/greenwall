import os
import io
from flask import Flask, request, render_template_string, send_file
from fpdf import FPDF
import datetime

app = Flask(__name__)

# 植物規格詳細定義
PLANT_DETAILS = {
    "succulent": {"name": "Succulent (2-3 inch)", "sink": 0.1, "desc": "Based on average growth rate of desert plants."},
    "potted": {"name": "Indoor Foliage (5 inch)", "sink": 0.5, "desc": "Based on MOE indoor air purification data."},
    "seedling": {"name": "Native Seedling (30-50cm)", "sink": 2.0, "desc": "Based on Forestry Agency sequestration tables."}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>蕨積 | 綠色提案系統</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f0f4f0; padding: 20px; color: #2d3436; line-height: 1.6; }
        .card { max-width: 500px; margin: auto; background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #2d6a4f; text-align: center; }
        .input-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        .desc-box { background: #f9f9f9; padding: 10px; border-radius: 5px; font-size: 0.85em; color: #666; margin-top: 5px; border: 1px solid #eee; }
        button { width: 100%; padding: 12px; background: #2d6a4f; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-top: 10px; }
        .result { margin-top: 20px; padding: 15px; background: #e8f5e9; border-left: 5px solid #2d6a4f; display: none; }
    </style>
</head>
<body>
    <div class="card">
        <h2>蕨積 - 綠色活動提案</h2>
        <form action="/download" method="post">
            <div class="input-group">
                <label>Event Name</label>
                <input type="text" name="event_name" value="Sample Event" required>
            </div>
            <div class="input-group">
                <label>Attendees</label>
                <input type="number" name="guests" id="guests" value="100" oninput="updateUI()">
            </div>
            <div class="input-group">
                <label>Hours</label>
                <input type="number" name="hours" id="hours" value="3" oninput="updateUI()">
            </div>
            <div class="input-group">
                <label>Plant Type</label>
                <select name="p_type" id="p_type" onchange="updateUI()">
                    <option value="succulent">Succulent (0.1kg/yr)</option>
                    <option value="potted" selected>Indoor Potted (0.5kg/yr)</option>
                    <option value="seedling">Native Seedling (2.0kg/yr)</option>
                </select>
                <div id="p_desc" class="desc-box"></div>
            </div>
            
            <div id="result" class="result" style="display:block;">
                <p>Emission: <strong id="em">150</strong> kg CO2e</p>
                <p>Required: <strong id="cnt">300</strong> plants</p>
            </div>
            <button type="submit">Download PDF Report</button>
        </form>
    </div>

    <script>
        const info = {
            succulent: "Spec: 2-inch pot. Data: Average arid plant growth.",
            potted: "Spec: 5-inch foliage. Data: MOE Air Purifying Plants.",
            seedling: "Spec: 30-50cm height. Data: Forestry Agency Sequestration Table."
        };
        function updateUI() {
            let g = document.getElementById('guests').value;
            let h = document.getElementById('hours').value;
            let t = document.getElementById('p_type').value;
            let factor = {succulent: 0.1, potted: 0.5, seedling: 2.0}[t];
            
            let em = g * h * 0.5;
            let cnt = Math.ceil(em / factor);
            
            document.getElementById('em').innerText = em;
            document.getElementById('cnt').innerText = cnt;
            document.getElementById('p_desc').innerText = info[t];
        }
        window.onload = updateUI;
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)
@app.route('/download', methods=['POST'])
def download():
    try:
        name = request.form.get('event_name', 'Unnamed Event')
        guests = int(request.form.get('guests', 0))
        hours = int(request.form.get('hours', 0))
        p_type = request.form.get('p_type')
        
        plant = PLANT_DETAILS[p_type]
        emission = guests * hours * 0.5
        count = int(emission / plant['sink']) + 1

        # 生成 PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Green Event Carbon Offset Proposal", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Event Name: {name}", ln=True)
        pdf.cell(0, 10, f"Estimated Emission: {emission} kg CO2e", ln=True)
        pdf.cell(0, 10, f"Offset Strategy: {count} units of {plant['name']}", ln=True)
        pdf.ln(10)
        
        pdf.set_font("Arial", 'I', 10)
        # 修正：移除多餘的轉義符號，改用簡單字串
        pdf.multi_cell(0, 5, f"Data Source: {plant['desc']}")
        pdf.ln(5)
        pdf.cell(0, 5, "Note: This is a preliminary estimate for CSR reporting.", ln=True)
        
        # 修正：直接使用 bytearray 輸出，避免 io 轉換錯誤
        pdf_bytes = pdf.output() 
        
        return send_file(
            io.BytesIO(pdf_bytes),
            as_attachment=True,
            download_name="proposal.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500


    # 生成 PDF (目前使用英文以避免 Render 字體庫問題)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Green Event Carbon Offset Proposal", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Event: {name}", ln=True)
    pdf.cell(0, 10, f"Estimated Emission: {emission} kg CO2e", ln=True)
    pdf.cell(0, 10, f"Offset Strategy: {count} units of {plant['name']}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 5, f"Data Source: {plant['desc']}\\nNote: This is a preliminary estimate for CSR reporting.")
    
    # 輸出檔案
    output = io.BytesIO()
    pdf_out = pdf.output(dest='S')
    output.write(pdf_out)
    output.seek(0)
    
    return send_file(output, as_attachment=True, download_name="proposal.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)

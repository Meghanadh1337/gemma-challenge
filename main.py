from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from typing import List, Annotated
from fastapi.openapi.utils import get_openapi
from parser import parse_pdfs
from auditor_logic import run_forensic_audit

app = FastAPI(title="Shadow Auditor", description="Forensic Accounting AI Application")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description=app.description,
        routes=app.routes,
    )
    # Fix for Swagger UI rendering issue with multiple files
    # Globally replaces contentMediaType with format: binary in components/schemas
    for schema in openapi_schema.get("components", {}).get("schemas", {}).values():
        properties = schema.get("properties", {})
        for prop in properties.values():
            # Check for single file
            if prop.get("contentMediaType") == "application/octet-stream":
                del prop["contentMediaType"]
                prop["format"] = "binary"
            # Check for list of files
            items = prop.get("items", {})
            if items.get("contentMediaType") == "application/octet-stream":
                del items["contentMediaType"]
                items["format"] = "binary"
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
async def root():
    return {"message": "Welcome to Shadow Auditor API"}

import hashlib

@app.post("/audit")
async def audit_documents(
    files: Annotated[List[UploadFile], File(description="Multiple PDF documents for forensic auditing")],
    industry: str = Form("General")
):
    """
    Upload multiple PDF documents for forensic auditing with hash-based deduplication.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    unique_contents = []
    seen_hashes = set()
    skipped_duplicates = 0

    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
        
        content = await file.read()
        # Calculate SHA-256 fingerprint
        file_hash = hashlib.sha256(content).hexdigest()
        
        if file_hash in seen_hashes:
            skipped_duplicates += 1
            continue
            
        seen_hashes.add(file_hash)
        unique_contents.append(content)

    if not unique_contents:
        raise HTTPException(status_code=400, detail="No unique PDF documents found")

    try:
        # Extract and concatenate text from unique documents only
        full_text = parse_pdfs(unique_contents)
        
        # Run forensic logic with industry context
        audit_report = run_forensic_audit(full_text, industry=industry)
        
        return {
            "file_count": len(unique_contents),
            "skipped_duplicates": skipped_duplicates,
            "total_character_count": len(full_text),
            "industry": industry,
            "report": audit_report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")

from fastapi.responses import HTMLResponse

@app.get("/portal", response_class=HTMLResponse)
async def upload_portal():
    """
    Serves a premium, state-managed forensic portal with LaTeX and Reasoning Trace support.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Shadow Auditor | Elite Forensic Portal</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700&display=swap" rel="stylesheet">
        <!-- MathJax for LaTeX Rendering -->
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <style>
            :root { --primary: #00ff88; --bg: #0a0a0c; --card: #16161d; --text: #f0f0f0; --accent: #00e5ff; }
            body { font-family: 'Outfit', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 2rem; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
            
            .container { width: 100%; max-width: 900px; padding: 2.5rem; background: rgba(22, 22, 29, 0.9); backdrop-filter: blur(15px); border-radius: 32px; border: 1px solid rgba(255,255,255,0.05); }
            h1 { font-size: 3.5rem; font-weight: 700; margin: 0; background: linear-gradient(90deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -3px; }
            
            .drop-zone { border: 2px dashed #444; border-radius: 20px; padding: 4rem; text-align: center; cursor: pointer; transition: 0.3s; background: rgba(255,255,255,0.02); margin-top: 2rem; }
            .drop-zone.dragover { border-color: var(--primary); background: rgba(0,255,136,0.05); }
            
            .file-item { background: #1e1e26; padding: 1rem; border-radius: 12px; margin-top: 1rem; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }
            
            .controls { display: grid; grid-template-columns: 1fr auto; gap: 1rem; margin-top: 2rem; }
            select, .btn-audit { padding: 1.2rem; border-radius: 14px; font-size: 1rem; font-family: inherit; font-weight: 700; border: none; }
            select { background: #222; color: #fff; border: 1px solid #444; width: 100%; }
            .btn-audit { background: var(--primary); color: #000; cursor: pointer; transition: 0.3s; }
            .btn-audit:disabled { opacity: 0.3; }

            /* Report Styling */
            #report-container { display: none; margin-top: 3rem; animation: fadeIn 0.8s ease-out; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            
            .card { background: #1a1a23; padding: 2rem; border-radius: 20px; border: 1px solid #333; margin-bottom: 2rem; }
            .section-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: var(--primary); margin-bottom: 1rem; display: block; }
            
            .risk-badge { display: inline-block; padding: 0.5rem 1.5rem; border-radius: 100px; font-weight: 700; font-size: 0.9rem; margin-bottom: 1rem; }
            .risk-critical { background: rgba(255, 68, 68, 0.2); color: #ff4444; border: 1px solid #ff4444; }
            .risk-warning { background: rgba(255, 170, 0, 0.2); color: #ffaa00; border: 1px solid #ffaa00; }
            .risk-stable { background: rgba(0, 255, 136, 0.2); color: var(--primary); border: 1px solid var(--primary); }

            .drift-box { background: rgba(0, 229, 255, 0.05); border-left: 4px solid var(--accent); padding: 1.5rem; border-radius: 0 12px 12px 0; margin: 1rem 0; font-style: italic; }
            
            .thought-toggle { cursor: pointer; background: #222; padding: 1rem; border-radius: 12px; font-size: 0.8rem; color: #888; text-align: center; transition: 0.2s; margin-top: 1rem; }
            .thought-toggle:hover { background: #282828; color: #ccc; }
            #thought-trace { display: none; background: #000; padding: 1.5rem; border-radius: 12px; font-family: monospace; font-size: 0.8rem; border: 1px solid #222; margin-top: 1rem; color: #888; overflow-x: auto; }

            .expert-analysis { white-space: pre-wrap; font-size: 1rem; line-height: 1.6; opacity: 0.9; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SHADOW AUDITOR</h1>
            <p style="opacity:0.5; margin-top:0.5rem">Next-Gen Forensic Intelligence Engine</p>
            
            <div id="setup-view">
                <div id="drop-zone" class="drop-zone">
                    <span>Drag & Drop Multiple PDFs or Click to Browse</span>
                    <input type="file" id="file-input" multiple accept=".pdf" style="display: none;">
                </div>
                <div id="file-queue"></div>
                <div class="controls">
                    <select id="industry-select">
                        <option value="General">Target Industry: General</option>
                        <option value="Energy">Target Industry: Energy (Oil & Gas)</option>
                        <option value="Technology">Target Industry: Technology & SaaS</option>
                    </select>
                    <button id="audit-btn" class="btn-audit" disabled>INITIALIZE AUDIT</button>
                </div>
            </div>

            <div id="status-indicator" style="display:none; margin-top:3rem; text-align:center;">
                <div id="status-text" style="font-size:1.2rem; font-weight:700; color:var(--primary)">Decrypting Evidence...</div>
                <div style="height:4px; background:#222; border-radius:2px; margin-top:1rem; overflow:hidden">
                    <div id="progress-fill" style="height:100%; background:var(--primary); width:0%; transition:0.5s"></div>
                </div>
            </div>

            <div id="report-container">
                <!-- Meta Info -->
                <div class="card">
                    <div id="risk-badge" class="risk-badge"></div>
                    <div style="font-size:4rem; font-weight:700; margin-bottom:1rem;" id="risk-score"></div>
                    <span class="section-title">Executive Summary</span>
                    <div id="summary-text" style="font-size:1.2rem; font-weight:400; line-height:1.5"></div>
                </div>

                <!-- Narrative Drift -->
                <div class="card">
                    <span class="section-title">Longitudinal Narrative Drift Detected</span>
                    <div id="drift-text" class="drift-box"></div>
                </div>

                <!-- Forensic Ratios -->
                <div class="card">
                    <span class="section-title">Deterministic Financial Audit (LaTeX)</span>
                    <div id="ratios-container"></div>
                </div>

                <!-- Expert Analysis -->
                <div class="card">
                    <span class="section-title">Expert Forensic Analysis (Expert Mode)</span>
                    <div id="expert-text" class="expert-analysis"></div>
                </div>

                <!-- Next Steps -->
                <div class="card">
                    <span class="section-title">Actionable Next Steps</span>
                    <div id="steps-text" style="line-height:2"></div>
                </div>

                <!-- Reasoning Trace -->
                <div class="thought-toggle" onclick="toggleThought()">VIEW AUDIT LOGIC (AI REASONING TRACE)</div>
                <div id="thought-trace"></div>
                
                <button onclick="location.reload()" class="btn-audit" style="width:100%; margin-top:2rem; background:#222; color:#fff">RUN NEW AUDIT</button>
            </div>
        </div>

        <script>
            let queue = [];
            const dropZone = document.getElementById('drop-zone');
            const fileInput = document.getElementById('file-input');
            const auditBtn = document.getElementById('audit-btn');

            dropZone.onclick = () => fileInput.click();
            dropZone.ondragover = (e) => { e.preventDefault(); dropZone.classList.add('dragover'); };
            dropZone.ondragleave = () => dropZone.classList.remove('dragover');
            dropZone.ondrop = (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); handleFiles(e.dataTransfer.files); };
            fileInput.onchange = () => handleFiles(fileInput.files);

            function handleFiles(files) {
                Array.from(files).forEach(f => { if(f.type === 'application/pdf') queue.push(f); });
                renderQueue();
            }

            function renderQueue() {
                const q = document.getElementById('file-queue');
                q.innerHTML = '';
                queue.forEach((f, i) => {
                    const d = document.createElement('div');
                    d.className = 'file-item';
                    d.innerHTML = `<span>📄 ${f.name}</span><span style="color:#ff4444;cursor:pointer" onclick="queue.splice(${i},1);renderQueue()">REMOVE</span>`;
                    q.appendChild(d);
                });
                auditBtn.disabled = queue.length === 0;
            }

            function toggleThought() {
                const t = document.getElementById('thought-trace');
                t.style.display = t.style.display === 'block' ? 'none' : 'block';
            }

            auditBtn.onclick = async () => {
                document.getElementById('setup-view').style.display = 'none';
                document.getElementById('status-indicator').style.display = 'block';
                
                const formData = new FormData();
                queue.forEach(f => formData.append('files', f));
                formData.append('industry', document.getElementById('industry-select').value);

                updateStatus('Cross-Referencing Narrative Goalposts...', 40);
                
                try {
                    const resp = await fetch('/audit', { method: 'POST', body: formData });
                    const data = await resp.json();
                    
                    if (data.report.includes('=== SHADOW_AUDITOR_RESULT ===')) {
                        const jsonStr = data.report.split('=== SHADOW_AUDITOR_RESULT ===')[1].split('=== END_RESULT ===')[0];
                        const result = JSON.parse(jsonStr);
                        renderReport(result);
                    } else {
                        alert("Format error in audit report.");
                    }
                } catch (e) {
                    alert("Audit failed: " + e);
                    location.reload();
                }
            };

            function updateStatus(text, progress) {
                document.getElementById('status-text').textContent = text;
                document.getElementById('progress-fill').style.width = progress + '%';
            }

            function renderReport(data) {
                document.getElementById('status-indicator').style.display = 'none';
                document.getElementById('report-container').style.display = 'block';
                
                document.getElementById('risk-score').textContent = data.score;
                const badge = document.getElementById('risk-badge');
                badge.textContent = data.level + ' RISK';
                badge.className = 'risk-badge risk-' + data.level.toLowerCase();
                
                document.getElementById('summary-text').textContent = data.summary;
                document.getElementById('drift-text').textContent = data.drift;
                document.getElementById('ratios-container').innerHTML = data.ratios;
                document.getElementById('expert-text').textContent = data.expert;
                document.getElementById('steps-text').textContent = data.next_steps;
                document.getElementById('thought-trace').textContent = data.thought_trace;
                
                // Trigger MathJax
                if(window.MathJax) MathJax.typeset();
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

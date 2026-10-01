"""
Air-Gapped Web Testing Console for DUMB-DOG-AI Resume Parsing & Candidate Intelligence
Fully self-hosted, running on local hardware (RTX 4080 16GB) with zero external cloud APIs.

Run with:
    py -3.12 web_ui.py
Then open http://localhost:8000 in your browser.
"""

import os
import sys
import time
import json
import torch
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from parsers.router import route_file
from parsers.docling_parser import parse_with_docling
from parsers.ocr_engine import extract_with_ocr
from optimized_pdf_engine import OptimizedPDFEngine
from extraction.llm_local import extract_candidate_profile
from matching.bge_matcher import SkillMatcher

app = FastAPI(title="DUMB-DOG-AI Testing Console")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BENCHMARK_DATA_DIR = Path("benchmark_data")
pdf_engine = OptimizedPDFEngine()
skill_matcher = SkillMatcher()

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DUMB-DOG-AI — Local Resume Intelligence Console</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    /* Robust air-gapped fallback styles in case CDN is offline */
    body { background-color: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .tab-active { border-bottom: 2px solid #3b82f6; color: #3b82f6; font-weight: 600; }
    pre { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
  </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen antialiased flex flex-col">

  <!-- Header -->
  <header class="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center font-black text-sm tracking-wider shadow">AI</div>
        <div>
          <h1 class="text-base font-bold leading-tight tracking-wide">DUMB-DOG-AI</h1>
          <p class="text-xs text-slate-400">Air-Gapped Resume Parsing &amp; Candidate Intelligence Console</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          RTX 4080 (16GB) Local
        </span>
        <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
          Air-Gapped (Zero Cloud)
        </span>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto px-4 py-6 flex-1 w-full grid grid-cols-1 lg:grid-cols-12 gap-6">

    <!-- Left Controls Panel (4 Cols) -->
    <div class="lg:col-span-4 space-y-5">

      <!-- Upload & Quick Samples Card -->
      <div class="bg-slate-800/90 border border-slate-700/80 rounded-xl p-5 shadow-lg space-y-4">
        <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider">1. Select Document</h2>
        
        <!-- File Dropzone -->
        <div id="dropzone" class="border-2 border-dashed border-slate-600 hover:border-blue-500 transition rounded-xl p-5 text-center cursor-pointer bg-slate-900/60">
          <input type="file" id="fileInput" class="hidden" accept=".pdf,.docx,.png,.jpg,.jpeg">
          <div class="text-xs text-slate-300 font-medium">Click or Drag &amp; Drop Resume</div>
          <div class="text-[11px] text-slate-500 mt-1">PDF, DOCX, PNG, JPG</div>
          <div id="selectedFileName" class="text-xs text-blue-400 font-semibold mt-2 hidden truncate"></div>
        </div>

        <!-- Quick Sample Buttons -->
        <div>
          <div class="text-xs text-slate-400 mb-2 font-medium">Or Quick-Load Benchmark Sample:</div>
          <div class="grid grid-cols-2 gap-2" id="samplesContainer">
            <button onclick="loadSample('thai_resume.pdf')" id="btn-thai_resume.pdf" class="sample-btn px-3 py-2 text-xs bg-slate-900 hover:bg-slate-700 rounded-lg border border-slate-700 text-left transition truncate">
              Thai Resume (PDF)
            </button>
            <button onclick="loadSample('english_resume.pdf')" id="btn-english_resume.pdf" class="sample-btn px-3 py-2 text-xs bg-slate-900 hover:bg-slate-700 rounded-lg border border-slate-700 text-left transition truncate">
              English Resume (PDF)
            </button>
            <button onclick="loadSample('bilingual_resume.pdf')" id="btn-bilingual_resume.pdf" class="sample-btn px-3 py-2 text-xs bg-slate-900 hover:bg-slate-700 rounded-lg border border-slate-700 text-left transition truncate">
              Bilingual (PDF)
            </button>
            <button onclick="loadSample('scanned_resume.png')" id="btn-scanned_resume.png" class="sample-btn px-3 py-2 text-xs bg-slate-900 hover:bg-slate-700 rounded-lg border border-slate-700 text-left transition truncate">
              Scanned Image (PNG)
            </button>
            <button onclick="loadSample('real_functional_resume.pdf')" id="btn-real_functional_resume.pdf" class="col-span-2 sample-btn px-3 py-2 text-xs bg-slate-900 hover:bg-slate-700 rounded-lg border border-slate-700 text-left transition truncate">
              Real Functional Resume (PDF)
            </button>
          </div>
        </div>
      </div>

      <!-- Configuration Card -->
      <div class="bg-slate-800/90 border border-slate-700/80 rounded-xl p-5 shadow-lg space-y-4">
        <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider">2. Configuration</h2>
        
        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1">Local LLM Extractor</label>
          <select id="modelSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500">
            <option value="qwen2.5:7b" selected>qwen2.5:7b (Top Accuracy &amp; F1)</option>
            <option value="typhoon2:8b">scb10x/typhoon2:8b (Thai Specialized)</option>
            <option value="llama3.1:8b">llama3.1:8b (Generalist)</option>
            <option value="deepseek-r1:8b">deepseek-r1:8b (Reasoning)</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1">Routing Mode</label>
          <select id="modeSelect" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500">
            <option value="auto" selected>Auto Gateway (3-Signal Garble Detection)</option>
            <option value="vector_fastpath">Force Vector Fast-Path (&lt; 10ms)</option>
            <option value="ocr_engine">Force Typhoon OCR (Vision-Language)</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1">Primary OCR Model</label>
          <div class="text-xs text-slate-400 bg-slate-900 px-3 py-2 rounded-lg border border-slate-700 font-mono">
            typhoon-ocr-finetuned:latest
          </div>
        </div>

        <button id="runBtn" onclick="runPipeline()" class="w-full py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 active:scale-[0.99] font-bold text-xs tracking-wider uppercase transition shadow-md flex items-center justify-center gap-2">
          Run Parsing &amp; Extraction
        </button>
      </div>

      <!-- Pipeline Telemetry -->
      <div id="telemetryCard" class="bg-slate-800/90 border border-slate-700/80 rounded-xl p-5 shadow-lg space-y-3 hidden">
        <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider">Live Telemetry &amp; Routing</h2>
        <div class="space-y-2 text-xs">
          <div class="flex justify-between py-1 border-b border-slate-700/50">
            <span class="text-slate-400">Selected Route:</span>
            <span id="routeBadge" class="font-bold text-emerald-400">Vector Fast-Path</span>
          </div>
          <div class="flex justify-between py-1 border-b border-slate-700/50">
            <span class="text-slate-400">Thai Garble Score:</span>
            <span id="garbleScore" class="font-mono text-slate-200">0.034 (Clean)</span>
          </div>
          <div class="flex justify-between py-1 border-b border-slate-700/50">
            <span class="text-slate-400">Total Latency:</span>
            <span id="totalLatency" class="font-bold text-blue-400">1,240 ms</span>
          </div>
          <div class="flex justify-between py-1">
            <span class="text-slate-400">Schema Validation:</span>
            <span id="schemaValid" class="font-bold text-emerald-400">PASSED (Pydantic v2)</span>
          </div>
        </div>
      </div>

    </div>

    <!-- Right Results Panel (8 Cols) -->
    <div class="lg:col-span-8 space-y-5">

      <!-- Tabs Header -->
      <div class="border-b border-slate-800 flex items-center gap-6 text-sm">
        <button onclick="switchTab('profile')" id="tabBtn-profile" class="tab-active py-2 transition">Candidate Profile</button>
        <button onclick="switchTab('skills')" id="tabBtn-skills" class="py-2 text-slate-400 hover:text-slate-200 transition">Skills &amp; Normalization</button>
        <button onclick="switchTab('markdown')" id="tabBtn-markdown" class="py-2 text-slate-400 hover:text-slate-200 transition">Parsed Markdown</button>
        <button onclick="switchTab('json')" id="tabBtn-json" class="py-2 text-slate-400 hover:text-slate-200 transition">Raw JSON</button>
      </div>

      <!-- State: Empty / Placeholder -->
      <div id="emptyState" class="bg-slate-800/40 border border-dashed border-slate-700 rounded-2xl p-16 text-center space-y-3">
        <div class="text-slate-400 font-semibold text-sm">No Document Processed Yet</div>
        <p class="text-xs text-slate-500 max-w-sm mx-auto">Select a sample resume on the left or upload your own file, then click "Run Parsing &amp; Extraction".</p>
      </div>

      <!-- State: Loading Spinner -->
      <div id="loadingState" class="hidden bg-slate-800/40 border border-slate-700 rounded-2xl p-16 text-center space-y-4">
        <div class="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <div class="text-sm font-semibold text-slate-200" id="loadingText">Processing document with local RTX 4080 engine...</div>
        <div class="text-xs text-slate-400">Routing, extracting text, running local LLM schema validation</div>
      </div>

      <!-- Tab 1: Candidate Profile Card -->
      <div id="tabContent-profile" class="hidden space-y-5">
        
        <!-- Header Info Card -->
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-md space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div>
              <h2 id="profName" class="text-2xl font-bold text-white tracking-tight">John Doe</h2>
              <div id="profRole" class="text-sm font-semibold text-blue-400 mt-0.5">Senior Software Engineer</div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <span id="profSeniority" class="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">Senior</span>
              <span id="profYears" class="px-3 py-1 rounded-full text-xs font-semibold bg-slate-700 text-slate-300 border border-slate-600">8.0 Years Exp</span>
            </div>
          </div>

          <div id="profContact" class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-300 border-t border-slate-700/60 pt-3">
            <div><span class="text-slate-500 font-medium">Email:</span> <span id="profEmail">-</span></div>
            <div><span class="text-slate-500 font-medium">Phone:</span> <span id="profPhone">-</span></div>
          </div>

          <div id="profSummaryBox" class="bg-slate-900/70 border border-slate-700/50 rounded-lg p-3 text-xs text-slate-300 leading-relaxed">
            <span class="font-semibold text-slate-200">Executive Summary: </span>
            <span id="profSummary">-</span>
          </div>
        </div>

        <!-- Work Experience Timeline -->
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-md space-y-4">
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300">Professional Experience</h3>
          <div id="profExperienceList" class="space-y-4"></div>
        </div>

        <!-- Education Section -->
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-md space-y-4">
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300">Education</h3>
          <div id="profEducationList" class="grid grid-cols-1 sm:grid-cols-2 gap-3"></div>
        </div>

      </div>

      <!-- Tab 2: Skills & Normalization -->
      <div id="tabContent-skills" class="hidden bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-md space-y-5">
        <div>
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">Canonical Normalized Skills (BGE-M3 Matching)</h3>
          <p class="text-xs text-slate-400 mb-4">Extracted raw skills mapped into standardized taxonomy with cosine similarity score.</p>
          <div id="skillsTable" class="divide-y divide-slate-700 text-xs"></div>
        </div>
      </div>

      <!-- Tab 3: Parsed Markdown -->
      <div id="tabContent-markdown" class="hidden bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-md space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300">Extracted Markdown Document</h3>
          <button onclick="copyMarkdown()" class="text-xs bg-slate-700 hover:bg-slate-600 px-2.5 py-1 rounded text-slate-200 transition">Copy Markdown</button>
        </div>
        <pre id="rawMarkdownContent" class="bg-slate-950 p-4 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-[550px]"></pre>
      </div>

      <!-- Tab 4: Raw JSON -->
      <div id="tabContent-json" class="hidden bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-md space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300">CandidateProfile JSON Schema Output</h3>
          <button onclick="copyJson()" class="text-xs bg-slate-700 hover:bg-slate-600 px-2.5 py-1 rounded text-slate-200 transition">Copy JSON</button>
        </div>
        <pre id="rawJsonContent" class="bg-slate-950 p-4 rounded-lg text-xs font-mono text-emerald-400 overflow-x-auto whitespace-pre max-h-[550px]"></pre>
      </div>

    </div>

  </main>

  <script>
    let activeTab = 'profile';
    let selectedSample = 'thai_resume.pdf';
    let currentUploadedFile = null;
    let latestJsonData = null;

    // Highlight default sample button
    window.onload = () => {
      const defBtn = document.getElementById('btn-thai_resume.pdf');
      if (defBtn) {
        defBtn.classList.add('bg-blue-600/30', 'border-blue-500');
        defBtn.classList.remove('bg-slate-900', 'border-slate-700');
      }
    };

    // Dropzone setup
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const selectedFileName = document.getElementById('selectedFileName');

    dropzone.onclick = () => fileInput.click();
    fileInput.onchange = (e) => {
      if (e.target.files.length > 0) {
        currentUploadedFile = e.target.files[0];
        selectedSample = null;
        selectedFileName.textContent = currentUploadedFile.name;
        selectedFileName.classList.remove('hidden');
        resetSampleHighlights();
      }
    };

    dropzone.ondragover = (e) => { e.preventDefault(); dropzone.classList.add('border-blue-500'); };
    dropzone.ondragleave = () => { dropzone.classList.remove('border-blue-500'); };
    dropzone.ondrop = (e) => {
      e.preventDefault();
      dropzone.classList.remove('border-blue-500');
      if (e.dataTransfer.files.length > 0) {
        currentUploadedFile = e.dataTransfer.files[0];
        selectedSample = null;
        selectedFileName.textContent = currentUploadedFile.name;
        selectedFileName.classList.remove('hidden');
        resetSampleHighlights();
      }
    };

    function resetSampleHighlights() {
      document.querySelectorAll('.sample-btn').forEach(b => {
        b.classList.remove('bg-blue-600/30', 'border-blue-500');
        b.classList.add('bg-slate-900', 'border-slate-700');
      });
    }

    function loadSample(sampleName) {
      selectedSample = sampleName;
      currentUploadedFile = null;
      selectedFileName.classList.add('hidden');
      resetSampleHighlights();
      const btn = document.getElementById(`btn-${sampleName}`);
      if (btn) {
        btn.classList.add('bg-blue-600/30', 'border-blue-500');
        btn.classList.remove('bg-slate-900', 'border-slate-700');
      }
    }

    function switchTab(tab) {
      activeTab = tab;
      ['profile', 'skills', 'markdown', 'json'].forEach(t => {
        const btn = document.getElementById(`tabBtn-${t}`);
        const content = document.getElementById(`tabContent-${t}`);
        if (t === tab) {
          btn.className = "tab-active py-2 transition";
          content.classList.remove('hidden');
        } else {
          btn.className = "py-2 text-slate-400 hover:text-slate-200 transition";
          content.classList.add('hidden');
        }
      });
    }

    async function runPipeline() {
      const runBtn = document.getElementById('runBtn');
      const emptyState = document.getElementById('emptyState');
      const loadingState = document.getElementById('loadingState');
      const telemetryCard = document.getElementById('telemetryCard');
      const model = document.getElementById('modelSelect').value;
      const mode = document.getElementById('modeSelect').value;

      emptyState.classList.add('hidden');
      ['profile', 'skills', 'markdown', 'json'].forEach(t => document.getElementById(`tabContent-${t}`).classList.add('hidden'));
      loadingState.classList.remove('hidden');
      runBtn.disabled = true;

      const formData = new FormData();
      formData.append('model', model);
      formData.append('mode', mode);
      if (currentUploadedFile) {
        formData.append('file', currentUploadedFile);
      } else {
        formData.append('sample', selectedSample);
      }

      try {
        const res = await fetch('/api/process', { method: 'POST', body: formData });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Processing failed');
        }
        const data = await res.json();
        latestJsonData = data;
        renderResults(data);
      } catch (err) {
        alert('Error: ' + err.message);
        emptyState.classList.remove('hidden');
      } finally {
        loadingState.classList.add('hidden');
        runBtn.disabled = false;
      }
    }

    function renderResults(data) {
      // Telemetry
      const telemetryCard = document.getElementById('telemetryCard');
      telemetryCard.classList.remove('hidden');
      document.getElementById('routeBadge').textContent = data.route;
      const garbleText = data.garble_score.toFixed(3) + (data.garble_score < 0.15 ? ' (Clean)' : ' (Degraded / Garbled)');
      document.getElementById('garbleScore').textContent = garbleText;
      document.getElementById('totalLatency').textContent = data.total_latency_ms + ' ms';
      document.getElementById('schemaValid').textContent = data.schema_valid ? 'PASSED (Pydantic v2)' : 'FAILED';

      const p = data.profile;

      // Tab 1: Profile
      document.getElementById('profName').textContent = p.full_name || 'N/A';
      document.getElementById('profRole').textContent = (p.experience && p.experience[0]) ? p.experience[0].role : 'Candidate';
      document.getElementById('profSeniority').textContent = p.seniority_level || 'Mid-Level';
      document.getElementById('profYears').textContent = (p.total_years_experience || 0) + ' Years Exp';
      document.getElementById('profEmail').textContent = p.contact_email || 'Not Specified';
      document.getElementById('profPhone').textContent = p.contact_phone || 'Not Specified';
      document.getElementById('profSummary').textContent = p.executive_summary || 'No summary generated.';

      // Experience
      const expList = document.getElementById('profExperienceList');
      expList.innerHTML = '';
      if (p.experience && p.experience.length > 0) {
        p.experience.forEach(exp => {
          const card = document.createElement('div');
          card.className = "border-l-2 border-blue-500 pl-4 space-y-1";
          const dates = `${exp.start_date || ''} - ${exp.end_date || 'Present'}`;
          let bullets = '';
          if (exp.achievements) {
            bullets = exp.achievements.map(a => `<li>• ${a}</li>`).join('');
          }
          card.innerHTML = `
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold text-slate-100">${exp.role}</span>
              <span class="text-slate-400 font-mono">${dates}</span>
            </div>
            <div class="text-xs text-blue-400 font-semibold">${exp.company}</div>
            <ul class="text-xs text-slate-300 mt-1 space-y-0.5 list-none">${bullets}</ul>
          `;
          expList.appendChild(card);
        });
      } else {
        expList.innerHTML = '<div class="text-xs text-slate-500">No experience records detected.</div>';
      }

      // Education
      const eduList = document.getElementById('profEducationList');
      eduList.innerHTML = '';
      if (p.education && p.education.length > 0) {
        p.education.forEach(edu => {
          const card = document.createElement('div');
          card.className = "bg-slate-900/60 p-3 rounded-lg border border-slate-700/40 text-xs";
          card.innerHTML = `
            <div class="font-bold text-slate-200">${edu.degree || 'Degree'}</div>
            <div class="text-slate-400 mt-0.5">${edu.institution || 'University'}</div>
            <div class="text-slate-500 text-[11px] mt-1">${edu.graduation_year || ''}</div>
          `;
          eduList.appendChild(card);
        });
      }

      // Tab 2: Skills & Normalization
      const skTable = document.getElementById('skillsTable');
      skTable.innerHTML = '';
      if (data.normalized_skills && data.normalized_skills.length > 0) {
        data.normalized_skills.forEach(item => {
          const row = document.createElement('div');
          row.className = "py-2 flex items-center justify-between";
          const isMatched = item.matched_canonical !== null;
          row.innerHTML = `
            <div>
              <span class="font-medium text-slate-200">${item.original}</span>
              <span class="text-slate-500 text-[11px] ml-2">&rarr;</span>
              <span class="ml-2 font-semibold ${isMatched ? 'text-indigo-400' : 'text-slate-500'}">
                ${item.matched_canonical || 'Unmapped Skill'}
              </span>
            </div>
            <div class="font-mono text-xs ${item.similarity_score >= 0.8 ? 'text-emerald-400 font-bold' : 'text-slate-500'}">
              Score: ${item.similarity_score.toFixed(2)}
            </div>
          `;
          skTable.appendChild(row);
        });
      }

      // Tab 3: Markdown
      document.getElementById('rawMarkdownContent').textContent = data.markdown || '';

      // Tab 4: JSON
      document.getElementById('rawJsonContent').textContent = JSON.stringify(p, null, 2);

      switchTab(activeTab);
    }

    function copyMarkdown() {
      if (latestJsonData && latestJsonData.markdown) {
        navigator.clipboard.writeText(latestJsonData.markdown);
        alert('Copied Markdown to clipboard!');
      }
    }

    function copyJson() {
      if (latestJsonData && latestJsonData.profile) {
        navigator.clipboard.writeText(JSON.stringify(latestJsonData.profile, null, 2));
        alert('Copied JSON to clipboard!');
      }
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def get_index():
    return HTMLResponse(content=HTML_CONTENT)


@app.post("/api/process")
async def process_resume(
    file: Optional[UploadFile] = File(None),
    sample: Optional[str] = Form(None),
    model: str = Form("qwen2.5:7b"),
    mode: str = Form("auto")
):
    t_start = time.perf_counter()
    temp_dir = tempfile.mkdtemp()
    target_path = None

    try:
        if file is not None and file.filename:
            target_path = Path(temp_dir) / file.filename
            with open(target_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        elif sample:
            sample_path = BENCHMARK_DATA_DIR / sample
            if not sample_path.exists():
                raise HTTPException(status_code=404, detail=f"Sample '{sample}' not found")
            target_path = sample_path
        else:
            raise HTTPException(status_code=400, detail="No file or sample provided")

        # 1. Routing Gateway
        route_decision = route_file(target_path)
        garble = route_decision.garble_score

        # Apply mode override if requested
        if mode == "vector_fastpath":
            use_ocr = False
            route_str = "Forced Vector Fast-Path (PyMuPDF)"
        elif mode == "ocr_engine":
            use_ocr = True
            route_str = "Forced OCR Engine (Typhoon VLM)"
        else:
            use_ocr = route_decision.requires_ocr
            route_str = "OCR Engine (Typhoon VLM)" if use_ocr else "Vector Fast-Path (Docling)"

        # 2. Parsing (Vector or OCR)
        if use_ocr:
            markdown_text = extract_with_ocr(str(target_path))
        else:
            # Check fast-path engine
            if target_path.suffix.lower() == ".pdf":
                fast_res = pdf_engine.process_document(target_path)
                markdown_text = fast_res.get("text") or parse_with_docling(str(target_path))
            else:
                markdown_text = parse_with_docling(str(target_path))

        # 3. LLM Extraction
        profile = extract_candidate_profile(markdown_text, model=model)

        # 4. Skill Normalization
        normalized = skill_matcher.normalize_skills(profile.skills)

        total_latency_ms = round((time.perf_counter() - t_start) * 1000)

        return JSONResponse(content={
            "filename": target_path.name,
            "route": route_str,
            "requires_ocr": use_ocr,
            "garble_score": garble,
            "total_latency_ms": total_latency_ms,
            "schema_valid": True,
            "markdown": markdown_text,
            "profile": profile.model_dump(),
            "normalized_skills": normalized
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if file is not None and Path(temp_dir).exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("[INFO] Starting DUMB-DOG-AI Web Testing Console on http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)

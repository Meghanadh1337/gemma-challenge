import os
import time
import json
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai
from google.genai import types

load_dotenv()

def get_api_key():
    key = os.getenv("GEMMA_API_KEY")
    if not key or "your_actual_key" in key:
        return None
    return key

# --- RETRY WRAPPER (Root cause fix for transient 500 errors) ---
def call_gemma(client, **kwargs):
    """Calls the Gemini API with automatic retry on transient 500 errors."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(**kwargs)
        except Exception as e:
            if "500 INTERNAL" in str(e) and attempt < max_retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s
                print(f"  [Retry {attempt+1}/{max_retries}] Gemini 500 error, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise

# --- SCHEMAS ---
class FinancialFacts(BaseModel):
    company_name: str
    predicted_industry: str
    revenue_current: float
    revenue_previous: float
    auditor_changes: int
    risk_factor_word_count_delta: float
    high_risk_keyword_count: int
    spe_mentions: int = 0
    mark_to_market_mentions: int = 0
    jv_mentions: int = 0
    deferred_revenue_growth: float = 0.0
    stock_based_comp_ratio: float = 0.0
    rd_spend_total: float = 0.0
    receivables_current: float = 0.0
    receivables_previous: float = 0.0
    inventory_turnover_delta: float = 0.0

class Citation(BaseModel):
    quote: str
    context: str

class ForensicAuditReport(BaseModel):
    executive_summary: str
    executive_summary_layman: str
    narrative_drift_analysis: str
    narrative_drift_layman: str
    forensic_analysis_expert: str
    forensic_analysis_layman: str
    archetype_match: str
    citations: List[Citation]
    next_steps: List[str]

# --- DETERMINISTIC ENGINE (Pure Python, no LLM) ---
class DeterministicForensicEngine:
    """Polymorphic Forensic Engine. Selects forensic vectors based on predicted industry."""
    def __init__(self, facts: FinancialFacts, temporal_gaps_detected: bool = False):
        self.facts = facts
        self.temporal_gaps_detected = temporal_gaps_detected
        self.metrics = {}
        self.ratios = []

    def compute(self):
        # 1. UNIVERSAL RED FLAGS (30% weight)
        self.metrics['auditor_instability'] = 1.0 if self.facts.auditor_changes > 0 else 0.0
        self.metrics['narrative_shift'] = min(abs(self.facts.risk_factor_word_count_delta) / 100, 1.0)
        self.metrics['semantic_suspicion'] = min(self.facts.high_risk_keyword_count * 0.1, 1.0)

        # 2. SECTOR-SPECIFIC LOGIC (70% weight)
        industry = self.facts.predicted_industry.upper()
        
        if "ENERGY" in industry:
            complexity = (self.facts.spe_mentions * 2) + self.facts.jv_mentions
            self.metrics['sector_specific_risk'] = min(complexity / 8, 1.0)
            self.metrics['accounting_opacity'] = min(self.facts.mark_to_market_mentions / 5, 1.0)
            self.ratios.append({
                "name": "Structural Complexity Index",
                "formula": "(SPE mentions × 2) + JV mentions",
                "value": f"{complexity}",
                "audit": "High counts of Special Purpose Entities suggest off-balance sheet risk."
            })

        elif "TECH" in industry or "SAAS" in industry:
            sbc_risk = self.facts.stock_based_comp_ratio
            rd_yield = self.facts.revenue_current / max(self.facts.rd_spend_total, 1)
            self.metrics['sector_specific_risk'] = min(sbc_risk * 5, 1.0)
            self.metrics['accounting_opacity'] = 1.0 if rd_yield < 2.0 else 0.0
            self.ratios.append({
                "name": "SBC to Revenue Dilution",
                "formula": "Stock Based Comp / Revenue",
                "value": f"{sbc_risk:.2%}",
                "audit": "High SBC can mask poor operating cash flow."
            })

        else:
            rec_rev_curr = self.facts.receivables_current / max(self.facts.revenue_current, 1)
            rec_rev_prev = self.facts.receivables_previous / max(self.facts.revenue_previous, 1)
            delta = rec_rev_curr - rec_rev_prev
            self.metrics['sector_specific_risk'] = min(max(delta * 5, 0), 1.0)
            self.metrics['accounting_opacity'] = min(abs(self.facts.inventory_turnover_delta) / 20, 1.0)
            self.ratios.append({
                "name": "Receivables Drift",
                "formula": "Δ(Receivables / Revenue)",
                "value": f"{delta:.4f}",
                "audit": "Receivables growing faster than sales is a prime revenue-recognition red flag."
            })

        # FINAL SYNTHESIS
        weights = {
            "auditor_instability": 0.10,
            "narrative_shift": 0.10,
            "semantic_suspicion": 0.10,
            "sector_specific_risk": 0.40,
            "accounting_opacity": 0.30
        }
        score = sum(self.metrics.get(k, 0) * w for k, w in weights.items()) * 100
        
        if self.metrics.get('sector_specific_risk', 0) > 0.5:
            score = max(score, 55.0)
        if self.metrics.get('sector_specific_risk', 0) > 0.75 or self.metrics.get('accounting_opacity', 0) > 0.75:
            score = max(score, 75.0)
        if self.temporal_gaps_detected:
            self.metrics['integrity_of_disclosures'] = 1.0
            score = max(score, 65.0)
            
        return min(score, 100.0)


def run_forensic_audit(text: str) -> str:
    """
    5-Pass Adaptive Forensic Pipeline with retry logic.
    """
    api_key = get_api_key()
    if not api_key:
        return json.dumps({"error": "GEMMA_API_KEY not found."})

    client = genai.Client(api_key=api_key)
    
    # Limit input to prevent API overload. 30K is plenty for integrity + classification.
    text_short = text[:30000]
    # 50K for extraction (was 100K — primary cause of 500 errors)
    text_medium = text[:50000]

    # --- PASS -1: DATA INTEGRITY PRE-FLIGHT ---
    try:
        integrity_resp = call_gemma(
            client,
            model="gemma-4-31b-it",
            contents=f"Analyze the following document for forensic integrity:\n\n{text_short}",
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a Forensic Data Integrity Validator. Return a JSON object with these exact keys:\n"
                    "is_financial_document (bool), single_entity_detected (bool), entities_found (list of strings), "
                    "filing_years (list of ints), temporal_gaps_detected (bool).\n"
                    "IMPORTANT: Subsidiaries and joint ventures of the primary filer are NOT separate companies."
                ),
                temperature=0,
                response_mime_type="application/json"
            )
        )
        raw_text = integrity_resp.text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
            raw_text = re.sub(r'\s*```$', '', raw_text)
        integrity = json.loads(raw_text)
        
        if not integrity.get("is_financial_document", True):
            return json.dumps({"error": "Audit Aborted: No valid financial disclosures detected."})
        if not integrity.get("single_entity_detected", True):
            entities = ', '.join(integrity.get('entities_found', []))
            return json.dumps({"error": f"Audit Aborted: Multiple unrelated entities found: {entities}. Upload files for one company only."})
            
        temporal_gaps = integrity.get("temporal_gaps_detected", False)
        entities_found = integrity.get("entities_found", [])
        filing_years = integrity.get("filing_years", [])
    except Exception as e:
        # If integrity check fails, proceed anyway with defaults rather than blocking
        print(f"  [WARN] Integrity check failed ({e}), proceeding with defaults.")
        temporal_gaps = False
        entities_found = ["Unknown"]
        filing_years = []

    # --- PASS 0: SECTOR CLASSIFICATION ---
    try:
        class_resp = call_gemma(
            client,
            model="gemma-4-31b-it",
            contents=f"Classify the primary industry for this company as one word: ENERGY, TECH, BANKING, or GENERAL.\n\n{text_short}",
            config=types.GenerateContentConfig(temperature=0)
        )
        industry = class_resp.text.strip().upper()
        if "ENERGY" in industry: sector = "ENERGY"
        elif "TECH" in industry: sector = "TECH"
        else: sector = "GENERAL"
    except:
        sector = "GENERAL"

    # --- PASS 1: ADAPTIVE EXTRACTION ---
    sector_hints = {
        "ENERGY": "Focus on Special Purpose Entities (SPEs), Mark-to-Market accounting, and structural complexity.",
        "TECH": "Focus on Stock-Based Comp (SBC) ratios, R&D yield, and Deferred Revenue growth.",
        "GENERAL": "Focus on Receivables vs Revenue growth and Inventory Turnover deltas."
    }
    
    try:
        extract_resp = call_gemma(
            client,
            model="gemma-4-31b-it",
            contents=f"Perform forensic extraction on these {sector} records:\n\n{text_medium}",
            config=types.GenerateContentConfig(
                system_instruction=(
                    f"You are a Sector-Specific Forensic Data Extractor for the {sector} industry.\n"
                    f"ONTOLOGY HINT: {sector_hints[sector]}\n"
                    "Extract raw numeric facts matching the provided schema. Do not calculate. Just extract."
                ),
                temperature=0,
                response_mime_type="application/json",
                response_schema=FinancialFacts
            )
        )
        facts = extract_resp.parsed
        facts.predicted_industry = sector
    except Exception as e:
        return json.dumps({"error": f"Extraction Error: {str(e)}"})

    # --- PASS 2: DETERMINISTIC COMPUTATION ---
    engine = DeterministicForensicEngine(facts, temporal_gaps)
    risk_score = engine.compute()
    metrics = engine.metrics
    risk_level = "CRITICAL" if risk_score > 70 else "WARNING" if risk_score > 30 else "STABLE"

    # --- PASS 3: CONSTRAINED INTERPRETATION ---
    # NOTE: thinking_config is used WITHOUT response_schema to avoid 500 crashes.
    # We get the thought trace from thinking, and parse JSON manually.
    interpretation_prompt = (
        "ROLE: You are an Elite Forensic Accounting Investigator. "
        "You are highly objective, evidence-driven, and deeply skeptical of management narrative.\n\n"
        f"Interpret the following results for {facts.company_name} in the {sector} sector.\n\n"
        f"FRAUD RISK SCORE: {risk_score:.2f}/100\n"
        f"METRICS: {json.dumps(metrics)}\n"
        f"RATIOS: {json.dumps(engine.ratios)}\n\n"
        "Return a JSON object with these exact keys:\n"
        "executive_summary, executive_summary_layman, narrative_drift_analysis, narrative_drift_layman, "
        "forensic_analysis_expert, forensic_analysis_layman, archetype_match (2-4 words ONLY), "
        "citations (list of {quote, context}), "
        "next_steps (list of strings, written for a retail investor with specific EDGAR search queries)."
    )

    try:
        report_resp = call_gemma(
            client,
            model="gemma-4-31b-it",
            contents=f"Analyze these forensic results:\n\n{text_medium}",
            config=types.GenerateContentConfig(
                system_instruction=interpretation_prompt,
                temperature=0.1,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_level="medium")
            )
        )
        
        thought_process = ""
        report_json = None
        if report_resp.candidates:
            for part in report_resp.candidates[0].content.parts:
                if getattr(part, 'thought', False):
                    thought_process += part.text + "\n"
                else:
                    # This is the actual JSON response
                    raw = part.text.strip()
                    if raw.startswith("```"):
                        raw = re.sub(r'^```(?:json)?\s*', '', raw)
                        raw = re.sub(r'\s*```$', '', raw)
                    if raw:
                        report_json = json.loads(raw)

        if not report_json:
            return json.dumps({"error": "Interpretation produced no output."})

        citations = report_json.get("citations", [])
        citation_str = "\n".join([f"- \"{c.get('quote','')}\"  [Context: {c.get('context','')}]" for c in citations])
        next_steps = report_json.get("next_steps", [])

        if filing_years:
            years_str = f"{min(filing_years)} to {max(filing_years)}" if len(filing_years) > 1 else str(filing_years[0])
        else:
            years_str = "Unknown Years"
        upload_context = f"{', '.join(entities_found)} Financial Filings ({years_str})"

        report_data = {
            "upload_context": upload_context,
            "score": f"{risk_score:.2f}",
            "level": risk_level,
            "metrics": metrics,
            "industry": sector,
            "summary": report_json.get("executive_summary", ""),
            "summary_layman": report_json.get("executive_summary_layman", ""),
            "drift": report_json.get("narrative_drift_analysis", ""),
            "drift_layman": report_json.get("narrative_drift_layman", ""),
            "ratios": engine.ratios,
            "citations": citation_str,
            "expert": report_json.get("forensic_analysis_expert", ""),
            "expert_layman": report_json.get("forensic_analysis_layman", ""),
            "archetype": report_json.get("archetype_match", "N/A"),
            "next_steps": "\n".join([f"{i+1}. {s}" for i, s in enumerate(next_steps)]),
            "thought_trace": thought_process if thought_process else "No reasoning trace available."
        }

        return f"=== SHADOW_AUDITOR_RESULT ===\n{json.dumps(report_data)}\n=== END_RESULT ==="

    except Exception as e:
        return json.dumps({"error": f"Interpretation Error: {str(e)}"})

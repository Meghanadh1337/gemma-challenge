import os
import time
import json
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

def get_api_key():
    key = os.getenv("GEMMA_API_KEY")
    if not key or "your_actual_key" in key:
        return None
    return key

def calculate_fraud_risk_score(metrics: Dict[str, float]) -> float:
    """
    Weighted scoring logic. Integrity of Disclosures now carries high weight.
    """
    weights = {
        "receivables_vs_revenue": 0.25,
        "auditor_turnover": 0.2,
        "buzzword_vs_cashflow": 0.15,
        "risk_factor_shift": 0.1,
        "integrity_of_disclosures": 0.3  # Shell games (like EOTT) are major red flags
    }
    
    score = sum(metrics.get(k, 0) * w for k, w in weights.items()) * 100
    return min(score, 100.0)

from google import genai
from google.genai import types
import json
from pydantic import BaseModel

from typing import List, Optional

class DataIntegrity(BaseModel):
    is_financial_document: bool
    single_entity_detected: bool
    entities_found: List[str]
    filing_years: List[int]
    temporal_gaps_detected: bool
    rejection_reason: str = ""

class FinancialFacts(BaseModel):
    # --- UNIVERSAL SIGNALS ---
    company_name: str
    predicted_industry: str # e.g. ENERGY, TECH, BANKING, GENERAL
    revenue_current: float
    revenue_previous: float
    auditor_changes: int
    risk_factor_word_count_delta: float
    high_risk_keyword_count: int
    
    # --- SECTOR-SPECIFIC SIGNALS (Polymorphic) ---
    # ENERGY/INFRA (Enron Pattern)
    spe_mentions: int = 0
    mark_to_market_mentions: int = 0
    jv_mentions: int = 0
    
    # TECH/SAAS (Revenue Pattern)
    deferred_revenue_growth: float = 0.0
    stock_based_comp_ratio: float = 0.0
    rd_spend_total: float = 0.0
    
    # GENERAL/RETAIL (Inventory Pattern)
    receivables_current: float = 0.0
    receivables_previous: float = 0.0
    inventory_turnover_delta: float = 0.0

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

class DeterministicForensicEngine:
    """
    Polymorphic Forensic Engine. 
    Selects forensic vectors based on predicted industry.
    """
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
            # ENRON ONTOLOGY: Complexity & Opacity
            complexity = (self.facts.spe_mentions * 2) + self.facts.jv_mentions
            self.metrics['sector_specific_risk'] = min(complexity / 8, 1.0)
            self.metrics['accounting_opacity'] = min(self.facts.mark_to_market_mentions / 5, 1.0)
            
            self.ratios.append({
                "name": "Structural Complexity Index",
                "formula": r"SPEs + JVs",
                "value": f"{complexity}",
                "audit": "High counts of Special Purpose Entities suggest off-balance sheet risk."
            })

        elif "TECH" in industry or "SAAS" in industry:
            # TECH ONTOLOGY: SBC & R&D
            sbc_risk = self.facts.stock_based_comp_ratio
            rd_yield = self.facts.revenue_current / max(self.facts.rd_spend_total, 1)
            self.metrics['sector_specific_risk'] = min(sbc_risk * 5, 1.0)
            self.metrics['accounting_opacity'] = 1.0 if rd_yield < 2.0 else 0.0
            
            self.ratios.append({
                "name": "SBC to Revenue Dilution",
                "formula": r"\frac{StockBasedComp}{Revenue}",
                "value": f"{sbc_risk:.2%}",
                "audit": "High SBC can mask poor operating cash flow."
            })

        else:
            # GENERAL ONTOLOGY: Receivables & Turnover
            rec_rev_curr = self.facts.receivables_current / max(self.facts.revenue_current, 1)
            rec_rev_prev = self.facts.receivables_previous / max(self.facts.revenue_previous, 1)
            delta = rec_rev_curr - rec_rev_prev
            self.metrics['sector_specific_risk'] = min(max(delta * 5, 0), 1.0)
            self.metrics['accounting_opacity'] = min(abs(self.facts.inventory_turnover_delta) / 20, 1.0)

            self.ratios.append({
                "name": "Receivables Drift",
                "formula": r"\Delta \frac{Receivables}{Revenue}",
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
        
        # --- BAYESIAN ARCHETYPE ESCALATOR ---
        # If the symbolic engine detects high sector-specific complexity (e.g., SPEs/JVs > 0.5)
        # or significant accounting opacity, we elevate the score to a baseline warning (55+)
        if self.metrics.get('sector_specific_risk', 0) > 0.5:
            score = max(score, 55.0) # Institutional baseline warning for structural risk
            
        if self.metrics.get('sector_specific_risk', 0) > 0.75 or self.metrics.get('accounting_opacity', 0) > 0.75:
            score = max(score, 75.0) # Elevate to CRITICAL if extreme complexity is found
            
        # --- TEMPORAL OPACITY PENALTY ---
        if self.temporal_gaps_detected:
            self.metrics['integrity_of_disclosures'] = 1.0  # Max penalty for missing records
            score = max(score, 65.0) # Baseline warning for missing data
            
        return min(score, 100.0)

class Citation(BaseModel):
    quote: str
    context: str

def run_forensic_audit(text: str) -> str:
    """
    5-Pass Adaptive Forensic Pipeline:
    -1. INTEGRITY: Pre-flight check for relevance and continuity.
    0. CLASSIFY: Predict sector to select forensic ontology.
    1. EXTRACT: Morph extraction prompt based on sector-specific fraud archetypes.
    2. COMPUTE: Deterministic math on sector-specific ratios.
    3. INTERPRET: Semantic analysis of symbolic findings.
    """
    api_key = get_api_key()
    if not api_key:
        return json.dumps({"error": "GEMMA_API_KEY not found."})

    client = genai.Client(api_key=api_key)
    
    # --- PASS -1: DATA INTEGRITY PRE-FLIGHT ---
    try:
        integrity_resp = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=f"Analyze the following document for forensic integrity:\n\n{text[:30000]}",
            config=types.GenerateContentConfig(
                system_instruction="You are a Forensic Data Integrity Validator. Analyze the text and strictly return the requested JSON schema. IMPORTANT: Subsidiaries, joint ventures, and consolidated entities of the primary filer DO NOT count as multiple companies. Only set single_entity_detected to false if you find financial filings from completely unrelated primary entities (e.g., an Apple 10-K mixed with a Microsoft 10-K).",
                temperature=0,
                response_mime_type="application/json",
                response_schema=DataIntegrity
            )
        )
        integrity = integrity_resp.parsed
        
        if not integrity.is_financial_document:
            return json.dumps({"error": f"Audit Aborted: No valid financial disclosures detected. Reason: {integrity.rejection_reason or 'Irrelevant Document'}"})
        if not integrity.single_entity_detected:
            return json.dumps({"error": f"Audit Aborted: Contamination detected. Multiple entities found: {', '.join(integrity.entities_found)}. Please upload files for a single entity."})
    except Exception as e:
        return json.dumps({"error": f"Integrity Check Failed: {str(e)}"})

    # --- PASS 0: SECTOR CLASSIFICATION ---
    try:
        class_resp = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=f"Classify the target industry for this company (ENERGY, TECH, BANKING, or GENERAL):\n\n{text[:20000]}",
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
    
    extraction_prompt = (
        f"You are a Sector-Specific Forensic Data Extractor for the {sector} industry.\n"
        f"ONTOLOGY HINT: {sector_hints[sector]}\n"
        "Extract raw numeric facts matching the provided schema. Do not calculate. Just extract."
    )
    
    try:
        extract_resp = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=f"Perform forensic extraction on these {sector} records:\n\n{text[:100000]}",
            config=types.GenerateContentConfig(
                system_instruction=extraction_prompt,
                temperature=0,
                response_mime_type="application/json",
                response_schema=FinancialFacts
            )
        )
        facts = extract_resp.parsed
        facts.predicted_industry = sector # Ensure override
    except Exception as e:
        return json.dumps({"error": f"Extraction Error: {str(e)}"})

    # --- PASS 2: DETERMINISTIC COMPUTATION ---
    engine = DeterministicForensicEngine(facts, integrity.temporal_gaps_detected)
    risk_score = engine.compute()
    metrics = engine.metrics
    risk_level = "CRITICAL" if risk_score > 70 else "WARNING" if risk_score > 30 else "STABLE"

    # --- PASS 3: CONSTRAINED INTERPRETATION ---
    # Centered on a single "Objective but Highly Skeptical Forensic Specialist" persona
    persona_system_instruction = (
        "ROLE: You are an Elite Forensic Accounting Investigator. "
        "PHILOSOPHY: You are highly objective, meticulously evidence-driven, but deeply skeptical of management narrative. "
        "Your mission is to uncover corporate double-speak and map numbers to known historical fraud archetypes. "
        "TONE: Cynical, sharp, objective, and professional."
    )

    interpretation_prompt = (
        f"{persona_system_instruction}\n\n"
        f"Interpret the following results for {facts.company_name} in the {sector} sector.\n\n"
        f"FRAUD RISK SCORE: {risk_score:.2f}/100\n"
        f"METRICS: {json.dumps(metrics)}\n"
        f"RATIOS: {json.dumps(engine.ratios)}\n\n"
        "IMPORTANT RULES:\n"
        "1. archetype_match: Provide ONLY a 2-4 word name (e.g., 'Off-Balance Sheet Vehicle'). Do NOT write a full sentence.\n"
        "2. next_steps: Write these explicitly for a regular retail investor (layman). Tell them exactly what to do next. Provide actionable search queries (e.g., 'Search SEC EDGAR for Form 8-K...') and tell them which specific documents to upload next to confirm the risks."
    )

    try:
        report_resp = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=f"Analyze these forensic results:\n\n{text[:80000]}",
            config=types.GenerateContentConfig(
                system_instruction=interpretation_prompt,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=ForensicAuditReport,
                thinking_config=types.ThinkingConfig(thinking_level="high")
            )
        )
        
        thought_process = ""
        if report_resp.candidates:
            for part in report_resp.candidates[0].content.parts:
                if getattr(part, 'thought', False):
                    thought_process += part.text + "\n"

        result = report_resp.parsed
        citation_str = "\n".join([f"- \"{c.quote}\"\n  [Context: {c.context}]" for c in result.citations])

        if integrity.filing_years:
            years_str = f"{min(integrity.filing_years)} to {max(integrity.filing_years)}" if len(integrity.filing_years) > 1 else str(integrity.filing_years[0])
        else:
            years_str = "Unknown Years"
        upload_context = f"{', '.join(integrity.entities_found)} Financial Filings ({years_str})"

        report_data = {
            "upload_context": upload_context,
            "score": f"{risk_score:.2f}",
            "level": risk_level,
            "metrics": metrics,
            "industry": sector,
            "summary": result.executive_summary,
            "summary_layman": result.executive_summary_layman,
            "drift": result.narrative_drift_analysis,
            "drift_layman": result.narrative_drift_layman,
            "ratios": engine.ratios,
            "citations": citation_str,
            "expert": result.forensic_analysis_expert,
            "expert_layman": result.forensic_analysis_layman,
            "archetype": result.archetype_match,
            "next_steps": "\n".join([f"{i+1}. {s}" for i, s in enumerate(result.next_steps)]),
            "thought_trace": thought_process if thought_process else "Reasoning trace captured natively."
        }

        return f"=== SHADOW_AUDITOR_RESULT ===\n{json.dumps(report_data)}\n=== END_RESULT ==="

    except Exception as e:
        return f"Interpretation Error: {str(e)}"

def data_to_list(data):
    if isinstance(data, list):
        return "\n".join([f"{i+1}. {s}" for i, s in enumerate(data)])
    return str(data)

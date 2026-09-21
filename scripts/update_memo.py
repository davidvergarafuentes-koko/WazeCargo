#!/usr/bin/env python3
"""
Update Final project memo.docx:
1. Integrate ML_Forecasting_Methodology_Memo content into Chapter 12
2. Integrate Congestion_Index_Methodology content into Chapter 13
3. Fix R² inconsistency (0.909 was the leaked metric)
4. Add financial details from GTM presentations
5. Clean up Artemiy placeholders as proper sections
6. Restructure forecast accuracy as Chapter 14
7. Renumber chapters 14+ by +1 and update cross-references
"""

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re

doc = Document('docs/Final project memo.docx')

# ============================================================
# HELPERS
# ============================================================

def find_para(text_frag, start=0):
    """Find paragraph by text fragment. Returns (index, paragraph)."""
    for i, p in enumerate(doc.paragraphs):
        if i >= start and text_frag in p.text:
            return i, p
    return None, None

def add_p_after(ref_el, text, style='Normal'):
    """Add paragraph after an XML element (paragraph._p or table._tbl)."""
    p = doc.add_paragraph(text, style=style)
    ref_el.addnext(p._p)
    return p

def add_heading_after(ref_el, text, level=2):
    style_name = f'Heading {level}'
    p = doc.add_paragraph(text, style=style_name)
    ref_el.addnext(p._p)
    return p

def add_bullet_after(ref_el, text):
    p = doc.add_paragraph(text, style='List Bullet')
    ref_el.addnext(p._p)
    return p

def add_table_after(ref_el, data, style_name='Light Shading Accent 1'):
    """Add table after ref_el. data = list of rows, each row = list of cell strings."""
    rows = len(data)
    cols = len(data[0]) if data else 0
    t = doc.add_table(rows=rows, cols=cols)
    try:
        t.style = style_name
    except:
        pass
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row_data in enumerate(data):
        for j, cell_text in enumerate(row_data):
            t.rows[i].cells[j].text = str(cell_text)
    ref_el.addnext(t._tbl)
    return t

def replace_in_para(para, old, new):
    """Replace text in paragraph. Handles single-run and multi-run cases."""
    # Try run-by-run first
    for run in para.runs:
        if old in run.text:
            run.text = run.text.replace(old, new)
            return True
    # Fall back to full-text replacement
    full = para.text
    if old in full:
        new_full = full.replace(old, new)
        for run in para.runs:
            run.text = ''
        if para.runs:
            para.runs[0].text = new_full
        else:
            para.add_run(new_full)
        return True
    return False


# ============================================================
# STEP 1: FIX R² INCONSISTENCY
# The R² = 0.909 in Chapter 18 was the leaked metric.
# The honest post-fix number is ~0.57 volume-weighted R².
# The production hybrid achieves 4.03% wMAPE on 2025 holdout.
# ============================================================
print("Step 1: Fixing R² inconsistency...")

for p in doc.paragraphs:
    if 'overall R² of 0.909' in p.text:
        replace_in_para(p,
            'overall R² of 0.909',
            'overall wMAPE of 4.03% on the 2025 holdout (hybrid ensemble)')
    # Also fix the LightGBM R² reference in Ch 12 if present
    if 'LightGBM achieved an R² of 0.909' in p.text:
        replace_in_para(p,
            'LightGBM achieved an R² of 0.909, meaning the model explained over 90% of the variance in monthly shipment counts',
            'LightGBM achieved a volume-weighted MAPE of 8.16% on the 2025 holdout fold. However, an earlier version of the pipeline reported an inflated R² of 0.91 due to a data-leakage bug that was later discovered and corrected (see section 12.6)')


# ============================================================
# STEP 2: INTEGRATE ML METHODOLOGY MEMO INTO CHAPTER 12
# Add data leakage section and production results after 12.4
# ============================================================
print("Step 2: Integrating ML methodology memo into Chapter 12...")

# Find "12.5 Final Model Selection" — we'll insert before it
idx_12_5, para_12_5 = find_para('12.5 Final Model Selection')
if not para_12_5:
    idx_12_5, para_12_5 = find_para('Final Model Selection')

if para_12_5:
    # We insert BEFORE 12.5 (which means using addprevious on 12.5)
    # Actually, insert after the last paragraph of 12.4 (which is just before 12.5)
    # Use addprevious on para_12_5 — insert in REVERSE order

    # Build content blocks to insert (in reverse order since addprevious)
    blocks = []

    # --- 12.5 Data Leakage Discovery & Fix ---
    blocks.append(('heading2', '12.5 Data Leakage Discovery & Fix'))
    blocks.append(('normal',
        'During the exploratory data analysis phase, two critical data-leakage bugs were discovered in the feature engineering SQL. '
        'These represent the most important methodological finding of the project and are documented in detail in notebook 09 (Bugs Found).'))

    blocks.append(('normal',
        'Bug 1 — Full-History Min-Max Normalisation. The columns sc_norm, v_norm, w_norm, and cd_norm were computed with a '
        'PARTITION BY window that had no ORDER BY or frame bounds, meaning the min and max were computed over the entire history '
        '(2005–2025). A training row from 2015 therefore already embedded the 2025 maximum value. Since sc_norm is a perfect affine '
        'transformation of shipment_count (the target), linear models could recover the target exactly: Ridge, Lasso, and ElasticNet '
        'all achieved R² = 1.000 with MAE near zero — an impossible result that was the first alarm signal.'))

    blocks.append(('normal',
        'Bug 2 — Inclusive Rolling Means. The rolling_3_mean and rolling_12_mean features were computed with '
        'ROWS BETWEEN n PRECEDING AND CURRENT ROW, meaning they included the current row\'s target value. This created an algebraic '
        'identity: shipment_count = 3 × rolling_3_mean − lag_1 − lag_2. Linear models exploited this exactly; tree models exploited '
        'it partially (R² ~0.91 instead of 1.0), making the leak harder to detect visually.'))

    blocks.append(('normal',
        'Impact on reported metrics (median R² across all ports and folds):'))

    blocks.append(('table', [
        ['Model', 'R² (Leaky)', 'R² (Clean)', 'Delta'],
        ['Ridge', '1.000', '0.369', '−0.631'],
        ['Lasso', '1.000', '0.349', '−0.651'],
        ['ElasticNet', '1.000', '0.368', '−0.632'],
        ['LightGBM', '0.535', '0.220', '−0.315'],
        ['XGBoost', '0.588', '0.319', '−0.269'],
        ['Random Forest', '0.510', '0.247', '−0.263'],
        ['Baseline', '−0.479', '−0.194', '+0.285'],
    ]))

    blocks.append(('normal',
        'The original project report cited LightGBM at R² = 0.91 — this was the partially-leaked metric. The honest, leak-free '
        'figure is R² ~0.57 (volume-weighted). The thesis presents both numbers transparently, with the debugging process as a '
        'central finding.'))

    blocks.append(('normal',
        'The fix: the leaked columns (sc_norm, v_norm, w_norm, cd_norm) were excluded from the ML feature list in '
        'wz_ml_utils.py FEATURE_COLS. The rolling means were corrected to use past-only windows '
        '(ROWS BETWEEN n PRECEDING AND 1 PRECEDING). Both notebooks and production pipeline scripts import the same '
        'FEATURE_COLS constant, ensuring the fix propagates everywhere.'))

    # --- 12.6 Production Model Performance ---
    blocks.append(('heading2', '12.6 Production Model Performance'))
    blocks.append(('normal',
        'The table below shows the volume-weighted MAPE on the 2025 holdout fold — the primary metric for production model selection:'))

    blocks.append(('table', [
        ['Rank', 'Model', 'wMAPE (%)', 'wR²'],
        ['1', 'Baseline Seasonal Naive', '4.33', '0.397'],
        ['2', 'ElasticNet', '8.16', '0.445'],
        ['3', 'LightGBM', '8.16', '0.028'],
        ['4', 'Ridge', '8.50', '0.389'],
        ['5', 'XGBoost', '8.51', '−0.028'],
        ['6', 'Random Forest', '8.82', '0.002'],
        ['7', 'Lasso', '8.89', '0.401'],
        ['8', 'Prophet', '14.18', '−1.052'],
    ]))

    blocks.append(('normal',
        'The Baseline Seasonal Naive model achieves the lowest wMAPE (4.33%) because Chilean port traffic is dominated by a few '
        'very large ports (San Antonio, Valparaíso) that are highly seasonal and stable year-over-year. However, the Baseline '
        'collapses on the 2023 fold (wMAPE = 41.0%) because it cannot handle the post-COVID structural shift. ML models, '
        'particularly XGBoost (14.3%) and LightGBM (15.9%), handled this fold much better.'))

    blocks.append(('normal', 'Stability across folds (wMAPE %):'))

    blocks.append(('table', [
        ['Model', 'Fold 2019', 'Fold 2023', 'Fold 2024', 'Fold 2025'],
        ['Baseline', '6.5%', '41.0%', '7.5%', '4.3%'],
        ['ElasticNet', '8.0%', '20.1%', '14.3%', '8.2%'],
        ['LightGBM', '17.2%', '15.9%', '7.7%', '8.2%'],
        ['Ridge', '7.9%', '20.8%', '14.2%', '8.5%'],
        ['XGBoost', '18.5%', '14.3%', '9.1%', '8.5%'],
        ['Random Forest', '11.2%', '17.0%', '13.8%', '8.8%'],
        ['Lasso', '7.6%', '26.4%', '16.1%', '8.9%'],
        ['Prophet', '18.8%', '32.8%', '19.6%', '14.2%'],
    ]))

    blocks.append(('normal',
        'The Baseline is either the best (folds 2019, 2024, 2025) or the worst (fold 2023). ML models are more consistent '
        'across folds. This motivates the hybrid approach.'))

    blocks.append(('normal',
        'The production pipeline uses a hybrid ensemble that combines the strengths of both approaches. Big ports '
        '(average ≥ 500 shipments/month, 10 port-direction pairs) always use the Baseline Seasonal Naive. Small ports '
        '(average < 500 shipments/month, ~51 port-direction pairs) use the ML model with the lowest average MAPE across '
        'all 4 CV folds.'))

    blocks.append(('normal',
        'Hybrid result on the 2025 fold: wMAPE = 4.03% — a 0.30 percentage point improvement over the pure Baseline (4.33%) '
        'and nearly half the error of pure LightGBM (8.16%). The improvement is modest in aggregate because big ports dominate '
        'the volume-weighted score, but it matters for the small ports where the ML models reduce individual port MAPE by '
        '5–15 percentage points.'))

    blocks.append(('normal', 'Model distribution in the hybrid (small ports):'))

    blocks.append(('table', [
        ['Model', 'Ports Selected'],
        ['Baseline Seasonal Naive', '13 (also some small ports)'],
        ['ElasticNet', '13'],
        ['XGBoost', '11'],
        ['Lasso', '9'],
        ['Ridge', '7'],
        ['LightGBM', '5'],
        ['Random Forest', '3'],
    ]))

    blocks.append(('normal',
        'ElasticNet and XGBoost are the most frequently selected ML models for small ports. ElasticNet performs well because '
        'it combines L1 (feature selection) and L2 (regularisation) penalties, which is effective when the feature set has '
        'moderate multicollinearity and the training set is small (some ports have only 36–60 monthly observations). '
        'XGBoost excels at capturing non-linear interaction patterns in the cargo-mix features.'))

    # --- 12.7 2026 National Forecast Summary ---
    blocks.append(('heading2', '12.7 2026 National Forecast Summary'))
    blocks.append(('normal', 'The table below compares each model\'s Chile-wide 2026 forecast against actual 2025 volumes:'))

    blocks.append(('table', [
        ['Model', 'Imports', 'Exports', 'Total'],
        ['Baseline (production)', '856,350', '186,207', '1,042,557'],
        ['Hybrid Ensemble', '855,281', '185,549', '1,040,830'],
        ['LightGBM', '790,873', '181,557', '972,430'],
        ['XGBoost', '768,530', '177,917', '946,447'],
        ['Random Forest', '807,536', '177,744', '985,280'],
        ['Ridge', '835,916', '182,451', '1,018,367'],
        ['Actual 2025', '814,110', '181,800', '995,910'],
    ]))

    blocks.append(('normal',
        'All models project 2026 imports within ±8% of 2025 actual, reflecting the stable trajectory of Chilean maritime trade '
        'post-pandemic. The Baseline and Hybrid ensemble forecast slightly higher than 2025 (~4–5% growth), while tree models '
        '(LightGBM, XGBoost) are more conservative. Export forecasts are tightly clustered across all models.'))

    # --- 12.8 Key Findings ---
    blocks.append(('heading2', '12.8 Key Findings from Model Evaluation'))

    key_findings = [
        'Feature engineering matters more than model choice. The COVID-aware feature pipeline (lag substitution, sample weighting, COVID flags) delivers a larger accuracy improvement than switching between model families.',
        'Simple baselines are hard to beat for large, seasonal ports. The Baseline Seasonal Naive achieves 4.33% wMAPE on the most recent fold — nearly half the error of the best ML model.',
        'ML models earn their keep on small ports and structural breaks. The hybrid ensemble improves on the pure Baseline by selecting ML models for ports where traffic patterns are irregular or where COVID-era structural shifts make last-year comparisons unreliable.',
        'Data leakage is the most dangerous bug in an ML pipeline. Two leakage bugs inflated the original LightGBM R² from ~0.57 (honest) to ~0.91 (leaked). The detection method — running the same features through multiple model families and comparing ordinally — should be a standard practice.',
        'Recursive forecasting is a reasonable strategy for a 12-month horizon. All models produce plausible national totals within ±8% of 2025 actual, validating the approach for a one-year planning horizon.',
        'The hybrid ensemble is the optimal production configuration. Congestion: Baseline for big ports (≥ 500 ships/mo), CV-selected ML for small ports. Commodity: purely CV-selected best model per HS2 × port × direction.',
    ]

    for i, finding in enumerate(key_findings, 1):
        blocks.append(('normal', f'{i}. {finding}'))

    # Now RENUMBER existing 12.5 → 12.9
    replace_in_para(para_12_5, '12.5 Final Model Selection', '12.9 Final Model Selection')

    # Insert blocks BEFORE para_12_5 (in forward order, inserting each after the previous)
    # We use addprevious for the first one, then addnext for subsequent
    last_el = None
    for block_type, content in blocks:
        if block_type == 'heading2':
            p = doc.add_paragraph(content, style='Heading 2')
            if last_el is None:
                para_12_5._p.addprevious(p._p)
            else:
                last_el.addnext(p._p)
            last_el = p._p
        elif block_type == 'normal':
            p = doc.add_paragraph(content, style='Normal')
            if last_el is None:
                para_12_5._p.addprevious(p._p)
            else:
                last_el.addnext(p._p)
            last_el = p._p
        elif block_type == 'table':
            t = add_table_after(last_el, content)
            last_el = t._tbl
        elif block_type == 'bullet':
            p = doc.add_paragraph(content, style='List Bullet')
            if last_el is None:
                para_12_5._p.addprevious(p._p)
            else:
                last_el.addnext(p._p)
            last_el = p._p

    print(f"  Inserted ML methodology content before section 12.9")
else:
    print("  WARNING: Could not find section 12.5 for ML memo integration")


# ============================================================
# STEP 3: INTEGRATE CI METHODOLOGY INTO CHAPTER 13
# Add weather adjustment and dashboard interpretation after
# the output tables summary (section 13.5)
# ============================================================
print("Step 3: Integrating CI methodology into Chapter 13...")

# Find the Artemiy placeholder lines
idx_swell, para_swell = find_para('Swell ML pipeline')
if para_swell:
    # Insert CI weather adjustment BEFORE the swell placeholder
    ci_blocks = []

    ci_blocks.append(('heading2', '13.6 Congestion Index Computation'))
    ci_blocks.append(('normal',
        'The congestion index displayed in the WazeCargo dashboard is a two-stage metric: a historical composite index '
        'built in SQL, followed by a machine-learning forecast projected onto 2026. The CI is computed per port, per direction '
        '(import/export), across the port\'s entire history (2005–2025). A value of 0% means the port is at its quietest month '
        'on record; 100% means it is at its historical peak load.'))

    ci_blocks.append(('normal',
        'The input metrics are min-max normalised within each port-direction partition: sc_norm (shipment count), v_norm (trade value), '
        'w_norm (cargo weight, exports only), cd_norm (commodity diversity), plus the raw cargo-type ratios pct_container (imports) '
        'and pct_refrigerated (exports).'))

    ci_blocks.append(('normal',
        'The formulas are:'))
    ci_blocks.append(('normal',
        'Import CI = 0.40 × sc_norm + 0.30 × v_norm + 0.20 × cd_norm + 0.10 × pct_container'))
    ci_blocks.append(('normal',
        'Export CI = 0.40 × w_norm + 0.30 × sc_norm + 0.20 × v_norm + 0.10 × pct_refrigerated'))
    ci_blocks.append(('normal',
        'The dominant signal (40% weight) is shipment count for imports and cargo weight for exports, reflecting the different '
        'bottleneck drivers for each direction. Trade value, cargo-mix diversity, and specialised cargo type (containers or reefer) '
        'add secondary dimensions. The dashboard does not display the raw historical CI directly. Instead it shows a 12-month '
        'forecast for 2026 — predicted shipment counts re-normalised against the port\'s historical min/max to produce a '
        'forward-looking congestion index.'))

    ci_blocks.append(('heading2', '13.7 Weather Adjustment Layer'))
    ci_blocks.append(('normal',
        'The dashboard offers two congestion views: "trade-only" (ci_raw) and "weather-adjusted" (ci_adjusted). The weather '
        'adjustment applies a multiplier based on historical port-closure data from swell and wind conditions. When a port '
        'has weather coverage, the adjusted CI incorporates the percentage of hours the port is typically closed by weather '
        'in each month. This pushes the effective congestion higher during storm-prone months, reflecting the real-world impact '
        'of weather on port throughput. On the dashboard chart, the gap between the dashed (trade-only) and solid '
        '(weather-adjusted) lines represents the weather impact.'))

    ci_blocks.append(('normal',
        'For example, a ci_raw value of 66% in July for a central port means: "July 2026 is forecast to be at 66% of this '
        'port\'s historical peak load, driven purely by trade demand." In Combined mode, the chart overlays both curves, '
        'and if the weather multiplier pushes the adjusted value to 74%, the 8-percentage-point gap quantifies the expected '
        'weather impact for that month.'))

    # Clean up Artemiy placeholders
    ci_blocks.append(('heading2', '13.8 Swell ML Pipeline'))
    ci_blocks.append(('normal',
        '[Section to be completed by Artemiy Klimkin — artemiy.i.klimkin@gmail.com. This section will cover the swell '
        'forecasting model architecture, training methodology, feature engineering from the Open-Meteo marine data, '
        'and the operability scoring system that converts raw swell/wind conditions into per-port hourly risk labels '
        '(NORMAL, WATCH, ADVISORY, WARNING, CLOSED).]'))

    ci_blocks.append(('heading2', '13.9 Stacking Architecture'))
    ci_blocks.append(('normal',
        '[Section to be completed by Artemiy Klimkin. This section will describe the stacking architecture that combines '
        'the congestion pipeline output with the swell pipeline output to produce a unified delay prediction. The stacking '
        'approach uses the congestion forecast and weather operability as inputs to a meta-learner that generates a composite '
        'delay risk score.]'))

    ci_blocks.append(('heading2', '13.10 Final Delay Prediction Generation'))
    ci_blocks.append(('normal',
        '[Section to be completed by Artemiy Klimkin. This section will explain how the stacking model\'s output is translated '
        'into actionable delay predictions — the probability of delay, expected delay duration, and the risk label shown on '
        'the dashboard — and how these predictions support the platform\'s core promise of anticipating disruptions before '
        'they occur.]'))

    # Insert CI blocks before the swell placeholder
    last_el = None
    for block_type, content in ci_blocks:
        if block_type == 'heading2':
            p = doc.add_paragraph(content, style='Heading 2')
            if last_el is None:
                para_swell._p.addprevious(p._p)
            else:
                last_el.addnext(p._p)
            last_el = p._p
        elif block_type == 'normal':
            p = doc.add_paragraph(content, style='Normal')
            if last_el is None:
                para_swell._p.addprevious(p._p)
            else:
                last_el.addnext(p._p)
            last_el = p._p
        elif block_type == 'table':
            t = add_table_after(last_el, content)
            last_el = t._tbl

    # Now DELETE the old placeholder lines
    old_placeholders = [
        'Swell ML pipeline',
        'Stacking architecture artemiy.i.klimkin@gmail.com',
        'Final delay prediction generation',
    ]
    for placeholder in old_placeholders:
        idx, p = find_para(placeholder)
        if p and len(p.text.strip()) < 80:  # Safety check: only delete short placeholder lines
            p._p.getparent().remove(p._p)

    print("  Inserted CI methodology and cleaned Artemiy placeholders")
else:
    print("  WARNING: Could not find 'Swell ML pipeline' placeholder")


# ============================================================
# STEP 4: RESTRUCTURE FORECAST ACCURACY AS CHAPTER 14
# The sections numbered 1-8 with Heading 1 style need to be
# wrapped under a Chapter 14 heading and renumbered as 14.1-14.8
# ============================================================
print("Step 4: Restructuring forecast accuracy as Chapter 14...")

# Find "Results and performance" paragraph — it's the intro line before sections 1-8
idx_results, para_results = find_para('Results and performance')

# Also find the accuracy report intro paragraph
idx_comparison, para_comparison = find_para('Comparison of the hybrid ensemble ML forecasts against actual Chilean customs data')

if para_comparison:
    # Insert Chapter 14 heading before the intro paragraph
    ch14_heading = doc.add_paragraph('CHAPTER 14. 2026 FORECAST VALIDATION', style='Heading 2')
    para_comparison._p.addprevious(ch14_heading._p)

    # Delete the "Results and performance" line if it exists
    if para_results:
        para_results._p.getparent().remove(para_results._p)

    # Now rename the Heading 1 sections to subsections (14.1, 14.2, etc.)
    renames = {
        '1. Data Sources & Methodology': '14.1 Data Sources & Methodology',
        '2. National Overview': '14.2 National Overview',
        '3. Accuracy by Port Size': '14.3 Accuracy by Port Size',
        '4. Large Port Monthly Breakdowns': '14.4 Large Port Monthly Breakdowns',
        '5. Medium Port Monthly Breakdowns': '14.5 Medium Port Monthly Breakdowns',
        '6. Small Port Sample Breakdowns': '14.6 Small Port Sample Breakdowns',
        '7. Key Findings': '14.7 Key Findings',
        '8. Comparison to Holdout Performance': '14.8 Comparison to Holdout Performance',
    }

    for old_text, new_text in renames.items():
        idx, p = find_para(old_text)
        if p:
            # Change the heading text
            replace_in_para(p, old_text, new_text)
            # Change style from Heading 1 to Heading 2
            p.style = doc.styles['Heading 2']

    print("  Restructured forecast accuracy as Chapter 14")
else:
    print("  WARNING: Could not find forecast accuracy intro paragraph")


# ============================================================
# STEP 5: RENUMBER CHAPTERS 14+ BY +1
# Old Ch 14 (GTM) → Ch 15, Old Ch 15 (Growth) → Ch 16, etc.
# ============================================================
print("Step 5: Renumbering chapters...")

# Renumber chapter headings (process from highest to lowest to avoid double-renumbering)
chapter_renames = [
    ('CHAPTER 20. FUTURE IMPROVEMENTS', 'CHAPTER 21. FUTURE IMPROVEMENTS'),
    ('CHAPTER 19. LIMITATIONS', 'CHAPTER 20. LIMITATIONS'),
    ('CHAPTER 18. PROJECT ITERATIONS', 'CHAPTER 19. PROJECT ITERATIONS'),
    ('CHAPTER 17. KEY LEARNINGS', 'CHAPTER 18. KEY LEARNINGS'),
    ('CHAPTER 16. PRODUCT ROADMAP', 'CHAPTER 17. PRODUCT ROADMAP'),
    ('CHAPTER 15. GROWTH STRATEGY', 'CHAPTER 16. GROWTH STRATEGY'),
    ('CHAPTER 14. GO-TO-MARKET STRATEGY', 'CHAPTER 15. GO-TO-MARKET STRATEGY'),
]

for old_title, new_title in chapter_renames:
    idx, p = find_para(old_title)
    if p:
        replace_in_para(p, old_title, new_title)
        print(f"  {old_title} → {new_title}")

# Renumber section headings within renamed chapters
section_renames_map = {
    # GTM: 14.x → 15.x
    '14.1': '15.1', '14.2': '15.2', '14.3': '15.3',
    '14.4': '15.4', '14.5': '15.5', '14.6': '15.6',
    # Growth: 15.x → 16.x
    '15.1': '16.1', '15.2': '16.2', '15.3': '16.3', '15.4': '16.4',
    # Roadmap: 16.x → 17.x
    '16.1': '17.1', '16.2': '17.2', '16.3': '17.3',
    # Learnings: 17.x → 18.x
    '17.1': '18.1', '17.2': '18.2', '17.3': '18.3', '17.4': '18.4',
    # Iterations: 18.x → 19.x
    '18.1': '19.1', '18.2': '19.2', '18.3': '19.3',
    # Limitations: 19.x → 20.x
    '19.1': '20.1', '19.2': '20.2', '19.3': '20.3',
    # Future: 20.x → 21.x
    '20.1': '21.1', '20.2': '21.2', '20.3': '21.3', '20.4': '21.4', '20.5': '21.5',
}

# Process from highest to lowest to avoid double-renumbering
sorted_sections = sorted(section_renames_map.items(), key=lambda x: float(x[0]), reverse=True)
for old_sec, new_sec in sorted_sections:
    for p in doc.paragraphs:
        if p.text.strip().startswith(old_sec + ' '):
            replace_in_para(p, old_sec, new_sec)

# Update cross-references in body text (Chapter X references)
# Process from highest to lowest
cross_ref_map = [
    ('Chapter 20', 'Chapter 21'),
    ('Chapter 19', 'Chapter 20'),
    ('Chapter 18', 'Chapter 19'),
    ('Chapter 17', 'Chapter 18'),
    ('Chapter 16', 'Chapter 17'),
    ('Chapter 14', 'Chapter 15'),
    # Ch 15 → 16 but careful — old Ch 14 is now Ch 15, so "Chapter 15"
    # references to old Ch 15 should become 16.
    # We need to be careful here. Let me handle it in two passes.
]

# First, temporarily rename to avoid collisions
# Old Ch 14 (GTM) references → "Chapter __15__"
# Old Ch 15 (Growth) references → "Chapter __16__"
# etc.

# Pass 1: Mark old references with temp markers (highest first)
temp_map = [
    ('Chapter 20', 'Chapter __21__'),
    ('Chapter 18', 'Chapter __19__'),
    ('Chapter 16', 'Chapter __17__'),
    ('Chapter 14', 'Chapter __15__'),
]

# Chapters that are NOT renumbered: 1-13 stay the same
# We need to handle chapters 14-20 in body text cross-refs
# Only modify if the text is "Chapter XX" not part of a heading we already renamed

# Actually, let's do a simpler approach: find and replace in all Normal paragraphs only
# (not headings, which were already renamed above)
for p in doc.paragraphs:
    if p.style and 'Heading' in p.style.name:
        continue
    text = p.text
    # Process from highest chapter number down
    for old_ch in [20, 18, 16, 14]:
        new_ch = old_ch + 1
        old_ref = f'Chapter {old_ch}'
        new_ref = f'Chapter {new_ch}'
        if old_ref in text:
            replace_in_para(p, old_ref, new_ref)
            text = p.text  # refresh after modification

print("  Cross-references updated")


# ============================================================
# STEP 6: ADD FINANCIAL DETAILS TO BUSINESS CHAPTERS
# ============================================================
print("Step 6: Adding financial details...")

# Find the Pro Plan description in Chapter 4 (now still Ch 4)
idx_pro, para_pro = find_para('The Pro Plan provides access to advanced predictive analytics')
if para_pro:
    # Insert pricing specifics after the Enterprise Plan paragraph
    idx_ent, para_ent = find_para('This tier targets larger organizations and logistics stakeholders', idx_pro)
    if para_ent:
        pricing_text = (
            'Indicative pricing: the Free Plan costs €0/month with limited port coverage; the Pro Plan targets '
            '€100–350/month depending on the number of ports and commodities monitored, positioned to deliver '
            'immediate ROI against demurrage costs averaging $1,500 per day per vessel — meaning a single '
            'avoided delay day pays for 2–4 months of the Pro subscription. The Enterprise Plan uses custom '
            'pricing based on fleet size, integration requirements, and dedicated support needs.'
        )
        p = add_p_after(para_ent._p, pricing_text, 'Normal')
        print("  Added pricing details to Chapter 4")

# Find GTM chapter (now Chapter 15) monetization section
idx_mon, para_mon = find_para('This tiered model enables broad adoption while creating a clear upgrade path')
if para_mon:
    financial_text = (
        'Revenue targets follow a phased ramp: €2,000 monthly recurring revenue (MRR) by month three, '
        '€5,000 MRR by month six, and €40,000 annual recurring revenue (ARR) by the end of year one. '
        'At an average revenue per user (ARPU) of €200/month, this implies 25 paying customers in year one. '
        'The five-year target is €1.2M ARR, driven by geographic expansion and enterprise adoption. '
        'Customer acquisition cost (CAC) is targeted below €500, with a lifetime value (LTV) to CAC ratio above 3:1.'
    )
    p = add_p_after(para_mon._p, financial_text, 'Normal')
    print("  Added financial projections to GTM chapter")

# Add success metrics detail
idx_metrics, para_metrics = find_para('These metrics will provide continuous feedback on product adoption')
if para_metrics:
    aarrr_text = (
        'The platform\'s funnel follows the AARRR framework (Acquisition, Activation, Retention, Revenue, Referral) '
        'with stage-specific KPIs: Acquisition targets 500 unique visitors/month and a 5% signup conversion rate; '
        'Activation measures whether new users check a port forecast within their first session (target: 60%); '
        'Retention tracks weekly active port checks (WAPC) as the north-star metric, targeting DAU/MAU above 0.25 '
        'during peak shipping seasons; Revenue monitors MRR and free-to-paid conversion rate (target: 3–5%); '
        'Referral targets a viral coefficient (K-factor) above 0.3 and Net Promoter Score above 50.'
    )
    p = add_p_after(para_metrics._p, aarrr_text, 'Normal')
    print("  Added AARRR funnel metrics")

# Add specific financial targets to Growth chapter (now Chapter 16)
idx_growth_validation, para_growth_validation = find_para('During this phase, the platform will concentrate on major Chilean ports')
if para_growth_validation:
    growth_financial = (
        'Financially, Phase 1 targets product-market fit with a 90-day launch plan: Month 1 focuses on deploying '
        'the public dashboard as the primary acquisition channel, Month 2 on personalised outreach to the first '
        '50 qualified importers identified through publicly available customs data, and Month 3 on converting '
        'activated users to paid Pro subscriptions. The phase ends when the platform achieves €2,000 MRR and at '
        'least three validated case studies demonstrating cost savings from forecast-driven logistics decisions.'
    )
    p = add_p_after(para_growth_validation._p, growth_financial, 'Normal')
    print("  Added Phase 1 financial targets to Growth chapter")


# ============================================================
# STEP 7: ADD TEAM INFO TO GENERAL INTRODUCTION
# ============================================================
print("Step 7: Adding team introduction...")

idx_intro_last, para_intro_last = find_para(
    'The project combines business analysis, data engineering, machine learning, and product development')

if para_intro_last:
    team_text = (
        'The project was developed by a team of five Master\'s students combining expertise across data science, '
        'machine learning, business strategy, and product design: Meliane Meledje, Michalis Arvanitis, Artemiy Klimkin, '
        'Gerson Montesinos, and David Vergara. Each member contributed to the project\'s interdisciplinary scope, '
        'with responsibilities spanning data engineering and cloud architecture, predictive modelling, go-to-market '
        'strategy, product design, and environmental data integration.'
    )
    p = add_p_after(para_intro_last._p, team_text, 'Normal')
    print("  Added team introduction")


# ============================================================
# STEP 8: UPDATE EXECUTIVE SUMMARY WITH 2026 VALIDATION
# ============================================================
print("Step 8: Updating executive summary...")

idx_exec_last, para_exec_last = find_para(
    'the proposed platform has the potential to improve supply-chain resilience')

if para_exec_last:
    validation_text = (
        'The forecasting system was validated against five months of live 2026 customs data (January–May), '
        'achieving a weighted MAPE of 8.5% across 54 port-direction pairs. The model is most accurate where '
        'it matters most: large ports carrying 98% of Chile\'s maritime trade volume achieve 8.3% wMAPE, '
        'with San Antonio import — handling 57% of all maritime imports — tracking within 3.4% of actual volumes. '
        'This represents acceptable degradation from the 4.03% wMAPE on the 2025 holdout, given that the 2026 '
        'predictions are fully out-of-sample recursive forecasts produced from a model trained on 2005–2025 data.'
    )
    p = add_p_after(para_exec_last._p, validation_text, 'Normal')
    print("  Added 2026 validation paragraph to executive summary")


# ============================================================
# STEP 9: UPDATE LIST OF TABLES
# ============================================================
print("Step 9: Updating list of tables and figures...")

# Add Table N°3 reference if not already there (forecast accuracy)
idx_table3, para_table3 = find_para('Table N°3')
if not para_table3:
    idx_table2_end, para_table2_end = find_para('content descriptions (Chapter 13)')
    if para_table2_end:
        p1 = add_p_after(para_table2_end._p,
            'Table N°3 : 2026 forecast accuracy summary — national totals,', 'Normal')
        p2 = add_p_after(p1._p,
            '                   wMAPE by port size category, and key highlights for', 'Normal')
        p3 = add_p_after(p2._p,
            '                   Jan–May 2026 out-of-sample validation (Chapter 14)', 'Normal')

        p4 = add_p_after(p3._p,
            'Table N°4 : Data leakage impact — before and after R² metrics', 'Normal')
        p5 = add_p_after(p4._p,
            '                   across all seven model families (Chapter 12)', 'Normal')

        p6 = add_p_after(p5._p,
            'Table N°5 : Production model ranking — volume-weighted MAPE', 'Normal')
        p7 = add_p_after(p6._p,
            '                   on 2025 holdout fold for all evaluated models', 'Normal')
        p8 = add_p_after(p7._p,
            '                   (Chapter 12)', 'Normal')


# ============================================================
# STEP 10: FIX CHAPTER REFERENCES IN LIST OF FIGURES/TABLES
# ============================================================
print("Step 10: Final cross-reference fixes...")

# Fix "Chapter 14" reference in list of figures (AARRR funnel → now Ch 15)
for p in doc.paragraphs:
    if 'AARRR funnel diagram' in p.text and 'Chapter 14' in p.text:
        replace_in_para(p, 'Chapter 14', 'Chapter 15')
    # Fix "Chapter 12 / Appendix C" in table list
    if 'wMAPE by port size' in p.text and 'Chapter 12' in p.text:
        replace_in_para(p, 'Chapter 12', 'Chapter 14')


# ============================================================
# STEP 11: SAVE
# ============================================================
output_path = 'docs/Final project memo.docx'
doc.save(output_path)
print(f"\nSaved updated memo to {output_path}")
print("Done.")

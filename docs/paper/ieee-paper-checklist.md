# IEEE Student Conference Paper Pre-Submission Checklist

This checklist is to be completed by the team during Weeks 7 and 8 to prepare the manuscript for submission.

## 1. Content Verification & Data Completion
- [ ] **Replace all Placeholders:** Review the entire manuscript and replace all `[PLACEHOLDER]` markers (e.g., `[RESULT_F1]`, `[RESULT_AUCROC]`, `[HARDWARE]`, `[SKLEARN_VERSION]`, `[DATASET_SUBSET_SIZE]`) with actual numerical values from Member 2's model runs.
- [ ] **Integrate High-Resolution Figures:**
  - [ ] **Figure 1 (Architecture Diagram):** Insert the system topology diagram from Member 1. Ensure text in the diagram is legible in print.
  - [ ] **Figure 2 (SHAP Summary Plot):** Export the SHAP dot/bar plot from the ML pipeline as a high-density vector file (PDF/SVG) or high-res PNG (min 300 DPI).
  - [ ] **Figure 3 (Trust Score Distribution Plot):** Export the density comparison plot showing malicious vs. normal sessions.
- [ ] **Check Figure Captions and References:** Verify that every figure has a descriptive caption and is referenced in the body text (e.g., "...as shown in Fig. 1"). Ensure no broken figure cross-references exist.
- [ ] **Author Metadata:** Fill in the correct names, email addresses, and institutional affiliations for all 5 team members in the IEEE template header.

## 2. Technical Accuracy & Scope Alignment
- [ ] **Scope Limitation Verification:** Confirm that the paper does not claim real-time, agent-based OS log collection. It must explicitly state that logs were simulated via event replay using the CERT r4.2 dataset, with live agents identified as future work.
- [ ] **System Scope Alignment:** Ensure the text accurately describes what was built:
  - [ ] Zero Trust PEP-PDP separation (Keycloak + FastAPI).
  - [ ] Hybrid ML pipeline (Isolation Forest anomaly score injected as a feature into Random Forest).
  - [ ] Weighted Trust Score formula ($100 \times [0.4 \times (1-A) + 0.4 \times (1-P_r) + 0.2 \times C_{id}]$).
  - [ ] Database-driven policy mapping (Allow, Require MFA, Restrict, Alert).
  - [ ] React UI consisting of the 4 specified monitoring views.
- [ ] **Limit Claims:** Verify that no statements imply multi-tenant support or multi-organization validation. The system is designed and tested as a single-organization, single-tenant prototype.

## 3. Formatting & IEEE Standards
- [ ] **Two-Column Layout:** Verify that the LaTeX/Word document strictly follows the standard IEEE conference template (two-column, single-spaced, 10pt font for body text).
- [ ] **Page Budget:** Ensure the final compiled document fits within the 6-to-8-page limit. Adjust spacing, figure sizes, and table padding if the text overflows.
- [ ] **Abstract Word Count:** Perform a final word count on the abstract to ensure it remains under the 250-word maximum.
- [ ] **Mathematical Notation:** Review all equations (e.g., Trust Score formula, Isolation Forest anomaly score, SHAP summation) to ensure they are rendered correctly using standard mathematical styling (LaTeX math mode).
- [ ] **Tone Check:** Ensure the text is written in the formal, third-person active/passive IEEE style (e.g., use "this work proposes" or "the system implements" instead of "we built" or "I ran").

## 4. References & Citation Standards
- [ ] **IEEE Citation Format:** Check that all in-text citations are formatted as sequential numbers in square brackets (e.g., "[1]", "[2], [3]").
- [ ] **Reference List Compilation:** Ensure the bibliography lists all references in order of appearance in the text.
- [ ] **Reference Completeness:** Verify that every citation has complete metadata, including authors, title, journal/conference name, volume, issue, page range, and year of publication.
- [ ] **NIST and Keycloak References:** Verify that the reference list includes the official citation for NIST SP 800-207 and Keycloak/OAuth2/OIDC standards.

## 5. Quality Assurance
- [ ] **Spell Check:** Run automated spell checkers across all LaTeX source files.
- [ ] **Grammar Check:** Review the manuscript for active/passive voice consistency, subject-verb agreement, and run-on sentences.
- [ ] **Mathematical Consistency:** Cross-check the equations in Section III (Methodology) with the descriptions in Section V (Results) to ensure symbols and weights match exactly.

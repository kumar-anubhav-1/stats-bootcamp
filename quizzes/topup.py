"""Quiz top-ups: brings every lesson quiz to ≥ 8 (Basic → Advanced) and ≥ 5 (Leader) questions and adds the L6.8 / L9.8 quizzes.

    python quizzes/topup.py      # idempotent: appends questions (ids tN) only if missing

Each item: (prompt, correct option, [(wrong option, why), ...], why-correct). Numeric items: ("num", prompt, answer, tol, explanation).
Every question is a scenario from NorthStar (retail) or Meridian (bank), and every option explains itself, so a wrong answer teaches.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
LET = "abcd"

T = {
    # ------------------------------------------------------------------ Day 0
    "L0.1-F": [
        ("Claude Code proposes deleting the `outputs/` folder 'to tidy up'. You should…", "Ask what it contains and why, then decline unless it is truly scratch",
         [("Accept — tidiness matters", "Outputs are your audit trail."), ("Let it delete everything in data/ too", "Data is regenerated, but never delete without understanding."),
          ("Ignore the message", "Answer it: unclear actions should be questioned.")], "Never approve an action you don't understand."),
        ("Your colleague gets a different number from the same config. First check?", "Same data version (seed/hash) and same config file",
         [("Their laptop speed", "Speed doesn't change results."), ("Font settings", "Irrelevant."), ("Re-run until it matches", "That hides the cause.")], "Reproducibility = same data + same config + same code."),
        ("Why commit your config files to Git?", "So anyone can rerun and review exactly what you did",
         [("Git makes code faster", "No."), ("It's required by Python", "No."), ("To delete old versions", "Git keeps history.")], "Configs are the record of your analysis."),
    ],
    "L0.3-L": [("A junior reports the panel has 25,000 rows but the brief said 25,000 baskets. What do you ask?", "What one row represents (grain): lines, baskets or customers?",
                [("Nothing — numbers match", "Same number, different grain."), ("Ask for a bigger extract", "Doesn't address grain."), ("Ask for a chart", "Grain first.")],
                "Every number depends on grain.")],
    "L0.4-F": [
        ("A NorthStar config ran on the bank's file without errors but the results look odd. Most useful next step?", "Read the schema report and check the column mapping and units",
         [("Edit the recipe code", "Never change recipe code to fit data."), ("Trust it — no errors", "No errors ≠ valid assumptions."), ("Delete outliers", "Diagnose first.")], "The schema report flags mismatched roles and units."),
        ("What does a saved baseline protect you from?", "Silent changes in results when code, data or libraries change",
         [("Slow runs", "No."), ("Typos in prompts", "No."), ("Missing data", "Different problem.")], "Regression checks catch unexpected drift in outputs."),
    ],
    "L0.4-L": [("A team wants 20 copies of a recipe, one per business unit. Your advice?", "One recipe, 20 configs — change data and mapping, not code",
                [("Approve 20 copies", "Copies drift apart."), ("One giant script", "Hard to review."), ("Let each team write their own", "Inconsistent methods.")],
                "Configuration over duplication keeps methods consistent.")],
    "L0.5-F": [
        ("A NorthStar loyalty extract has postcode, birth date and gender. Why is it still risky after removing names?", "The combination can re-identify individuals (quasi-identifiers)",
         [("It isn't risky", "Linkage attacks are common."), ("Only names identify people", "Quasi-identifiers do too."), ("Because gender is sensitive only", "The combination is the issue.")], "Generalise or suppress quasi-identifiers."),
        ("Which is safest for practising analysis?", "Synthetic data like this course's datasets",
         [("A copy of production data on your laptop", "Breaches policy."), ("Pseudonymised production data in a public AI tool", "Still personal data."), ("Screenshots of customer records", "Still personal data.")], "Synthetic data carries no customer risk."),
    ],
    "L0.5-L": [("A vendor demo needs 'a sample of real complaints'. Best response?", "Provide synthetic or properly anonymised, approved samples under a data agreement",
                [("Send 100 real complaints by email", "Breach risk."), ("Refuse any demo", "Too blunt."), ("Let the vendor access production", "No.")],
                "Data minimisation and approvals first.")],
    # ------------------------------------------------------------------ Day 6 new lesson
    "L6.8-F": [
        ("Which algorithm predicts from the k most similar past cases?", "K-nearest neighbours", [("Naive Bayes", "Uses likelihoods."), ("PCA", "Unsupervised compression."), ("Gradient boosting", "Sequential trees.")], "KNN = similarity."),
        ("Naive Bayes is fast and useful for routing complaints because it…", "Multiplies per-word likelihoods assuming independence",
         [("Builds deep trees", "No."), ("Learns attention weights", "That's a transformer."), ("Finds clusters", "That's k-means.")], "Simple, fast text classifier."),
        ("Random forest vs gradient boosting:", "Forest averages independent trees; boosting adds trees that fix earlier errors",
         [("They are the same", "Different ensembles."), ("Boosting uses one tree", "Many."), ("Forest is unsupervised", "Supervised.")], "Bagging vs boosting."),
        ("num", "Test AUC of the logistic model in the credit bake-off?", "{{ a.d6l_credit['Logistic regression'].auc }}", 0.01, "Ties or beats the complex models."),
        ("Why were KNN and SVM trained on fewer rows?", "They slow down sharply as the number of rows grows",
         [("Bug", "Deliberate."), ("They need fewer rows to be accurate", "No."), ("Regulation", "No.")], "A real scalability cost."),
        ("Which pair are unsupervised?", "K-means and PCA", [("Logistic and SVM", "Supervised."), ("Random forest and GBM", "Supervised."), ("Transformer and KNN", "No.")], "No target variable."),
        ("Diffusion models are used to…", "Generate images or synthetic data by reversing a noising process",
         [("Forecast demand", "Not their purpose."), ("Score credit risk", "No."), ("Cluster customers", "No.")], "Generative top of the ladder."),
        ("Every learner beat 'same week last year' on Beverages demand. What does that tell you?", "The features carry real predictive signal",
         [("Seasonal naive is broken", "It's a benchmark."), ("Use the most complex model", "Gain over linear is small."), ("Nothing", "It's the key sanity check.")], "Beat naive first, then compare."),
    ],
    "L6.8-L": [
        ("The data-science team wants an MLP for default because 'AI is better'. Your first ask?", "The same-split bake-off table including logistic and a business metric",
         [("Approve", "No evidence."), ("Ask for more layers", "No."), ("Ask for a demo", "Demos aren't evidence.")], "Evidence before complexity."),
        ("The best demand model beats linear regression by {{ a.d6l_demand_gain_vs_linear }}%. Decision?", "Adopt only if that accuracy saves more than the cost of running and explaining it",
         [("Always adopt the best", "Ignores cost."), ("Never change", "Too rigid."), ("Use both at random", "No.")], "Translate accuracy into money."),
        ("Where is a transformer the right rung?", "Reading complaint text or summarising reviews",
         [("Credit scorecard", "Tabular and regulated."), ("Safety stock", "Formula."), ("Store A/B test", "Statistics.")], "Text and sequences."),
        ("open", "Explain the ML ladder to a board member in two sentences.", "Algorithms range from simple, explainable ones (linear, logistic, trees) to powerful, opaque ones (boosting, neural networks, transformers, diffusion). We start simple and only climb when a fair test shows a material, explainable gain.", "Full: ladder + climbing rule. Partial: one."),
        ("Which proposal most needs explainability?", "Automated credit declines", [("Product image tagging", "Lower stakes."), ("Review summaries for staff", "Lower stakes."), ("Demand forecasts", "Lower stakes.")], "Adverse-action reasons are required."),
    ],
    # ------------------------------------------------------------------ Day 8
    "L8.1-F": [("Before K-means on revenue (thousands) and promo share (0–1), you must…", "Standardise both features", [("Sort the data", "No."), ("Remove promo share", "No."), ("Nothing", "Revenue would dominate.")], "Distances need comparable scales."),
               ("PCA's first component is…", "The direction of maximum variance", [("The most important business feature", "Not necessarily."), ("A cluster", "No."), ("The target", "Unsupervised.")], "Ordered by variance.")],
    "L8.1-L": [("A segment has 2% of customers but a catchy name. Your concern?", "Too small to act on economically", [("None", "Size matters."), ("Name too catchy", "Not the issue."), ("Need more segments", "No.")], "Sizeable is a criterion.")],
    "L8.2-F": [("RFM 'R' for a customer who bought yesterday is…", "High recency score (recent)", [("Low", "Recent = good."), ("Undefined", "No."), ("Their revenue", "That's M.")], "Recency = days since last purchase, scored."),
               ("Why exclude bulk buyers when computing typical CLV?", "They distort averages (R07) and belong in their own segment", [("They don't buy", "They buy a lot."), ("Regulation", "No."), ("They never return", "Not why.")], "Heavy tails.")],
    "L8.2-L": [("Marketing wants to cut retention spend on gold customers. Ask?", "Their retention and CLV sensitivity — small retention drops cost the most here", [("Agree", "Risky."), ("Ask for colours", "No."), ("Nothing", "No.")], "CLV is retention-sensitive.")],
    "L8.3-F": [("Support of {Beer, Chips} is…", "Share of all baskets containing both", [("P(Chips | Beer)", "Confidence."), ("Lift", "Ratio to chance."), ("Count of beer", "No.")], "Joint frequency."),
               ("num", "Lift of Beer → Chips?", "{{ a.d8_beer.lift }}", 0.05, "R21.")],
    "L8.3-L": [("A rule has lift 3 but support 0.05%. Action?", "Low priority — too few baskets to matter commercially", [("Top priority", "Tiny reach."), ("Delete data", "No."), ("Bundle immediately", "Untested.")], "Lift with a support floor.")],
    "L8.4-F": [("num", "Snacks units change (%) for a +5% price rise?", "{{ a.d8_p5_units_snacks }}", 0.5, "Elastic."),
               ("Why exclude stock-out weeks from elasticity?", "Sales are capped by availability, not price (censored)", [("They're holidays", "No."), ("Too few", "No."), ("No reason", "There is.")], "R12.")],
    "L8.4-L": [("Promo ROI {{ a.d8_promo_roi }}. Interpretation?", "Each 1 of discount returns less than 1 of incremental margin before halo", [("Profitable", "Below 1."), ("Break-even", "No."), ("Meaningless", "No.")], "Cut or redesign deep promos.")],
    "L8.5-F": [("Isolation Forest flags 1% by default. Why change it?", "Match flags to review capacity", [("Default is always right", "Arbitrary."), ("More flags = better", "Overloads team."), ("Never change", "No.")], "Alert budget."),
               ("A customer flagged by robust z, forest and rule is…", "Higher-confidence — independent methods agree", [("Lower confidence", "No."), ("A bug", "No."), ("Irrelevant", "No.")], "Agreement raises precision.")],
    "L8.5-L": [("Flagged customers will be contacted. Safeguard?", "Human review and a respectful script before any action", [("Automatic ban", "False positives."), ("Public list", "No."), ("Nothing", "No.")], "Due process.")],
    "L8.6-F": [("Most ordinary shared-address components have…", "2–3 accounts (households)", [("15 accounts", "That's a ring."), ("0", "No."), ("100", "No.")], "Size separates rings from families."),
               ("Bunching ratio = deposits 9–10k ÷ 10–11k. A ratio near 1 means…", "No excess just below the threshold", [("Structuring", "Ratio ≫ 1 means that."), ("Fraud", "No."), ("Data error", "No.")], "Compare with smooth decline.")],
    "L8.6-L": [("Compliance asks for 'all evidence'. What goes in?", "Pattern, dates, amounts, linked accounts and method — no conclusions about guilt", [("Your opinion", "No."), ("Customer contact notes", "Tipping-off risk."), ("Only the score", "Insufficient.")], "Evidence, not verdicts.")],
    "L8.7-F": [("IV of 0.02 means a variable is…", "Not useful (< 0.02 rule of thumb)", [("Very strong", "No."), ("Suspicious", "That's > 0.5."), ("Medium", "0.1–0.3.")], "IV bands."),
               ("num", "Roll rate (%) from 60–89 to 90+?", "{{ a.d8_roll_60_90 }}", 1, "Most roll forward.")],
    "L8.7-L": [("PDO 20 at 600 = 50:1 means…", "Every 20 points doubles the good:bad odds", [("20% default", "No."), ("Score 600 is bad", "No."), ("Nothing", "Scaling.")], "Scorecard scaling.")],
    # ------------------------------------------------------------------ Day 9
    "L9.1-F": [("A placebo test runs the DiD where…", "No effect should exist (e.g. a category without the promotion)", [("The effect is largest", "No."), ("Only treated stores", "No."), ("Random weeks only", "Partial.")], "Falsification."),
               ("num", "Within-customer loyalty effect (%) from two-way fixed effects?", "{{ a.d9_r20_twfe }}", 3, "True +5%.")],
    "L9.1-L": [("'Pre-trends look parallel' — what evidence?", "Event-study plot and pre-period trend test", [("A single week", "Noisy."), ("Gut feel", "No."), ("Post-period only", "No.")], "Show the pre-period.")],
    "L9.2-F": [("num", "KM survival (%) at 24 months?", "{{ a.d9_km_s24 }}", 0.5, "F13."),
               ("Hazard ratio for digital share per 10 points {{ a.d9_cox.digital_share_10pp.hr }} means…", "Each +10 points of digital use lowers the churn hazard by about 11%", [("Raises churn", "HR < 1."), ("No effect", "Significant."), ("11% churn", "It's relative.")], "HR < 1 protective.")],
    "L9.2-L": [("Retention team wants 'average lifetime'. Offer?", "Restricted mean survival to 24 months ({{ a.d9_rmst24 }} months)", [("Mean of churners", "Biased."), ("Max tenure", "No."), ("Nothing", "No.")], "RMST handles censoring.")],
    "L9.3-F": [("Weight decay in an MLP is the same idea as…", "Ridge (L2) regularisation", [("Bootstrap", "No."), ("PCA", "No."), ("Cross-entropy", "Loss.")], "Penalty on weights."),
               ("For shelf photos, the first choice is…", "A convolutional / pretrained vision model", [("Logistic regression", "Pixels need features."), ("K-means", "Unsupervised."), ("ARIMA", "No.")], "Images = DL home turf.")],
    "L9.3-L": [("An LLM summary quotes a policy that doesn't exist. Root cause and fix?", "Hallucination — ground with RAG and citations, add review", [("Bigger model", "Doesn't guarantee."), ("Ignore", "Compliance risk."), ("Retrain logistic", "No.")], "Grounding.")],
    "L9.4-F": [("num", "Insurance loss ratio excluding the 3 catastrophic claims?", "{{ a.d9_ins_loss_ratio_excat }}", 0.02, "vs {{ a.d9_ins_loss_ratio }} with them."),
               ("Capital = VaR − expected loss covers…", "Unexpected loss", [("Expected loss", "Priced in."), ("All losses", "No."), ("Profit", "No.")], "EL priced, UL capitalised.")],
    "L9.4-L": [("A stress of PD × 2.5 raises EL to {{ a.d9_cr_stress_el }}M. Use?", "Set limits and contingency plans for a downturn", [("Ignore — unlikely", "Stress tests matter."), ("Publish as forecast", "It's a scenario."), ("Delete", "No.")], "Scenario planning.")],
    "L9.5-F": [("Calibration within groups means…", "The same predicted PD gives the same default rate in each group", [("Equal approval rates", "Parity."), ("Equal TPR", "Opportunity."), ("Equal sizes", "No.")], "Score means the same."),
               ("num", "Approval rate (%) for group B?", "{{ a.d9_appr_B }}", 0.5, "vs {{ a.d9_appr_A }}% A.")],
    "L9.5-L": [("Personalised pricing charges one area 8% more. First step?", "Check whether the area proxies a protected group and whether the gap is justified", [("Launch", "Risky."), ("Lower all prices", "Blunt."), ("Ignore", "No.")], "Proxy check.")],
    "L9.6-F": [("Score PSI 0.27 with stable AUC suggests…", "Population drift — recalibrate and review cut-offs", [("Concept drift", "AUC stable."), ("Data bug", "Check units first, but likely mix."), ("No issue", "Act band.")], "Ladder."),
               ("num", "Late-vintage default rate (%)?", "{{ a.d9_f12_def_late }}", 0.2, "vs {{ a.d9_f12_def_early }}% early.")],
    "L9.6-L": [("Who should own a model's monitoring?", "A named model owner with thresholds and escalation", [("Nobody", "No."), ("The vendor only", "Accountability stays."), ("IT only", "Business owns risk.")], "MRM.")],
    "L9.7-F": [("Which chart title is best?", "Partner vintages default 3× faster", [("Default rate by vintage", "Descriptive only."), ("Chart 3", "No."), ("Data", "No.")], "Message titles."),
               ("A number without its uncertainty invites…", "False precision and overconfident decisions", [("Trust", "Unearned."), ("Nothing", "No."), ("Better decisions", "No.")], "Show ranges.")],
    "L9.7-L": [("The CFO interrupts at slide 2: 'What do you want?' You…", "State the decision and the ask immediately", [("Continue the agenda", "Lose them."), ("Show methods", "No."), ("Apologise", "Answer.")], "Answer first.")],
    "L9.8-F": [
        ("num", "PD (%) from the one-neuron example (utilisation 0.9, bureau 620)?", "{{ a.d9n_neuron.p }}", 0.5, "σ(z) with z = {{ a.d9n_neuron.z }}."),
        ("A neuron with a sigmoid output on raw features is equivalent to…", "Logistic regression", [("K-means", "No."), ("PCA", "No."), ("A decision tree", "No.")], "Same formula."),
        ("Cross-entropy loss is used for…", "Classification probabilities (e.g. default yes/no)", [("Weekly sales amounts", "Use MSE."), ("Clustering", "No."), ("Benford tests", "No.")], "Log-loss."),
        ("Backpropagation computes…", "Gradients of the loss with respect to every weight, via the chain rule", [("The data mean", "No."), ("Predictions only", "That's the forward pass."), ("Cluster centres", "No.")], "Blame assignment."),
        ("Learning rate too high causes…", "Oscillation or divergence of the loss", [("Slow but steady progress", "That's too low."), ("Perfect fit", "No."), ("Nothing", "It matters.")], "See the 3-D bowl."),
        ("num", "Epoch with the lowest validation loss for the weakly penalised network?", "{{ a.d9n_weak_best_epoch }}", 2, "Then it overfits."),
        ("Self-attention lets a transformer…", "Weigh every token against every other token for context", [("Ignore word order completely", "Positional encoding adds order."), ("Only read one word", "No."), ("Cluster documents", "No.")], "softmax(QKᵀ/√d)V."),
        ("A diffusion model generates an image by…", "Starting from noise and removing predicted noise step by step", [("Copying a training image", "It learns the distribution."), ("Sorting pixels", "No."), ("Clustering colours", "No.")], "Reverse process."),
    ],
    "L9.8-L": [
        ("A vendor shows a falling training loss as proof of quality. You ask for…", "Validation loss by epoch and an out-of-time test", [("More epochs", "Worsens overfitting."), ("A bigger GPU", "Irrelevant."), ("Nothing", "No.")], "Generalisation evidence."),
        ("RAG matters for a policy chatbot because…", "Answers are grounded in and cite your actual documents", [("It's faster", "Not the point."), ("It removes all errors", "Reduces, not removes."), ("It replaces review", "No.")], "Grounding."),
        ("Generated product images must be…", "Labelled, rights-checked and reviewed before publishing", [("Published directly", "Risky."), ("Kept secret", "Disclose."), ("Banned outright", "Too blunt.")], "Governance."),
        ("open", "Why does a strong L2 penalty help the network on 3,000 accounts?", "It limits how large weights can get, so the network can't memorise noise; validation loss stays near {{ a.d9n_strong_val_end }} instead of rising to {{ a.d9n_weak_val_end }}.", "Full: mechanism + numbers. Partial: mechanism."),
        ("SFT and RLHF are…", "Post-training steps that teach a pre-trained model to follow instructions and preferred behaviour", [("Data cleaning", "No."), ("Clustering", "No."), ("Forecasting", "No.")], "Post-training."),
    ],
    # ------------------------------------------------------------------ Day 10
    "L10.1-F": [("Which recipe first on an unseen file?", "rcp_profile then rcp_quality", [("rcp_classifier", "Too early."), ("rcp_drift", "Needs windows."), ("None", "Always profile.")], "Data first."),
                ("A day with double the usual orders, identical content, new ids, is…", "A duplicated load", [("A sale", "Content identical."), ("Normal peak", "Too exact."), ("Fraud", "Unlikely.")], "Check content duplicates.")],
    "L10.1-L": [("The transfer readout claims delivery time causes low ratings. You ask…", "Is it association, and what confounders (zone, hour) were controlled?", [("Accept", "Causal claim."), ("Ask for colours", "No."), ("Nothing", "No.")], "Association vs causation.")],
    "L10.2-F": [("num", "Default rate (%) of the 2025Q3 vintage?", "{{ a.d10_def_late }}", 0.2, "vs {{ a.d10_def_ref }}% in 2025Q1."),
                ("BOGO margin was negative in Q4. First question?", "Was it incremental volume or discounted purchases that would happen anyway?", [("Stop all promos", "Blunt."), ("Run more BOGO", "No."), ("Ignore", "No.")], "Incrementality.")],
    "L10.2-L": [("A capstone uses lesson numbers without re-running. Verdict?", "Send back — every number must come from their own configs and outputs", [("Accept", "Unverified."), ("Extra credit", "No."), ("Ignore", "No.")], "Reproducibility.")],
}


def build_q(qid, item):
    if item[0] == "num":
        _, prompt, ans, tol, expl = item
        return {"id": qid, "type": "numeric", "difficulty": 2, "prompt": prompt, "answer": ans, "tolerance_abs": tol, "explanation": expl}
    if item[0] == "open":
        _, prompt, model, rubric = item
        return {"id": qid, "type": "open", "difficulty": 3, "prompt": prompt, "model": model, "rubric": rubric}
    prompt, correct, wrongs, why = item
    opts = [{"id": "a", "text": correct, "correct": True, "why": why}] + [{"id": LET[i + 1], "text": w, "why": y} for i, (w, y) in enumerate(wrongs)]
    return {"id": qid, "type": "mcq", "difficulty": 2, "prompt": prompt, "options": opts}


class _Dumper(yaml.SafeDumper):
    pass


def _str(dumper, s):
    # strings holding Jinja must survive raw-text rendering: double-quoted style never doubles single quotes
    if "{{" in s or "{%" in s:
        return dumper.represent_scalar("tag:yaml.org,2002:str", s, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", s)


_Dumper.add_representer(str, _str)


def main():
    files = sorted((ROOT / "bank").glob("day*.yaml"))
    banks = {f: yaml.safe_load(f.read_text()) for f in files}
    where = {q["id"]: (f, q) for f, b in banks.items() for q in b["quizzes"]}
    new_quizzes = {"L6.8-F": ("day06.yaml", "L6.8 The ML ladder (Basic → Advanced)", "L6.8", "F", ["C190"]),
                   "L6.8-L": ("day06.yaml", "L6.8 Choosing the rung (Leader)", "L6.8", "L", ["C282"]),
                   "L9.8-F": ("day09.yaml", "L9.8 Inside neural networks (Basic → Advanced)", "L9.8", "F", ["C277"]),
                   "L9.8-L": ("day09.yaml", "L9.8 Governing deep learning and GenAI (Leader)", "L9.8", "L", ["C286"])}
    added = 0
    for qid, items in T.items():
        if qid not in where:
            fname, title, lesson, track, concepts = new_quizzes[qid]
            f = ROOT / "bank" / fname
            quiz = {"id": qid, "title": title, "lesson": lesson, "track": track, "questions": []}
            gate = next(i for i, q in enumerate(banks[f]["quizzes"]) if q["id"].endswith("GATE"))
            banks[f]["quizzes"].insert(gate, quiz)
            where[qid] = (f, quiz)
            default_concepts = concepts
        f, quiz = where[qid]
        default_concepts = quiz["questions"][0]["concepts"] if quiz["questions"] else new_quizzes[qid][4]
        have = {q["id"] for q in quiz["questions"]}
        for k, item in enumerate(items, 1):
            nid = f"t{k}"
            if nid in have:
                continue
            q = build_q(nid, item)
            q["concepts"] = default_concepts
            quiz["questions"].append(q)
            added += 1
    for f, b in banks.items():
        f.write_text(yaml.dump(b, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100000))
    print("added", added)


if __name__ == "__main__":
    main()

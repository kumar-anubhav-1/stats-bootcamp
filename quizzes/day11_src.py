"""Source for quizzes/bank/day11.yaml (computer vision). Run: python quizzes/day11_src.py"""
from pathlib import Path

import yaml

from topup import _Dumper, build_q

C = {"L11.1": "C276", "L11.2": "C282", "L11.3": "C207", "L11.4": "C205", "L11.5": "C216"}
Q = {
    "L11.1-F": [
        ("A shelf photo of 48 × 192 pixels in colour contains how many numbers?", "27,648 (48 × 192 × 3)", [("9,216", "Forgot the 3 colour channels."), ("192", "One row only."), ("48", "One column only.")], "Rows × columns × channels."),
        ("A pixel value of 0 in the red channel means…", "No red light at that point (dark)", [("Bright red", "255 is brightest."), ("Missing data", "It's a valid value."), ("An error", "No.")], "0 dark, 255 bright."),
        ("A 3 × 3 filter with −1s on the left and +1s on the right detects…", "Vertical edges (left-to-right brightness jumps)", [("Colour", "It ignores colour."), ("Horizontal edges", "That's top-to-bottom."), ("Noise only", "It responds to edges.")], "Weighted sums highlight patterns."),
        ("What does a CNN learn?", "Its own filters, from edges up to shapes", [("Fixed hand-made rules", "Learned."), ("Only colours", "Also shapes."), ("Nothing new vs regression", "Learns spatial filters.")], "Stacked learned filters."),
        ("num", "Average brightness of store S07's photos from week 5?", "{{ a.v_bright_s7_after }}", 0.03, "Was {{ a.v_bright_s7_before }} — a dim camera (V1)."),
        ("Store S03's photos have much lower sharpness. Most likely?", "The camera is out of focus", [("More products", "Doesn't lower sharpness."), ("A bigger store", "No."), ("Better lighting", "No.")], "V2."),
        ("Why check image quality before modelling?", "Models fail silently on conditions unlike their training images", [("It's required by law", "No."), ("To speed up training", "Not the point."), ("It isn't needed", "It is.")], "Quality first."),
        ("Hand-made image features are…", "Quick and explainable but fragile when conditions change", [("Always best", "No."), ("Impossible to compute", "Easy."), ("The same as CNN filters", "Hand-made vs learned.")], "Trade-off."),
    ],
    "L11.1-L": [
        ("A vendor shows accuracy before any images. You ask…", "To see random images from every camera first", [("For a bigger model", "No."), ("For the price", "Later."), ("Nothing", "No.")], "Look at the data."),
        ("Cheapest ongoing safeguard for a camera network?", "Daily brightness and sharpness checks per camera", [("Retrain weekly", "Costly; misses root cause."), ("More cameras", "No."), ("None", "No.")], "Quality monitoring."),
        ("Shelf cameras capture shoppers. Best control?", "Point at shelves, blur faces, short retention", [("Keep everything", "Privacy risk."), ("Turn off cameras", "Loses value."), ("Face recognition", "High legal risk.")], "Privacy by design."),
        ("open", "Explain to a store manager what the system 'sees'.", "A grid of numbers per photo — brightness of red, green and blue at each point; the model learns which number patterns mean an empty slot.", "Full: numbers + pattern learning. Partial: one."),
        ("One camera degrades. Who should be alerted first?", "The camera owner, before reports go out", [("The CEO", "Too late/too high."), ("Nobody", "No."), ("Customers", "No.")], "Fix at source."),
    ],
    "L11.2-F": [
        ("Only {{ a.v_gap_share }}% of windows are gaps. A model saying 'no gap' everywhere would score about…", "93% accuracy while finding no gaps", [("50%", "No."), ("0%", "No."), ("100%", "No.")], "Accuracy trap."),
        ("Recall for gaps means…", "Share of real gaps the model finds", [("Share of flags that are real", "Precision."), ("Overall accuracy", "No."), ("Speed", "No.")], "Coverage."),
        ("num", "Gap recall (%) of the small network on the dim camera, without augmentation?", "{{ a.v_cls['Small neural network on raw pixels'].rec_dim }}", 5, "Accuracy still {{ a.v_cls['Small neural network on raw pixels'].acc_dim }}%."),
        ("num", "Gap recall (%) on the dim camera after brightness augmentation?", "{{ a.v_aug.rec_dim }}", 5, "Robust to light."),
        ("Data augmentation means…", "Creating extra training images by changing what shouldn't matter (light, small shifts)", [("Collecting more stores", "That's more data, not augmentation."), ("Changing labels", "No."), ("Adding features by hand", "No.")], "Invariance."),
        ("Why split by store, not by random window?", "Windows from the same photo would leak into test and inflate results", [("Faster", "No."), ("Required by sklearn", "No."), ("No reason", "Leakage.")], "Group split (L6.4)."),
        ("Transfer learning is…", "Fine-tuning a model pretrained on millions of photos for your task", [("Training from scratch", "Opposite."), ("Moving data between servers", "No."), ("A type of augmentation", "Different.")], "Reuse filters."),
        ("The brightness rule has very low precision because…", "Dark packs look like empty slots", [("It's too slow", "No."), ("It ignores colour", "Partly, but the issue is dark packs."), ("It's random", "No.")], "Simple rules confuse look-alikes."),
    ],
    "L11.2-L": [
        ("'98% accuracy on shelf gaps.' Your first question?", "What are gap recall and precision, by store and camera?", [("Can it be 99%?", "Wrong metric."), ("How fast is it?", "Later."), ("Who built it?", "Irrelevant.")], "Rare-event metrics."),
        ("Which test result matters most for a 400-store rollout?", "Performance on the worst camera and unseen stores", [("Average on training stores", "Leaky."), ("Best store", "Cherry-picked."), ("Vendor demo", "Not evidence.")], "Test where it runs."),
        ("A team trained a CNN from scratch on 800 images. Advice?", "Start from a pretrained model and fine-tune with augmentation", [("Collect 1 million images first", "Unnecessary."), ("Use a brightness rule", "Weak."), ("Ship it", "Risky.")], "Transfer learning."),
        ("open", "Why did the neural network fail in store S07, and how was it fixed?", "It had only seen bright photos; in the dim store gaps looked like products. Training with random brightness changes taught it that a gap is a gap in any light — recall rose from {{ a.v_cls['Small neural network on raw pixels'].rec_dim }}% to {{ a.v_aug.rec_dim }}%.", "Full: cause + fix + numbers. Partial: one."),
        ("Each model failed differently (false alarms, dim light, blur). Lesson?", "Test every model on every condition you expect in production", [("Pick the most complex", "Still failed."), ("Average the results", "Hides failures."), ("Ignore rare conditions", "They happen.")], "Stress testing."),
    ],
    "L11.3-F": [
        ("IoU of two boxes is…", "Overlap ÷ total area covered by both", [("Overlap ÷ true box", "No."), ("Distance between centres", "No."), ("Union ÷ overlap", "Inverted.")], "Intersection over union."),
        ("num", "IoU for truth 80–104 and prediction 90–118?", "0.37", 0.02, "Overlap 14 ÷ union 38."),
        ("A prediction with IoU 0.4 at a 0.5 standard counts as…", "A false alarm, and the true gap as a miss", [("A hit", "Below standard."), ("Half a hit", "No partial credit."), ("Ignored", "No.")], "Matching rule."),
        ("num", "Detection recall (%) on new stores at IoU ≥ 0.5?", "{{ a.v_det['test stores'].recall }}", 3, "Precision {{ a.v_det['test stores'].precision }}%."),
        ("AP at IoU 0.75 is much lower than at 0.5 because…", "Box edges are coarse (4-pixel steps)", [("The model is random", "No."), ("Fewer gaps", "Same gaps."), ("Bug", "Expected.")], "Stricter overlap."),
        ("Average precision summarises…", "The precision–recall curve across score thresholds", [("Accuracy", "No."), ("IoU only", "No."), ("Training loss", "No.")], "Area under PR."),
        ("Non-maximum suppression…", "Removes duplicate overlapping boxes, keeping the highest score", [("Adds boxes", "No."), ("Normalises pixels", "No."), ("Augments data", "No.")], "Deduplication."),
        ("num", "Predicted on-shelf availability (%) on new stores?", "{{ a.v_det['test stores'].osa_pred }}", 1, "vs {{ a.v_det['test stores'].osa_true }}% labelled."),
    ],
    "L11.3-L": [
        ("A vendor quotes 'precision 0.9'. You ask…", "At what IoU, on which images, and with what recall?", [("Nothing", "Incomplete."), ("For 0.95", "No."), ("For the code", "Not the point.")], "Context."),
        ("Camera OSA is {{ (a.v_det['test stores'].osa_true - a.v_det['test stores'].osa_pred) | round(1) }} points below audited OSA. Action?", "Report the bias and calibrate with a monthly manual audit", [("Hide it", "No."), ("Abandon cameras", "Overreaction."), ("Ignore", "Misleads managers.")], "Known bias."),
        ("Missed gaps cost sales; false alarms cost staff time. Threshold choice?", "Minimise total cost of misses and false alarms", [("Always 0.5", "Arbitrary."), ("Maximise accuracy", "Wrong objective."), ("Minimise false alarms only", "Misses sales.")], "Cost-based (L6.6)."),
        ("open", "Tell the COO how reliable the gap alerts are.", "On new stores the system finds about {{ a.v_det['test stores'].recall | round(0) }}% of gaps and {{ a.v_det['test stores'].precision | round(0) }}% of its alerts are real; it slightly under-states availability, so we calibrate monthly against a manual audit.", "Full: recall + precision + bias. Partial: one."),
        ("Without augmentation, dim-store detection recall fell to {{ a.v_det_dim_noaug.recall }}%. Governance lesson?", "Monitor per-camera performance and image quality continuously", [("Buy brighter bulbs only", "Partial."), ("Nothing", "No."), ("Use fewer stores", "No.")], "Monitoring."),
    ],
    "L11.4-F": [
        ("OCR of a cheque amount is…", "Several image-classification problems, one per character", [("One regression", "No."), ("Clustering", "No."), ("A forecast", "No.")], "Characters."),
        ("num", "Best digit accuracy (%) on test digits?", "{{ a.v_ocr_acc[a.v_ocr_best] }}", 1, "{{ a.v_ocr_best }}."),
        ("num", "Field accuracy (%) for 6-digit amounts?", "{{ a.v_cheque_field_acc }}", 1, "≈ digit accuracy⁶."),
        ("Why is field accuracy lower than digit accuracy?", "Any one wrong digit makes the whole amount wrong", [("Different model", "Same."), ("Bug", "No."), ("More data", "No.")], "Errors multiply."),
        ("Confidence routing means…", "Automate reads above a confidence threshold; send the rest to people", [("Retrain often", "No."), ("Read everything twice", "Costly."), ("Ignore low confidence", "Unsafe.")], "Human-in-the-loop."),
        ("num", "Share (%) of cheques automated at the 0.5%-error threshold?", "{{ a.v_route_auto_at_thr }}", 3, "Threshold {{ a.v_route_threshold }}."),
        ("Before routing on confidence, the probabilities should be…", "Calibrated", [("Rounded", "No."), ("Hidden", "No."), ("Doubled", "No.")], "L6.6."),
        ("Flipping digit images as augmentation is…", "Wrong — a flipped 6 can look like a 9", [("Always fine", "Changes meaning."), ("Required", "No."), ("Irrelevant", "It matters.")], "Augment only meaning-preserving changes."),
    ],
    "L11.4-L": [
        ("A vendor quotes 99% character accuracy. You ask for…", "Field-level accuracy at our error tolerance", [("Speed", "Later."), ("Logo", "No."), ("Nothing", "Incomplete.")], "Business-level metric."),
        ("Set first: the error tolerance or the automation target?", "The error tolerance — automation follows", [("Automation target", "Risk becomes an afterthought."), ("Neither", "No."), ("Vendor decides", "No.")], "Risk appetite first."),
        ("Cheapest extra protection beyond the model?", "Business-rule cross-checks (figures vs words, valid date, account exists)", [("A bigger model", "Costly."), ("No checks", "No."), ("Manual review of everything", "Defeats automation.")], "Rules."),
        ("open", "Write the business case sentence for cheque automation.", "At a 0.5% error tolerance we can automate about {{ a.v_route_auto_at_thr }}% of cheques; the rest go to clerks, and a daily audit sample checks automated reads.", "Full: tolerance + automation + audit. Partial: one."),
        ("A scanner batch drops accuracy to {{ a.v_ocr_smudged_acc }}%. Response?", "Route that scanner's items to people and fix the scanner", [("Retrain immediately", "Fix the source."), ("Ignore", "Errors."), ("Raise automation", "Opposite.")], "Drift response."),
    ],
    "L11.5-F": [
        ("Cohen's kappa corrects agreement for…", "Agreement expected by chance", [("Sample size", "No."), ("Image size", "No."), ("Model accuracy", "No.")], "Chance-corrected."),
        ("num", "Kappa between annotators A and B?", "{{ a.v_kappa }}", 0.02, "Raw agreement {{ a.v_agree_pct }}%."),
        ("Kappa is much lower than raw agreement here because…", "Most windows are obvious 'product', so chance agreement is high", [("Bug", "No."), ("Too few windows", "No."), ("Kappa is always lower by 30 points", "Depends on base rates.")], "Base rates."),
        ("Random label noise of 8% mostly…", "Averages out; systematic errors do not", [("Destroys any model", "Not random noise."), ("Improves models", "No."), ("Has no effect ever", "Systematic noise does.")], "Random vs systematic."),
        ("Image drift is best caught by…", "Daily per-camera statistics (brightness, sharpness, confidence) with PSI bands", [("Annual review", "Too late."), ("Customer complaints", "Too late."), ("Bigger models", "No.")], "Monitoring."),
        ("Face recognition for loss prevention is…", "High legal risk in many places; avoid unless clearly lawful and approved", [("Always fine", "No."), ("Required", "No."), ("Low risk", "No.")], "Biometrics."),
        ("Usually the largest hidden cost of a vision project is…", "Labelling", [("GPUs", "Often smaller."), ("Cameras", "Visible."), ("Licences", "Smaller.")], "Labels."),
        ("Fairness in ID verification means testing…", "Accuracy and false rejections by group and document type", [("Overall accuracy only", "Hides gaps."), ("Speed", "No."), ("Nothing", "No.")], "L9.5."),
    ],
    "L11.5-L": [
        ("Minimum evidence before scaling cameras to all stores?", "Pilot with audited KPI, per-camera monitoring and a cost per gap found", [("A demo", "No."), ("Vendor slides", "No."), ("Nothing", "No.")], "Evidence."),
        ("Kappa 0.55 between labellers. Action?", "Improve the guide, retrain labellers, adjudicate disagreements", [("Proceed", "Weak labels."), ("Drop labelling", "No."), ("Use one labeller", "Hides the problem.")], "Label quality."),
        ("Who should sign off privacy for shelf cameras?", "Legal/privacy officer with store operations", [("The data scientist alone", "No."), ("Nobody", "No."), ("The vendor", "No.")], "Accountability."),
        ("open", "Give three reasons vision projects fail after the pilot.", "Camera and lighting drift, poor or inconsistent labels, and no monitoring or audited KPI (plus privacy issues and unpriced errors).", "Full: three. Partial: one or two."),
        ("The model's average confidence falls in one store. Likely?", "Image-quality or environment change at that store", [("Model improved", "No."), ("More gaps", "Possibly, but check images first."), ("Nothing", "Investigate.")], "Drift signal."),
    ],
    "D11-GATE": [
        ("A colour image of 100 × 100 pixels has…", "30,000 numbers", [("10,000", "Forgot channels."), ("300", "No."), ("100", "No.")], "× 3."),
        ("Edge filters respond to…", "Sudden brightness changes", [("Colour names", "No."), ("Labels", "No."), ("Nothing", "No.")], "Gradients."),
        ("For rare gaps, report…", "Recall and precision", [("Accuracy only", "Trap."), ("Loss", "No."), ("AUC only", "Partial.")], "Rare events."),
        ("Augmentation should change…", "Things that don't change the label", [("Labels", "No."), ("Anything", "Flips can change meaning."), ("Nothing", "Then it's not augmentation.")], "Invariance."),
        ("Transfer learning helps when…", "Labelled images are few", [("Data is huge only", "Helps most when small."), ("Never", "No."), ("Only for text", "No.")], "Reuse."),
        ("IoU 0.5 is…", "A common standard for counting a detection as correct", [("Perfect overlap", "That's 1."), ("No overlap", "That's 0."), ("A pixel count", "No.")], "Standard."),
        ("AP summarises…", "The precision–recall curve", [("Accuracy", "No."), ("Training loss", "No."), ("Image size", "No.")], "Detection metric."),
        ("A 6-character field is right less often than one character because…", "Errors multiply", [("Different scanners", "No."), ("Bug", "No."), ("It isn't", "It is.")], "Field accuracy."),
        ("Confidence routing trades…", "Automation rate against error rate", [("Speed against cost", "No."), ("Pixels against labels", "No."), ("Nothing", "No.")], "Threshold."),
        ("Kappa measures…", "Chance-corrected agreement between labellers", [("Model accuracy", "No."), ("Image quality", "No."), ("IoU", "No.")], "Labels."),
        ("A dim camera is…", "Image drift — monitor per camera", [("Concept drift only", "Input drift."), ("Irrelevant", "No."), ("A label error", "No.")], "V1."),
        ("Shelf cameras and privacy:", "Point at shelves, blur faces, limit retention", [("Record everything", "No."), ("Face recognition", "Risky."), ("No controls", "No.")], "Privacy by design."),
    ],
}
META = {"L11.1": "Images as data", "L11.2": "Classification and augmentation", "L11.3": "Detection, IoU and OSA", "L11.4": "Document AI", "L11.5": "Vision in production"}


def main():
    quizzes = []
    for qid, items in Q.items():
        if qid == "D11-GATE":
            q = {"id": qid, "title": "Day 11 gate (pass 75%)", "lesson": "D11", "track": "Mixed", "pass_mark": 75, "questions": []}
            conc = "C282"
        else:
            lid, tr = qid.split("-")
            q = {"id": qid, "title": f"{lid} {META[lid]} ({'Basic → Advanced' if tr == 'F' else 'Leader'})", "lesson": lid, "track": tr, "questions": []}
            conc = C[lid]
        for k, it in enumerate(items, 1):
            x = build_q(f"q{k}", it)
            x["concepts"] = [conc]
            q["questions"].append(x)
        quizzes.append(q)
    out = Path(__file__).resolve().parent / "bank" / "day11.yaml"
    out.write_text(yaml.dump({"quizzes": quizzes}, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100000))
    print("written", out, sum(len(q["questions"]) for q in quizzes))


if __name__ == "__main__":
    main()

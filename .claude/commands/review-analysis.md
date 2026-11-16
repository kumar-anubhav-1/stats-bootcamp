---
description: Review someone else's analysis or code like a sceptical senior
argument-hint: <path to analysis folder, notebook or script>
---
Review $ARGUMENTS as a senior data scientist would. Produce:

1. A three-sentence summary of what was done and concluded.
2. The assumptions it relies on (explicit and hidden).
3. Risks, each tagged: wrong test/unit, leakage, silent row loss, ignored assumption, multiple testing, correlation read as causation, stale parameters, unit/grain mismatch, hallucinated or unverifiable number.
4. Which numbers you could reproduce, and which you could not.
5. The three questions you would ask the author, and your recommendation: approve / approve with changes / reject.

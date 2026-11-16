---
description: Re-run a config and confirm results are unchanged versus the saved baseline
argument-hint: <config path>
---
Run `python -m toolkit.run $ARGUMENTS --check-baseline`. If it passes, say so in one line. If it fails, list every metric that
changed (old → new), explain the most likely cause (data change, config change, code change, library version), and do not
update the baseline unless I explicitly approve.

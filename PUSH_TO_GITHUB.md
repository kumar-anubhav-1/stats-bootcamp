# Push-to-GitHub checklist

Two repositories, because a public repo cannot hide files:

| Repository | Visibility | Contains |
| --- | --- | --- |
| `stats-bootcamp` | public or org-internal | everything learners use: site, data generators, toolkit, quizzes, exercises, Navigator |
| `stats-bootcamp-instructor` | **private** | the same plus `instructor/pack/` (rubrics, guides, code-review exam + key), `instructor/exam_config.py` (held-out exam parameters), `instructor/transfer_gen.py` (transfer dataset), `tools/instructor_pack.py` |

## 1. Final checks (in this workspace)

- [ ] `make` (full build) ends with **✔ All checks passed** — data regenerated, 42 anomalies within band, all recipe baselines pass, strict site build
- [ ] `make instructor` writes `instructor/pack/transfer_key.md` and `exam_key.md` with no `n/a` rows you rely on
- [ ] `git status` is clean; generated data, `site/`, `outputs/` and the two keys are git-ignored
- [x] Licence: CC BY-NC 4.0 (`LICENSE`, footer copyright in `mkdocs.yml`)
- [ ] Set `repo_url` in `mkdocs.yml` to the public repository URL

## 2. Split

```bash
tools/split_repos.sh ../stats-bootcamp-public ../stats-bootcamp-instructor
```

The script copies committed files only, removes instructor-only material from the public copy and **aborts if anything instructor-only
leaks** (it scans for answer-key markers).

## 3. Create the repositories and push

```bash
# public (or internal)
cd ../stats-bootcamp-public
gh repo create <org>/stats-bootcamp --public --source . --push        # or --internal

# private
cd ../stats-bootcamp-instructor
gh repo create <org>/stats-bootcamp-instructor --private --source . --push
```

(Without the GitHub CLI: create both empty repos on github.com, then `git remote add origin <url> && git push -u origin main`.)

## 4. Turn on the site and CI (public repo)

- [ ] Settings → Pages → Source: **GitHub Actions**
- [ ] Actions → run **deploy-site** once; check the Pages URL opens and a quiz works
- [ ] Actions → **data-and-tests** passes on the push (it skips exam/transfer generation automatically in the public repo)
- [ ] Settings → Codespaces: allow for the organisation; open one Codespace and run `make quick`
- [ ] Branch protection on `main`: require the data-and-tests check

## 5. Private repo

- [ ] Restrict access to instructors
- [ ] Run `make instructor` in a Codespace or locally; download keys for the cohort; never commit keys or `instructor/*/truth`
- [ ] For a resit: change the exam seeds in `instructor/exam_config.py`, rerun `make instructor`

## 6. Before each cohort

- [ ] Pull both repos; `make` passes
- [ ] Update dates in the facilitator guide; send Day 0 pre-work and the diagnostic link
- [ ] Prepare the transfer file and exam data folders for distribution (data only)
- [ ] Clear previous cohort's progress files from your machine

## 7. Keeping them in sync

Develop in the private repo (it is a superset). To update learners, rerun `tools/split_repos.sh` into fresh folders and push the public
copy over the public repo (`git push --force-with-lease` on a release branch, then merge), or cherry-pick commits that touch no
instructor files.

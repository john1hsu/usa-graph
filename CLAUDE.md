# USA Graph — run playbook

This repo is a citation-backed, reasoner-checked knowledge graph about the United States of America: its land, rivers and environment; its states, territories, regions, cities and landmarks; the Native nations and their histories; American history from before European colonization through the colonial era, the Revolution, expansion, the Civil War and Reconstruction, industrialization, the world wars, the Cold War and civil rights era to today; the Constitution, government, rights, law and elections; the presidents, founders, activists and inventors who shaped it; and its economy, society, immigration, culture, science, foreign relations and national symbols. A scheduled run adds **exactly one new, unique article** per run. Every article must leave a reader *understanding the United States more accurately* — what happened, how it works, and what the evidence actually shows. Follow these steps in order. Read `SCHEMA.md` before writing.

## 1. Sync and orient
```bash
pip install -r requirements.txt --break-system-packages -q
git pull --rebase origin main
python3 scripts/kg.py build      # must print OK; fix the repo first if it doesn't
```
Read `graph/stats.md`, `graph/frontier.md`, `graph/competency.md` and `topics/seeds.yaml`. `graph/index.json` lists every node (ids, titles, aliases, edges, dates, timelines, review questions, source URLs).

## 2. Pick the topic (graph-driven)
Use the current UTC hour modulo 3:
- **0 → depth.** Take the top node in `graph/frontier.md` that fits a domain, **skipping any node that would belong to the domain with the most articles** ("Domain coverage" in `graph/stats.md`; on a tie for most, skip all tied domains), so one domain's dense cross-links can't snowball into a lopsided graph. Use its *Expected type* (inferred by the reasoner) as the article's `type` unless it is clearly wrong.
- **1 → breadth.** Take the domain at the top of "Domain coverage" in `graph/stats.md` (fewest articles; skip the domain of the most recent commit on ties) and pick an unwritten seed or another important topic in it.
- **2 → gap.** Take the first row of the first non-empty *(gap)* section in `graph/competency.md` and write the article that closes it (what an event led to, the amendment or case that protects a right, the body that enacted a law, what happened at a place, the role a person played, a link to an orphan).
- If the chosen mode yields nothing (as on the first runs, when the frontier is empty), fall back to breadth.

Then prove it is unique:
```bash
python3 scripts/kg.py similar "<candidate title>"
```
If any score ≥ 0.5, or an existing title/alias names the same thing, pick a different topic. Never write a second article on an existing subject — not a rename, a sub-angle that restates it, a nickname ("the Keystone State" vs. Pennsylvania), an abbreviation (SCOTUS vs. the Supreme Court), a numbered form (Amendment XIV vs. the Fourteenth Amendment) or a "v." spelling variant. Record alternate names, abbreviations and Native-language names as `aliases`.

Choose the right granularity: a war, its key battles and the treaty that ended it are separate nodes (`partOf`, `ledTo`); a state and its largest city are separate nodes (`locatedIn`); a law and the court case that interpreted it are separate nodes (`interprets`). A popular myth gets its own `Myth` node rather than a paragraph buried in the real topic.

Sibling graphs cover neighbouring ground: art movements and artworks belong mainly to `john1hsu/art-history`, business concepts to `john1hsu/business-knowledge-graph`, and AWS and Salesforce topics to their own graphs. Write here when the topic is about the United States itself (e.g. the Hudson River School as an American movement, Silicon Valley as a region and industry), and link a sibling article with `sameAs` (its https URL) when it is the same subject.

## 3. Research
- Run several web searches and read the actual pages (WebFetch). Don't rely on snippets or memory — names, dates, vote counts and figures must come from a page you opened this run.
- Collect 3–6 credible sources: ≥ 1 scholarly and ≥ 2 strong (see `SCHEMA.md`). Prefer **primary sources** (National Archives and its Founding Documents, Founders Online, the Library of Congress, the Avalon Project at Yale, Congress.gov and the Constitution Annotated, Supreme Court opinions), **official sources** (National Park Service, Census Bureau, USGS, BLS/BEA, the State Department's Office of the Historian, the House and Senate historians, state archives and state government sites, and tribal nations' own official sites), and **scholarly ones** (American National Biography, the Oxford Research Encyclopedia of American History, state encyclopedias such as the Handbook of Texas, Encyclopedia Virginia and NCpedia, the Miller Center, the Gilder Lehrman Institute, Oyez, OpenStax U.S. History, *The American Yawp*, peer-reviewed journals, the Smithsonian and presidential libraries). **Never cite Wikipedia, quotation sites, Find a Grave, Reddit/Quora, SEO statistics aggregators** or the other banned sources.
- Every URL you cite must be one you opened this run. Never invent a URL, DOI or Wikidata id. Only add `sameAs: [wd:Q…]` if you opened that Wikidata page and it is the same subject.
- **Dates and numbers.** Give exact dates where the record has them (`start`, `end`, `timeline`), and say "about" or "c." in prose when it doesn't. Every statistic (population, area, GDP, casualties, vote counts) names its source and year — "2020 census", "BEA, 2024" — and current figures come from the official agency. Prefer durable figures; don't write "currently" without a year.
- **Quotations.** Famous lines are often misattributed to founders and presidents. Quote only from the primary text (cite the document, and section or line where it helps) or a scholarly source that verifies it; flag paraphrases and misattributions. No quotation longer than 15 words; at most one quote per source. Paraphrase everything else.
- **Myths and debates.** Check popular stories against the record. A claim the evidence contradicts gets its own `Myth` node (`evidenceStatus: myth`) with a `challengedBy` edge. Where historians genuinely disagree about causes, motives or significance, use `interpretive`, add a `## Debates and interpretations` section, and present each major view fairly with its own source.
- **Fairness and accuracy.** Tell American history whole: include Native nations, enslaved and free Black Americans, women, immigrants and other communities as participants with their own sources and perspectives, and name injustices — slavery, removal, segregation, exclusion, incarceration — plainly rather than in euphemism. Use the names nations and communities use for themselves, and say when a name has changed. Describe political parties, ideologies and current controversies even-handedly: report what each side has said and done, with sources for each, and don't take a side, rank figures or editorialize.

## 4. Write the node
```bash
python3 scripts/kg.py new <domain> <slug> <Type>   # scaffold with the fields and sections the class requires
```
- 400–1,000 words, for a curious general reader: what it is, the background, what happened or how it works, why it matters, and **Connections**; plus the sections its class requires (`SCHEMA.md`). Where relevant, connect it to the present day and to how it is remembered.
- `start`/`end` are required for eras, events, conflicts, documents, laws, court cases, people (birth/death), states (statehood) and movements. `timeline` (≥ 3 dated entries, in order) is required for eras, conflicts and movements and welcome anywhere a sequence matters. `misconception` (myth / fact / why) is required for `Myth` nodes and welcome wherever a popular misconception exists.
- `review`: ≥ 2 questions with answers, each answerable from the article itself — favour *why* and *how* questions and cause-and-effect over trivia.
- Every substantive paragraph carries footnote citations `[^sN]`; list every source in `## Sources`.
- Edges: 1–3 `broader`, `related` as needed, `requires` for genuine background (Reconstruction requires the Civil War), and ≥ 1 (ideally 2–5) typed `relations`, **each citing the source that supports it** and a confidence. Use `occurredDuring`/`occurredIn` to place happenings in time and space, `ledTo` for consequences, `partOf` for battles within wars, `establishes`/`enactedBy`/`amends`/`interprets`/`overturns`/`protects` for law, and `heldOffice`, `participatedIn`, `foundedBy`, `ledBy`, `authoredBy` for people. Link to existing ids wherever they fit (`graph/index.json`); new target ids are fine and join the frontier. Match each predicate's domain and range (`SCHEMA.md`). Never write inverses — the reasoner adds them.
- If a needed class or predicate is missing, add it to `ontology/ontology.ttl` (label, domain/range, inverse/characteristics) in the same commit. Keep the ontology small; reuse first.
- Back-links: if `graph/suggested-links.md` or the new node shows an existing article should point to it, you may add the id to that article's `related` (or a sourced typed relation). Don't otherwise rewrite existing articles.

## 5. Validate, build, commit, push
```bash
python3 scripts/kg.py build    # fix every problem (structure, citations, dates, reasoning contradictions, SHACL) and re-run until OK
git add -A
git commit -m "Add <Title> (<domain>, <mode> run)"
git pull --rebase origin main && python3 scripts/kg.py build && git push origin main
```
If the push is rejected, pull --rebase, rebuild, and push again (once). Commit regenerated `graph/` files with the article; CI fails if they are stale.

## Don'ts
- Don't add more than one article per run, delete articles, or rewrite history.
- Don't commit if validation fails; leave the repo clean.
- Don't cite a source you didn't open, attach a source to an edge it doesn't support, or attribute a quotation you couldn't verify.
- Don't hand-edit anything in `graph/`.
- Don't take partisan sides, endorse or criticise candidates or parties, or present one side of a live political dispute as settled. Don't write about elections, cases or legislation still in progress; wait until results are certified or decisions are final, and use official sources for them.
- Don't write articles about private individuals, or include living people's personal details beyond their documented public role.
- Don't use stereotypes or caricatures of any people, region or community, in prose or examples.

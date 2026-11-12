# USA Graph

A growing, citation-backed knowledge graph about the United States of America: its land and places, the Native nations, its history from before colonization to today, the Constitution, government, rights and elections, the people who shaped it, and its economy, society, culture, science and symbols. A scheduled run researches one new topic, writes it as a sourced node with dates, a timeline, review questions and evidenced, typed edges, and only commits it if the validator, the OWL reasoner and the SHACL shapes all agree it is sound.

**Read it online: https://john1hsu.github.io/usa-graph/** (rebuilt automatically on every new article by `.github/workflows/pages.yml` from `site/build.py`).

Start with **[`graph/timeline.md`](graph/timeline.md)** — every dated article and key moment in one chronology — and **[`graph/study-guide.md`](graph/study-guide.md)**, which collects every review question (with its answer) and every myth-versus-fact, grouped by domain.

## Architecture

```
articles/<domain>/<slug>.md          Markdown + YAML frontmatter (one node each)
        │  scripts/kg.py
        ▼
 1. structural validation      citations, dates, uniqueness (shingles + TF-IDF), study-aid rules, acyclicity
 2. RDF assembly               SKOS + PROV-O + schema.org dates + timelines, review Q&A and myth/fact, one named graph per article
 3. OWL 2 RL reasoning         inverse / symmetric / transitive properties, domain & range typing
 4. consistency checking       disjoint-class contradictions, domain/range violations
 5. SHACL validation           ontology/shapes.ttl (semantic contract on the exported RDF)
 6. exports + analytics        graph/  (regenerated on every commit; CI fails if stale)
```

| Layer | What | Where |
|---|---|---|
| Ontology | OWL 2 RL classes (State, City, NaturalFeature, Landmark, Era, Event, Conflict, Document, Law, CourtCase, Right, Principle, Policy, Movement, Person, Institution, Office, TribalNation, Community, Tradition, Symbol, Myth, …) and typed relations (`occurredDuring`, `occurredIn`, `ledTo`, `locatedIn`, `borders`, `establishes`, `enactedBy`, `amends`, `interprets`, `overturns`, `protects`, `heldOffice`, `participatedIn`, `commemorates`, `challengedBy`, …) with inverses, symmetry, transitivity, domains, ranges and disjointness; aligned with SKOS, PROV-O and schema.org | `ontology/ontology.ttl` |
| Shapes | SHACL: every node defined, sourced, levelled, evidence-rated and with ≥ 2 review questions; happenings, documents, people, states and movements dated; eras, conflicts and movements carry a timeline; myths carry a myth/fact block | `ontology/shapes.ttl` |
| Nodes | One Markdown article per entity: id, class, dates, hierarchy, background reading, evidenced typed edges, timeline, myth/fact, review Q&A, evidence status, entity links and sources | `articles/<domain>/` |
| Timeline | One chronology of every dated article and timeline entry | `graph/timeline.md` |
| Study guide | Every review question with its answer, and every myth vs. fact | `graph/study-guide.md` |
| Linked data | N-Triples (asserted and OWL-RL inferred), TriG with per-article named graphs and provenance, Turtle-star edge evidence (RDF 1.2), JSON-LD, JSON index | `graph/triples.nt`, `graph/inferred.nt`, `graph/graph.trig`, `graph/edge-evidence.ttls`, `graph/graph.jsonld`, `graph/index.json` |
| Analytics | PageRank, betweenness, Louvain communities, k-core, coverage by type/domain/level/evidence | `graph/stats.md` |
| Frontier | Unwritten nodes ranked by referrers weighted by their centrality, with the **type the reasoner expects** | `graph/frontier.md` |
| Link prediction | Adamic-Adar scores for written nodes that should probably be connected | `graph/suggested-links.md` |
| Competency questions | SPARQL over asserted + inferred triples: most consequential events, happenings by era, rights and what protects them, what founding texts established, office holders, myths and debates; *gap* queries (events with no recorded consequences, unprotected rights, unanchored laws and cases, places with nothing tied to them, people with no recorded role, orphans) drive gap-filling runs | `queries/*.rq` → `graph/competency.md` |
| Learning path | Topological layers of the `requires` background-reading DAG | `graph/learning-path.md` |

## What makes it more than a link list

- **Sourced to the record.** Every paragraph and every typed edge cites a source, with a strong preference for primary documents (National Archives, Library of Congress, Congress.gov, Supreme Court opinions), official agencies (NPS, Census, Office of the Historian, tribal governments) and scholarly references.
- **Evidence-aware.** Every node has an `evidenceStatus` (established, interpretive, contested, myth, legal-text, statistical, tradition), so settled facts, historians' debates, the text of the law, official statistics and folklore are never confused. Popular myths get their own nodes, linked to the evidence that challenges them.
- **Time-aware.** Dated nodes publish `schema:startDate`/`endDate`; eras, wars and movements carry timelines; everything merges into one site-wide chronology.
- **Study-ready.** Every article ends with review questions and answers; myths come with the fact that replaces them.
- **Reasoning, not just storage.** Writers state one direction (`Brown v. Board overturns Plessy v. Ferguson`); the OWL-RL reasoner materialises `overturnedBy`, symmetric `borders`, transitive `locatedIn`, and types unwritten nodes from property ranges (anything `protects` points at is a Right). Contradictory typing fails the build.
- **Self-directing growth.** Runs rotate between depth (frontier), breadth (least-covered domain) and gap (SPARQL competency gaps).
- **Reproducible.** Outputs are byte-for-byte deterministic; CI re-runs tests and the build and fails if `graph/` is stale.

## Usage

```bash
pip install -r requirements.txt
python3 scripts/kg.py check                          # validate + reason + SHACL
python3 scripts/kg.py build                          # ...and regenerate graph/
python3 scripts/kg.py similar "Amendment XIV"        # duplicate check for a candidate topic
python3 scripts/kg.py new civil-war-and-reconstruction reconstruction Era   # scaffold
python3 scripts/kg.py query queries/05-happenings-by-era.rq       # or an inline SPARQL string
python3 -m pytest -q tests                           # end-to-end tests on fixture articles
```

Steer what gets written by editing `topics/seeds.yaml`. The run playbook is `CLAUDE.md`; the article format is `SCHEMA.md`. The `.nt`, `.trig` and `.jsonld` exports load into Apache Jena/Fuseki, GraphDB, Oxigraph, rdflib, or Neo4j via n10s; `.ttls` needs an RDF 1.2 / RDF-star aware store.

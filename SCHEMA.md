# Article schema

Each article is one **node**: `articles/<domain>/<slug>.md`, where the filename equals the id's slug and `<domain>` is a key in `topics/seeds.yaml`. Scaffold one with `python3 scripts/kg.py new <domain> <slug> <Type>`, which pre-fills the fields and sections its class needs.

```markdown
---
id: us:battle-of-gettysburg              # us: + lowercase-hyphen slug; never changes
type: Conflict                           # most specific class from ontology/ontology.ttl
title: Battle of Gettysburg
aliases: [Gettysburg]
domain: civil-war-and-reconstruction     # key in topics/seeds.yaml (becomes a SKOS ConceptScheme)
summary: >-                              # 1–2 sentence definition (skos:definition)
  A three-day battle of the American Civil War fought around Gettysburg, Pennsylvania, in July 1863 that ended in a Union victory.
level: introductory                      # introductory | intermediate | advanced
evidenceStatus: established              # see table below
start: 1863-07-01                        # YYYY, YYYY-MM or YYYY-MM-DD; -1000 for 1000 BCE -> schema:startDate
end: 1863-07-03                          # optional -> schema:endDate
broader: [us:civil-war-battles]          # skos:broader, 1–3; must stay acyclic
related: [us:gettysburg-address]         # skos:related (symmetric)
requires: [us:american-civil-war]        # background needed to understand it (transitive, acyclic) -> graph/learning-path.md
relations:                               # typed edges: EVERY one cites a source id below
  - {predicate: partOf, object: us:american-civil-war, source: s1, confidence: high}
  - {predicate: occurredIn, object: us:pennsylvania, source: s1}              # confidence defaults to medium
  - {predicate: ledBy, object: us:george-meade, source: s2}
  - {predicate: ledTo, object: us:gettysburg-address, source: s3}
timeline:                                # Era, Conflict, Movement: >= 3 entries, chronological
  - {date: 1863-07-01, event: Confederate forces drive Union troops back through the town.}
  - {date: 1863-07-02, event: Fighting on the Union flanks at Little Round Top and Culp's Hill.}
  - {date: 1863-07-03, event: Pickett's Charge fails and Lee's army begins to withdraw.}
misconception:                           # Myth: required; optional anywhere else
  myth: Gettysburg was the bloodiest single day of the war.
  fact: Antietam (September 17, 1862) was the bloodiest single day; Gettysburg was the costliest battle overall.
  why: Mixing up "battle" and "day" distorts how the war's turning points are remembered.
review:                                  # every article: >= 2, each answerable from the article
  - question: Why is Gettysburg often called a turning point of the Civil War?
    answer: It ended Lee's second invasion of the North, and with the fall of Vicksburg a day later shifted momentum to the Union.
  - question: How did the battle lead to the Gettysburg Address?
    answer: The dead were buried in a new national cemetery there, which Lincoln helped dedicate in November 1863.
sameAs: []                               # optional entity links: Wikidata QIDs or https IRIs (incl. sibling graphs) -> skos:exactMatch
sources:                                 # >= 3; >= 2 strong; >= 1 scholarly
  - id: s1
    title: "Gettysburg National Military Park: History & Culture"
    publisher: National Park Service
    url: https://www.nps.gov/...
    type: government
    accessed: 2026-11-12
created: 2026-11-12
modified: 2026-11-20                     # optional; set when an article is revised
---

# Battle of Gettysburg

Prose with footnote citations after each claim.[^s1]

## Background            (class-specific sections: see table below)
## What happened
## Aftermath and legacy
## Debates and interpretations   (when evidenceStatus is interpretive or contested)
## Connections           (always: explain each edge in prose, with citations)
## Sources               (always)
[^s1]: National Park Service, "Gettysburg National Military Park: History & Culture". https://... (accessed 2026-11-12)
```

## Classes (`type`) and their required sections

| Class | Use for | Required sections (plus Connections, Sources) |
|---|---|---|
| `Concept` | general ideas: the American Dream, the frontier, sectionalism | Origins, Significance |
| `Principle` | constitutional principles and doctrines: separation of powers, federalism, judicial review | Origins, How it works |
| `Right` | rights and civil liberties: freedom of speech, the right to vote, due process, equal protection | Origins, How it works |
| `Policy` | policies, doctrines and programs: the New Deal, the Monroe Doctrine, containment, Social Security | Origins, How it works |
| `Movement` | movements: abolitionism, women's suffrage, the labor movement, the civil rights movement | Origins, Goals and methods, Outcomes |
| `Tradition` | customs, holidays, art forms, sports, foodways: Thanksgiving, jazz, baseball, barbecue | Origins, Meaning and practice |
| `Symbol` | national symbols: the flag, the Great Seal, the bald eagle, the national motto | Origins, Meaning and practice |
| `Industry` | economic sectors: railroads, steel, automobiles, aerospace, technology | History, Today |
| `Interpretation` | historians' theses: Turner's frontier thesis, American exceptionalism as an idea | The argument, Critiques |
| `Myth` | popular claims the evidence contradicts: Washington's wooden teeth, Betsy Ross's flag | The myth, What the evidence shows, Why it persists |
| `Field` | disciplines: American studies, constitutional law, Native American and Indigenous studies | Origins, Significance |
| `Country`, `State`, `Territory`, `Region`, `City` | the U.S. and its neighbours; the 50 states; DC and the territories; New England, the Midwest; cities and towns | Geography, History, Today |
| `NaturalFeature` | rivers, lakes, mountains, canyons, ecosystems | Geography, Human history |
| `Landmark` | built or designated sites: the Statue of Liberty, Independence Hall, national parks and historic sites | History, Significance |
| `Era` | periods: the colonial era, Reconstruction, the Gilded Age, the Cold War | Background, Key developments, Legacy |
| `Event`, `Conflict` | dated events; wars, battles and rebellions | Background, What happened, Aftermath and legacy |
| `Document` | founding and political texts, speeches, treaties, proclamations | Background, What it says, Legacy |
| `Law` | statutes, amendments, executive orders | Background, What it says, Legacy |
| `CourtCase` | court decisions | Background, The decision, Legacy |
| `Work` | books, songs, films, artworks | Background, About the work, Reception and legacy |
| `Person` | presidents, founders, activists, inventors, artists | Life and work, Legacy |
| `Institution`, `Office` | government bodies and agencies; public offices | Origins, Powers and structure |
| `Organization` | parties, unions, companies, advocacy groups | History, Role |
| `TribalNation` | Native nations, named as they name themselves | History, Government and sovereignty, Today |
| `Community` | immigrant, ethnic, religious and social communities | History, Today |

`Conflict` is a kind of `Event`; `Law` and `CourtCase` are kinds of `Document`; `Era`, `Event` and `Conflict` are `Happening`s; the place classes are `Place`s. Disjointness is declared (ideas vs. places vs. happenings vs. texts vs. people vs. organizations vs. institutions vs. offices vs. Native nations vs. communities; states vs. cities vs. regions vs. natural features vs. countries; eras vs. events; myths vs. rights vs. policies vs. movements vs. principles). The reasoner types unwritten nodes from edge ranges; two edges that imply incompatible types fail the build.

**Dated classes** (`Happening`, `Document`, `Person`, `State`, `Movement`) need `start`. **Timeline classes** (`Era`, `Conflict`, `Movement`) need ≥ 3 timeline entries. **`Myth`** needs a `misconception` block. **Every article** needs ≥ 2 `review` questions with answers.

## Predicates (`relations[].predicate`)

| Predicate | Meaning | Constraint | Inferred inverse |
|---|---|---|---|
| `partOf` | component of (a battle in a war, an office in a body) | transitive | `hasPart` |
| `requires`* | background needed to understand it | transitive, acyclic | `prerequisiteOf` |
| `instanceOf` | an example or kind of | | `hasInstance` |
| `contrastsWith`, `confusedWith` | comparisons | symmetric | itself |
| `locatedIn` | geographic containment | transitive, → Place | `contains` |
| `borders` | shares a border | symmetric, Place → Place | itself |
| `capitalOf` | capital city of | → Place | `hasCapital` |
| `occurredDuring` | happened during an era | → Era | `periodOf` |
| `occurredIn` | took place in | Happening → Place | `siteOf` |
| `ledTo` | led to / contributed to | | `resultedFrom` |
| `establishedBy` | created by a document or law | → Document | `establishes` |
| `enactedBy` | enacted or ratified by | Law → Institution | `enacted` |
| `signedBy` | signed by | Document → Person | `signed` |
| `amends` | amends | Law → Document | `amendedBy` |
| `interprets` | interprets a text or clause | CourtCase → | `interpretedIn` |
| `overturns` | overturns or supersedes | Document → Document | `overturnedBy` |
| `protects` | protects or guarantees a right | → Right | `protectedBy` |
| `heldOffice` | held a public office | Person → Office | `officeHolder` |
| `memberOf` | member of | | `hasMember` |
| `foundedBy`, `ledBy` | founded / led or commanded by | → Person | `founded`, `led` |
| `participatedIn` | took part in | → Happening or Movement | `participant` |
| `affected` | affected or shaped | | `affectedBy` |
| `originatedIn` | originated in or among | → Place, Community or TribalNation | `originOf` |
| `symbolizes`, `commemorates` | stands for / memorializes | | `symbolizedBy`, `commemoratedBy` |
| `supportedBy`, `challengedBy` | evidence for / against (myth-busting, critiques) | | `supports`, `challenges` |
| `introducedBy` | proposed, coined or introduced by | → Person | `introduced` |
| `introducedIn` | first set out in | → Document or Work | `introduces` |
| `authoredBy` | written or created by | Document or Work → Person | `authored` |
| `influencedBy` | influenced by | | `influenced` |
| `studiedIn` | studied in a discipline | → Field | |

\* `requires` is written as its own list, not under `relations`. Never write inverses yourself; the reasoner materialises them in `graph/inferred.nt`. If you need a new predicate or class, add it to `ontology/ontology.ttl` with a label, any domain/range, and its inverse/characteristics in the same commit.

## Evidence status

| value | meaning | rule |
|---|---|---|
| `established` | well documented in primary records and scholarly consensus | |
| `interpretive` | the facts are settled but historians disagree about causes, motives or significance | needs ≥ 2 scholarly source types and a `## Debates and interpretations` section |
| `contested` | a factual claim in active dispute | needs ≥ 2 scholarly source types, a `challengedBy` relation and a `## Debates and interpretations` section |
| `myth` | a popular claim the evidence contradicts | `Myth` nodes only; needs ≥ 2 scholarly source types and a `challengedBy` relation |
| `legal-text` | what a law, ruling, founding document or official rule says | documents, laws, cases, rights, principles, offices, institutions, policies; needs a `primary` or `government` source |
| `statistical` | current figures from official statistics (with the year) | needs a `government` source |
| `tradition` | a custom, legend or folklore described as such | |

## Source types

| type | strong | scholarly | examples |
|---|---|---|---|
| `primary` | yes | yes | National Archives, Founders Online, Library of Congress collections, Avalon Project, Congress.gov bill text, Supreme Court opinions |
| `government` | yes | yes | National Park Service, Census Bureau, USGS, BLS/BEA, Office of the Historian, House/Senate historians, state archives, tribal nations' official sites |
| `academic` | yes | yes | Miller Center, Gilder Lehrman Institute, Oyez, university history departments |
| `scholarly-encyclopedia` | yes | yes | American National Biography, Oxford Research Encyclopedia of American History, Handbook of Texas, Encyclopedia Virginia, NCpedia |
| `textbook` | yes | yes | OpenStax U.S. History, *The American Yawp*, OpenStax American Government |
| `peer-reviewed` | yes | yes | *Journal of American History*, *American Historical Review*, *William and Mary Quarterly* (DOI page) |
| `museum` | yes | yes | Smithsonian museums, presidential libraries, Mount Vernon, Monticello, historical societies |
| `intergovernmental` | yes | yes | UNESCO World Heritage, United Nations |
| `institutional` | yes | no | National Constitution Center, Pew Research Center, Bill of Rights Institute |
| `magazine` | yes | no | *Smithsonian* magazine, *American Heritage* |
| `encyclopedia` | yes | no | Britannica |
| `news`, `community` | no | no | context only, never the sole support for a claim |

**Banned:** Wikipedia (and mirrors), Wikiquote, Conservapedia, RationalWiki, wikiHow, Quora, Reddit, Fandom, Find a Grave, Genius, SEO statistics aggregators (World Population Review), quotation aggregators (BrainyQuote, Goodreads quotes, AZ Quotes…), content farms and AI-generated pages.

## Enforcement summary (`scripts/kg.py check`)

1. **Structure:** required fields, enums, id/filename/folder agreement, known domain, dates (valid format, start before end, not in the future).
2. **Citations:** ≥ 3 sources, ≥ 2 strong, ≥ 1 scholarly, https only, no banned or duplicate URLs, every source cited, every substantive paragraph cited, every typed edge cites a source; evidence-status source rules above.
3. **Study aids:** class-specific sections; `start` for dated classes; ≥ 3 chronological timeline entries for eras, conflicts and movements; a myth/fact/why block for myths; ≥ 2 review questions with real answers for every article; `challengedBy` for contested claims and myths.
4. **Graph rules:** ≥ 3 edges and ≥ 1 typed relation per node, domain/range on written targets, no cycles in `broader` / `requires` / `partOf`.
5. **Uniqueness:** no shared ids, titles or aliases; no near-identical titles; no copied text (5-gram shingles); no same-topic rewrite (TF-IDF cosine ≥ 0.80; ≥ 0.60 warns).
6. **Reasoning:** OWL 2 RL closure; any node inferred into two disjoint classes fails.
7. **SHACL:** `ontology/shapes.ttl` over the exported RDF with RDFS inference.

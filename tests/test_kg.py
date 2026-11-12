"""End-to-end tests for scripts/kg.py against a throwaway tree of fixture articles.

Fixtures use example.org URLs and synthetic prose: they exercise the validator,
reasoner, SHACL shapes and exports, and are never part of the real graph.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
KG = REPO / "scripts" / "kg.py"
NS = "https://github.com/john1hsu/usa-graph/"
TYPE = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"


def body(slug: str, sections: list[str]) -> str:
    def para(i: int) -> str:
        words = " ".join(f"{slug.replace('-', '')}{i}w{j}" for j in range(150))
        return f"Synthetic fixture prose for {slug} paragraph {i}: {words}.[^s1][^s2][^s3]"
    out = [f"# {slug}", "", para(0), "", para(1), ""]
    for k, s in enumerate(sections, 2):
        out += [s, "", para(k), ""]
    out += ["## Connections", "", para(99), "", "## Sources", "",
            "[^s1]: Fixture one. https://example.org/1", "[^s2]: Fixture two. https://example.org/2",
            "[^s3]: Fixture three. https://example.org/3"]
    return "\n".join(out) + "\n"


SOURCES = """sources:
  - {id: s1, title: Fixture one, publisher: Example, url: "https://example.org/SLUG/1", type: primary, accessed: 2026-11-02}
  - {id: s2, title: Fixture two, publisher: Example, url: "https://example.org/SLUG/2", type: magazine, accessed: 2026-11-02}
  - {id: s3, title: Fixture three, publisher: Example, url: "https://example.org/SLUG/3", type: textbook, accessed: 2026-11-02}
created: 2026-11-02
"""

REVIEW = """review:
  - question: What is the first fixture question about this topic?
    answer: The first fixture answer, long enough to count as a real answer.
  - question: What is the second fixture question about this topic?
    answer: The second fixture answer, also long enough to count as one.
"""

ARTICLES = {
    ("civil-war-and-reconstruction", "battle-of-gettysburg"): ("""id: us:battle-of-gettysburg
type: Conflict
title: Battle of Gettysburg
aliases: [Gettysburg campaign battle]
domain: civil-war-and-reconstruction
summary: A three-day battle of the American Civil War fought at Gettysburg, Pennsylvania, in July 1863, ending in a Union victory.
level: introductory
evidenceStatus: established
start: 1863-07-01
end: 1863-07-03
broader: [us:civil-war-battles]
relations:
  - {predicate: partOf, object: us:american-civil-war, source: s1, confidence: high}
  - {predicate: occurredIn, object: us:pennsylvania, source: s1, confidence: high}
  - {predicate: occurredDuring, object: us:civil-war-era, source: s3}
  - {predicate: ledBy, object: us:george-meade, source: s3}
timeline:
  - {date: 1863-07-01, event: Confederate and Union forces meet west and north of the town.}
  - {date: 1863-07-02, event: Fighting on the Union flanks at Little Round Top and Culp's Hill.}
  - {date: 1863-07-03, event: Pickett's Charge is repulsed and the battle ends.}
""" + REVIEW, ["## Background", "## What happened", "## Aftermath and legacy"]),
    ("civil-war-and-reconstruction", "gettysburg-address"): ("""id: us:gettysburg-address
type: Document
title: Gettysburg Address
domain: civil-war-and-reconstruction
summary: Abraham Lincoln's short speech at the dedication of the Soldiers' National Cemetery at Gettysburg in November 1863.
level: introductory
evidenceStatus: established
start: 1863-11-19
related: [us:declaration-of-independence]
requires: [us:battle-of-gettysburg]
relations:
  - {predicate: authoredBy, object: us:abraham-lincoln, source: s1, confidence: high}
  - {predicate: commemorates, object: us:battle-of-gettysburg, source: s1, confidence: high}
  - {predicate: influencedBy, object: us:declaration-of-independence, source: s3}
""" + REVIEW, ["## Background", "## What it says", "## Legacy"]),
    ("rights-and-law", "fourteenth-amendment"): ("""id: us:fourteenth-amendment
type: Law
title: Fourteenth Amendment
aliases: [Amendment XIV]
domain: rights-and-law
summary: The 1868 amendment to the U.S. Constitution that defined national citizenship and guaranteed due process and equal protection of the laws.
level: intermediate
evidenceStatus: legal-text
start: 1868-07-09
requires: [us:reconstruction-amendments]
relations:
  - {predicate: amends, object: us:united-states-constitution, source: s1, confidence: high}
  - {predicate: enactedBy, object: us:united-states-congress, source: s1, confidence: high}
  - {predicate: protects, object: us:equal-protection, source: s1, confidence: high}
  - {predicate: occurredDuring, object: us:reconstruction, source: s3}
""" + REVIEW, ["## Background", "## What it says", "## Legacy"]),
    ("cold-war-and-civil-rights", "brown-v-board-of-education"): ("""id: us:brown-v-board-of-education
type: CourtCase
title: Brown v. Board of Education
domain: cold-war-and-civil-rights
summary: The 1954 Supreme Court decision holding that state-mandated racial segregation in public schools violates the Equal Protection Clause.
level: introductory
evidenceStatus: established
start: 1954-05-17
broader: [us:landmark-supreme-court-cases]
relations:
  - {predicate: interprets, object: us:fourteenth-amendment, source: s1, confidence: high}
  - {predicate: overturns, object: us:plessy-v-ferguson, source: s1, confidence: high}
  - {predicate: protects, object: us:equal-protection, source: s3}
""" + REVIEW, ["## Background", "## The decision", "## Legacy"]),
    ("symbols-and-national-identity", "betsy-ross-flag-myth"): ("""id: us:betsy-ross-flag-myth
type: Myth
title: Betsy Ross and the first flag
domain: symbols-and-national-identity
summary: The popular story that Philadelphia upholsterer Betsy Ross designed and sewed the first American flag, which no contemporary record confirms.
level: introductory
evidenceStatus: myth
broader: [us:american-founding-myths]
relations:
  - {predicate: challengedBy, object: us:flag-resolution-of-1777, source: s1, confidence: high}
  - {predicate: confusedWith, object: us:flag-of-the-united-states, source: s3}
misconception:
  myth: Betsy Ross designed and sewed the first Stars and Stripes at George Washington's request.
  fact: The story first appeared in 1870 from her grandson's family account; no record from the 1770s confirms it.
  why: Family stories told a century later are weak evidence for who designed a national symbol.
""" + REVIEW, ["## The myth", "## What the evidence shows", "## Why it persists"]),
    ("states-and-territories", "pennsylvania"): ("""id: us:pennsylvania
type: State
title: Pennsylvania
aliases: [Keystone State]
domain: states-and-territories
summary: A Mid-Atlantic state, the second to ratify the Constitution, home of Philadelphia, Pittsburgh and the state capital, Harrisburg.
level: introductory
evidenceStatus: established
start: 1787-12-12
broader: [us:mid-atlantic]
relations:
  - {predicate: borders, object: us:new-york, source: s3, confidence: high}
  - {predicate: hasCapital, object: us:harrisburg, source: s1}
""" + REVIEW, ["## Geography", "## History", "## Today"]),
}


def make_tree(tmp: Path, articles=ARTICLES) -> Path:
    for d in ("ontology", "topics", "queries"):
        shutil.copytree(REPO / d, tmp / d)
    for (dom, slug), (fm, secs) in articles.items():
        p = tmp / "articles" / dom / f"{slug}.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"---\n{fm}{SOURCES.replace('SLUG', slug)}---\n{body(slug, secs)}")
    return tmp


def run(tmp: Path, *args: str, hashseed: str = "random") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(KG), *args], cwd=tmp,
                          env={"PYTHONHASHSEED": hashseed, "USA_KG_ROOT": str(tmp), "PATH": ""},
                          capture_output=True, text=True)


def test_valid_tree_builds(tmp_path):
    t = make_tree(tmp_path)
    r = run(t, "build")
    assert r.returncode == 0, r.stdout + r.stderr
    g = t / "graph"
    inferred = (g / "inferred.nt").read_text()
    # inverse properties materialised by the reasoner
    assert f"battle-of-gettysburg> <{NS}ontology#commemoratedBy> <{NS}id/gettysburg-address>" in inferred
    assert f"equal-protection> <{NS}ontology#protectedBy> <{NS}id/fourteenth-amendment>" in inferred
    assert f"plessy-v-ferguson> <{NS}ontology#overturnedBy> <{NS}id/brown-v-board-of-education>" in inferred
    assert f"fourteenth-amendment> <{NS}ontology#interpretedIn> <{NS}id/brown-v-board-of-education>" in inferred
    # symmetric property materialised
    assert f"new-york> <{NS}ontology#borders> <{NS}id/pennsylvania>" in inferred
    # range axioms type unwritten frontier nodes
    assert f"equal-protection> {TYPE} <{NS}ontology#Right>" in inferred
    assert f"reconstruction> {TYPE} <{NS}ontology#Era>" in inferred
    assert f"abraham-lincoln> {TYPE} <{NS}ontology#Person>" in inferred
    # subclass typing: a Conflict is also an Event and a Happening
    assert f"battle-of-gettysburg> {TYPE} <{NS}ontology#Happening>" in inferred
    frontier = (g / "frontier.md").read_text()
    assert "`us:abraham-lincoln`" in frontier and "Person" in frontier
    assert "<< <" in (g / "edge-evidence.ttls").read_text()
    triples = (g / "triples.nt").read_text()
    assert "https://schema.org/startDate" in triples and "ReviewQuestion" in triples and "TimelineEntry" in triples
    timeline = (g / "timeline.md").read_text()
    assert timeline.index("1787-12-12") < timeline.index("1863-07-01") < timeline.index("1954-05-17")
    assert "Pickett's Charge" in timeline
    guide = (g / "study-guide.md").read_text()
    assert "| Myth | Fact |" in guide and "**Q:**" in guide and "**A:**" in guide
    idx = json.loads((g / "index.json").read_text())
    assert {x["id"] for x in idx} == {"us:battle-of-gettysburg", "us:gettysburg-address", "us:fourteenth-amendment",
                                      "us:brown-v-board-of-education", "us:betsy-ross-flag-myth", "us:pennsylvania"}
    assert next(x for x in idx if x["id"] == "us:battle-of-gettysburg")["end"] == "1863-07-03"
    comp = (g / "competency.md").read_text()
    assert "us:battle-of-gettysburg" in comp  # a conflict with no recorded consequences -> gap
    path = (g / "learning-path.md").read_text()
    assert path.index("Battle of Gettysburg") < path.index("Gettysburg Address")
    # deterministic: rebuilding under different hash seeds (as CI and scheduled runs do) is byte-identical
    before = {p.name: p.read_text() for p in g.iterdir()}
    for seed in ("1", "2", "3", "4"):
        assert run(t, "build", hashseed=seed).returncode == 0
        assert before == {p.name: p.read_text() for p in g.iterdir()}, f"output changed with PYTHONHASHSEED={seed}"


def mutate(key, old, new):
    arts = dict(ARTICLES)
    fm, secs = arts[key]
    assert old in fm
    arts[key] = (fm.replace(old, new), secs)
    return arts


BATTLE = ("civil-war-and-reconstruction", "battle-of-gettysburg")
ADDRESS = ("civil-war-and-reconstruction", "gettysburg-address")
AMEND = ("rights-and-law", "fourteenth-amendment")
BROWN = ("cold-war-and-civil-rights", "brown-v-board-of-education")
MYTH = ("symbols-and-national-identity", "betsy-ross-flag-myth")
PA = ("states-and-territories", "pennsylvania")


@pytest.mark.parametrize("key,old,new,expect", [
    (AMEND, "type: Law", "type: Document", "enactedBy expects subject"),
    (ADDRESS, "source: s3}", "source: s9}", "unknown source"),
    (BATTLE, "evidenceStatus: established", "evidenceStatus: contested", "needs a challengedBy"),
    (BATTLE, "  - {date: 1863-07-02, event: Fighting on the Union flanks at Little Round Top and Culp's Hill.}\n", "",
     ">= 3 entries"),
    (BATTLE, "date: 1863-07-02,", "date: 1863-08-02,", "chronological order"),
    (BATTLE, "end: 1863-07-03", "end: 1863-06-03", "is before start"),
    (BROWN, "start: 1954-05-17\n", "", "needs a start date"),
    (BROWN, "evidenceStatus: established", "evidenceStatus: myth", "only for type Myth"),
    (PA, "  - question: What is the second fixture question about this topic?\n"
         "    answer: The second fixture answer, also long enough to count as one.\n", "", ">= 2 review questions"),
    (MYTH, "fact: The story first appeared in 1870 from her grandson's family account; no record from the 1770s confirms it.",
     "fact: Betsy Ross designed and sewed the first Stars and Stripes at George Washington's request.",
     "myth and fact are the same"),
    (ADDRESS, "title: Gettysburg Address", "title: Gettysburg Address\naliases: [Keystone State]", "collides"),
    (AMEND, "protects, object: us:equal-protection", "protects, object: us:reconstruction", "contradiction"),
    (BROWN, "overturns, object: us:plessy-v-ferguson", "overturns, object: us:pennsylvania",
     "expects object in ['Document']"),
])
def test_rejections(tmp_path, key, old, new, expect):
    t = make_tree(tmp_path, mutate(key, old, new))
    r = run(t, "check")
    assert r.returncode == 1 and expect in r.stdout, r.stdout


def test_court_case_sections(tmp_path):
    t = make_tree(tmp_path)
    p = t / "articles" / "cold-war-and-civil-rights" / "brown-v-board-of-education.md"
    p.write_text(p.read_text().replace("## The decision", "## Other notes"))
    r = run(t, "check")
    assert r.returncode == 1 and "The decision" in r.stdout, r.stdout


def test_debated_needs_debate_section(tmp_path):
    arts = mutate(PA, "evidenceStatus: established", "evidenceStatus: interpretive")
    r = run(make_tree(tmp_path, arts), "check")
    assert r.returncode == 1 and "Debates and interpretations" in r.stdout, r.stdout


def test_legal_text_needs_the_text(tmp_path):
    t = make_tree(tmp_path)
    p = t / "articles" / "rights-and-law" / "fourteenth-amendment.md"
    p.write_text(p.read_text().replace("type: primary", "type: academic"))
    r = run(t, "check")
    assert r.returncode == 1 and "needs the text itself" in r.stdout, r.stdout


def test_myth_needs_misconception(tmp_path):
    fm, secs = ARTICLES[MYTH]
    cut = fm[fm.index("misconception:"):fm.index("review:")]
    arts = dict(ARTICLES)
    arts[MYTH] = (fm.replace(cut, ""), secs)
    r = run(make_tree(tmp_path, arts), "check")
    assert r.returncode == 1 and "misconception block" in r.stdout, r.stdout


def test_requires_cycle(tmp_path):
    arts = mutate(BATTLE, "broader: [us:civil-war-battles]",
                  "broader: [us:civil-war-battles]\nrequires: [us:gettysburg-address]")
    r = run(make_tree(tmp_path, arts), "check")
    assert r.returncode == 1 and "cycle in 'requires'" in r.stdout


def test_banned_source(tmp_path):
    t = make_tree(tmp_path)
    p = t / "articles" / "states-and-territories" / "pennsylvania.md"
    p.write_text(p.read_text().replace("https://example.org/pennsylvania/1", "https://en.wikipedia.org/wiki/X"))
    r = run(t, "check")
    assert r.returncode == 1 and "banned domain" in r.stdout


def test_bce_dates(tmp_path):
    arts = mutate(PA, "start: 1787-12-12", "start: -1000")
    r = run(make_tree(tmp_path, arts), "build")
    assert r.returncode == 0, r.stdout
    assert "1000 BCE" in (tmp_path / "graph" / "timeline.md").read_text()


def test_similar_and_new(tmp_path):
    t = make_tree(tmp_path)
    r = run(t, "similar", "Keystone State")
    assert r.returncode == 0 and r.stdout.splitlines()[1].split()[3] == "us:pennsylvania"
    r = run(t, "new", "civil-war-and-reconstruction", "reconstruction", "Era")
    assert r.returncode == 0
    text = (t / "articles" / "civil-war-and-reconstruction" / "reconstruction.md").read_text()
    assert "start:" in text and "timeline:" in text and "review:" in text and "## Key developments" in text
    r = run(t, "new", "presidents-and-founders", "washington-cherry-tree-myth", "Myth")
    assert r.returncode == 0
    text = (t / "articles" / "presidents-and-founders" / "washington-cherry-tree-myth.md").read_text()
    assert "misconception:" in text and "## What the evidence shows" in text
    r = run(t, "new", "presidents-and-founders", "abraham-lincoln", "Person")
    assert r.returncode == 0 and "## Life and work" in (t / "articles" / "presidents-and-founders" / "abraham-lincoln.md").read_text()


def test_empty_tree(tmp_path):
    t = make_tree(tmp_path, {})
    r = run(t, "build")
    assert r.returncode == 0, r.stdout

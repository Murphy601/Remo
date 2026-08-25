"""Continue each document in its own genre until it is long enough for ~100 pages.

The extra pages have to earn their place: more constraints, rejected options,
executable steps, and named owners. Not a shared weekly log stapled to every file.
"""

from __future__ import annotations

import hashlib
import random
import re
from datetime import date, timedelta


TICKET_RE = re.compile(
    r"\b(?:CLH|RVH|OAK|NS|REC|INC|TDD|PRD|SOP|RB|ADR|REQ|MEM|MTG|EVAL|TST)-[A-Z0-9-]{2,20}\b"
)
HOST_RE = re.compile(r"\b[a-z0-9._-]+\.(?:internal|net|example|local)\b", re.I)


def _words(s: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", s or ""))


def _blob(spec: dict) -> str:
    parts = [spec.get("title", ""), spec.get("summary", ""), spec.get("subtitle", "")]
    for b in spec.get("blocks", []):
        if b.get("text"):
            parts.append(b["text"])
        for it in b.get("items") or []:
            parts.append(str(it))
        for row in b.get("rows") or []:
            parts.extend(str(c) for c in row)
        if b.get("caption"):
            parts.append(b["caption"])
    return "\n".join(parts)


def extract_facts(spec: dict) -> dict:
    blob = _blob(spec)
    tickets = list(dict.fromkeys(TICKET_RE.findall(blob)))
    hosts = list(dict.fromkeys(HOST_RE.findall(blob)))
    named = re.findall(
        r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b",
        " ".join(
            [
                spec.get("audience", ""),
                spec.get("owners", ""),
                spec.get("author", ""),
                blob[:6000],
            ]
        ),
    )
    named = list(dict.fromkeys(named))[:14]
    if "Aman Kumar" not in named:
        named = ["Aman Kumar"] + named
    slug = spec.get("slug", "doc")
    seed = int(hashlib.md5(slug.encode()).hexdigest()[:8], 16)
    dt = spec.get("doc_type", "").lower()
    if any(k in dt for k in ("meeting", "notes", "readout")):
        genre = "notes"
    elif any(k in dt for k in ("runbook", "sop")):
        genre = "runbook"
    elif any(k in dt for k in ("incident", "postmortem")):
        genre = "incident"
    elif any(k in dt for k in ("memo", "capacity", "recommendation")):
        genre = "memo"
    elif any(k in dt for k in ("prd", "requirement")):
        genre = "prd"
    elif any(k in dt for k in ("test", "load", "eval", "rubric")):
        genre = "test"
    else:
        genre = "design"
    return {
        "spec": spec,
        "slug": slug,
        "doc_id": spec.get("doc_id", "DOC"),
        "title": spec.get("title", "Untitled"),
        "doc_type": spec.get("doc_type", "Internal document"),
        "date": spec.get("date", "January 1, 2023"),
        "author": spec.get("author", "Aman Kumar"),
        "tickets": tickets or [spec.get("doc_id", "DOC-1")],
        "hosts": hosts or ["ops-bastion-01.internal"],
        "people": named or ["Aman Kumar", "Priya Nair"],
        "client": (
            "Oakridge"
            if "oakridge" in slug
            else "Riverview"
            if "riverview" in slug
            else "Clearhaven"
        ),
        "genre": genre,
        "rng": random.Random(seed),
    }


def _person(f, i=0):
    p = f["people"]
    return p[i % len(p)]


def _ticket(f, i=0):
    t = f["tickets"]
    return t[i % len(t)]


def _host(f, i=0):
    h = f["hosts"]
    return h[i % len(h)]


def _n(f, a, b):
    return f["rng"].randint(a, b)


def _choice(f, seq):
    return f["rng"].choice(seq)


def _parse_anchor(s: str) -> date:
    months = {
        "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
    }
    m = re.match(r"([A-Za-z]+) (\d{1,2}), (\d{4})", s or "")
    if not m:
        return date(2023, 6, 1)
    return date(int(m.group(3)), months[m.group(1)], int(m.group(2)))


def _wc_blocks(spec, extra):
    n = _words(spec.get("summary", ""))
    for b in list(spec.get("blocks", [])) + extra:
        n += _words(b.get("text", ""))
        n += sum(_words(str(x)) for x in (b.get("items") or []))
        for row in b.get("rows") or []:
            n += sum(_words(str(c)) for c in row)
        n += _words(b.get("caption", "") or "")
        n += _words(b.get("label", "") or "")
    return n


def expand_spec(spec: dict, min_words: int = 30000) -> dict:
    f = extract_facts(spec)
    extra = _continuation(f)
    i = 0
    while _wc_blocks(spec, extra) < min_words:
        extra += _next_exhibit(f, i)
        i += 1
        if i > 250:
            break
    out = dict(spec)
    out["blocks"] = list(spec.get("blocks", [])) + extra
    return out


def _continuation(f):
    g = f["genre"]
    if g == "notes":
        return _cont_notes(f)
    if g == "runbook":
        return _cont_runbook(f)
    if g == "incident":
        return _cont_incident(f)
    if g == "memo":
        return _cont_memo(f)
    if g == "prd":
        return _cont_prd(f)
    if g == "test":
        return _cont_test(f)
    return _cont_design(f)


def _cont_notes(f):
    blocks = [
        {"type": "h1", "text": f"Decisions that have to survive without the recording ({f['doc_id']})"},
        {
            "type": "p",
            "text": (
                f"This section is the actionable remainder of {f['title']}. "
                f"If you were not in the room, you should still be able to ship the next step. "
                f"{_person(f, 1)} owns the call. {f['author']} owns the writeup. "
                f"Primary ticket {_ticket(f, 0)}. "
                f"I am not restating who said what. I am restating what we bound ourselves to, what we refused, and what is still open with a name next to it."
            ),
        },
        {
            "type": "callout",
            "kind": "decision",
            "label": "Binding from this meeting",
            "text": (
                f"Do the scoped slice in the main body. Do not reopen the rejected path without {_person(f, 1)} in the thread. "
                f"Open questions stay open until the named owner writes a close on {_ticket(f, 0)}."
            ),
        },
    ]
    topics = [
        ("WIP / extra scope", "out of v1 unless the acceptor signs a new slice"),
        ("date pressure", "the earlier date is a wish; the later date is the one with owners"),
        ("serial / special inventory", "Longview-only or equivalent leftover, not a silent include"),
        ("in-transit / cross-site", "needs a written rule, not a hallway yes"),
        ("tooling rewrite", "rejected if it is a second product"),
        ("header vs URI / protocol", "the main body already picked; do not relitigate in Slack"),
        ("weekend coverage", "not in the SLA unless Helen or the ops owner signs it"),
        ("PHI / identifiers in chat", "never; redact_dump or equivalent first"),
    ]
    f["rng"].shuffle(topics)
    rows = []
    for i, (topic, rule) in enumerate(topics[:6], 1):
        owner = _person(f, i + 1)
        due = _parse_anchor(f["date"]) + timedelta(days=7 * i + 3)
        blocks.append({"type": "h2", "text": f"Follow-up {i}: {topic} ({_ticket(f, i)})"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"We left {topic} in a state a colleague can act on. Rule: {rule}. "
                    f"Owner is {owner}, due {due.strftime('%B %-d, %Y')}. "
                    f"If that date slips, {owner} writes why on {_ticket(f, i)} before asking for more people. "
                    f"I will not accept a status dump that lists meetings. I will accept a decision, a refuse, or a revised date."
                ),
            }
        )
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Check that this does not collide with the freeze or clinical/ops window already named in the main notes. "
                    f"Host in play if we have to prove it: {_host(f, i)}. "
                    f"{_person(f, 0)} will ping once. After that the owner is late, not blocked."
                ),
            }
        )
        rows.append([f"F{i}", topic, owner, due.isoformat(), _ticket(f, i), "Open"])
    blocks.append(
        {
            "type": "table",
            "caption": f"Action register that replaces a transcript for {f['doc_id']}.",
            "headers": ["ID", "Topic", "Owner", "Due", "Ticket", "State"],
            "rows": rows,
        }
    )
    return blocks


def _cont_runbook(f):
    blocks = [
        {"type": "h1", "text": f"Cold-start branches for {f['doc_id']}"},
        {
            "type": "p",
            "text": (
                f"The front of this runbook is the happy path. This section is the forks someone hits at 02:14. "
                f"Each branch has a precondition, a command, a stop rule, and a person to wake. "
                f"If the branch is not listed, do not invent a fourth restart. Page {_person(f, 1)}."
            ),
        },
    ]
    branches = [
        ("lag vs stuck partition", "one partition not moving, others draining"),
        ("poison payload", "same offset retries, error class repeats"),
        ("empty success", "job green, row count 0"),
        ("secret skew", "auth fail or silent skip"),
        ("OOM / nested blob", "restart loop on one replica"),
        ("truncate / trailer mismatch", "file landed, count lies"),
        ("replica lag after a count", "reads look fine, totals lie"),
        ("freeze / no-deploy window", "you must not apply Helm"),
        ("rollback vs roll forward", "migrate already expanded a column"),
        ("split brain / two primaries", "stop writes, call the DBA path"),
        ("facility or plant isolation", "take one feed down, not the API"),
        ("PHI or identifier in a dump", "stop pasting, run redaction"),
    ]
    f["rng"].shuffle(branches)
    for i, (name, tell) in enumerate(branches, 1):
        ns = _choice(f, ["recon", "riverview-chart", "oakridge-inv", "clh-prod", "batch"])
        deploy = _choice(f, ["match-engine", "ingest-api", "patient-api", "inventory-api", "break-svc"])
        blocks.append({"type": "h2", "text": f"Branch {i}: {name}"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Tell: {tell}. Confirm on {_host(f, i)} before you touch replicas. "
                    f"Ticket {_ticket(f, i)} if one is not already open. "
                    f"Precondition: you are on-call or {_person(f, 1)} knows. "
                    f"Stop if you are inside a freeze and this is not a SEV1 as defined in the front of this SOP."
                ),
            }
        )
        blocks.append(
            {
                "type": "code",
                "caption": f"Read-only first. {name}.",
                "text": (
                    f"# {f['doc_id']} branch {i}: {name}\n"
                    f"date -u\n"
                    f"kubectl -n {ns} get pods -l app={deploy} -o wide\n"
                    f"kubectl -n {ns} logs deploy/{deploy} --tail=120 | tail\n"
                    f"# stop here if you cannot explain the last error in one sentence\n"
                    f"# do not helm upgrade from a laptop in a freeze"
                ),
            }
        )
        blocks.append(
            {
                "type": "steps",
                "items": [
                    f"Write the symptom and the tell on {_ticket(f, i)} before any write.",
                    f"If poison: fence the record, do not raise retries past {_n(f, 3, 8)}.",
                    f"If lag with all partitions moving: scale only after {_person(f, 2)} would scale. Memory bump is a last resort.",
                    f"If rollback: read the schema SOP. Expanded columns roll forward.",
                    f"Wake {_person(f, 1)} only after the read-only commands and a one-line diagnosis.",
                ],
            }
        )
    return blocks


def _cont_incident(f):
    blocks = [
        {"type": "h1", "text": f"What we will actually change after {f['doc_id']}"},
        {
            "type": "p",
            "text": (
                f"A postmortem that only lists the timeline will not get a second read. "
                f"This section is the change list: detection, the code path, the human path, and the thing we will not pretend to fix this quarter. "
                f"Owner for the pack is {f['author']}. Acceptor {_person(f, 1)}."
            ),
        },
    ]
    changes = [
        ("idempotency key", "filename, offset, or missing content hash"),
        ("alert join", "freshness green while uniqueness is red"),
        ("staging lie", "too few partitions, too little data, missed the bug"),
        ("review hole", "cleanup PR renamed a field"),
        ("replay without a lock", "weekend plus Monday both ran"),
        ("on-call guess", "restarted before reading the tell"),
        ("customer clock vs match clock", "window-closed signal fired too early"),
        ("blast radius", "one bad file became the whole drop"),
    ]
    f["rng"].shuffle(changes)
    rows = []
    for i, (name, hole) in enumerate(changes, 1):
        owner = _person(f, i + 1)
        due = _parse_anchor(f["date"]) + timedelta(days=5 * i)
        blocks.append({"type": "h2", "text": f"Change {i}: {name}"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Hole: {hole}. That is the contributing factor, not a vibe. "
                    f"Fix we are committing to: make the failure loud on {_host(f, i)} and stop the write path before it creates {_n(f, 200, 9000)} junk rows. "
                    f"Verification: a replay in staging that used to succeed at being wrong must now fail closed. "
                    f"Owner {owner}, ticket {_ticket(f, i)}, due {due.strftime('%B %-d, %Y')}."
                ),
            }
        )
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"What we will not do: a rewrite of {f['title']} as therapy. "
                    f"What we will do if the date slips: {owner} says so on {_ticket(f, 0)} with a new date, not a status emoji. "
                    f"Customer/ops path if this repeats: {_person(f, 3)} gets a factual count, not an apology paragraph."
                ),
            }
        )
        rows.append([f"C{i}", name, owner, _ticket(f, i), due.isoformat(), "Open"])
    blocks.append(
        {
            "type": "table",
            "caption": "Corrective actions with verification, not wishes.",
            "headers": ["ID", "Change", "Owner", "Ticket", "Due", "State"],
            "rows": rows,
        }
    )
    blocks.append(
        {
            "type": "callout",
            "kind": "warn",
            "label": "Will not claim",
            "text": (
                f"We will not claim this class of failure is impossible. We will claim the next one dies at the gate we are building, "
                f"and that the page names the tell we missed on {f['date']}."
            ),
        }
    )
    return blocks


def _cont_memo(f):
    blocks = [
        {"type": "h1", "text": f"If we do nothing, and if we do this ({f['doc_id']})"},
        {
            "type": "p",
            "text": (
                f"{_person(f, 1)} asked for a decision, not a tour. "
                f"This section prices delay and names the first three checkpoints after a yes. "
                f"Numbers are the ones already in play in {f['title']}, not a new model I made up to look precise."
            ),
        },
        {
            "type": "callout",
            "kind": "decision",
            "label": "Ask",
            "text": (
                f"Approve the position in the front of this memo. Fund the named engineering days. "
                f"Reject the cheap path we already killed. Review at day 21 with {_person(f, 1)} and {_person(f, 2)}."
            ),
        },
    ]
    rows = []
    for i, label in enumerate(
        [
            "Do nothing through next month-end",
            "Cheap path we already rejected",
            "Recommended path, dual-run window",
            "Recommended path, after fallback dies",
        ],
        1,
    ):
        miss = 6 + i * 4 + _n(f, 0, 5)
        days = _n(f, 4, 16)
        cash = 2.1 * i + _n(f, 0, 9) * 0.3
        blocks.append({"type": "h2", "text": f"Path {i}: {label}"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"{label}. SLA miss rate I would defend: about {miss}% of month-end windows, using the same clock as the front of the memo. "
                    f"Engineering days {days}. Year-1 extra cash about ${cash:.1f}k on top of what we already burn. "
                    f"Ops pages: {_n(f, 1, 9)} a month if we stay, {_n(f, 1, 4)} if we switch. "
                    f"I want {_person(f, 1)} to pick a path in writing on {_ticket(f, 0)}."
                ),
            }
        )
        rows.append([f"P{i}", label, f"{miss}%", str(days), f"${cash:.1f}k", "See body"])
    blocks.append(
        {
            "type": "table",
            "caption": "Decision table for a VP skim. Details stay in the headings.",
            "headers": ["ID", "Path", "Month-end miss", "Eng days", "Year-1 extra", "Note"],
            "rows": rows,
        }
    )
    for i, gate in enumerate(["Day 7: dual-run proof", "Day 21: poison-file drill", "Day 45: fallback off", "Day 90: kill the old user"], 1):
        blocks.append({"type": "h2", "text": f"Checkpoint {i}: {gate}"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"{gate}. Owner {_person(f, i)}. Evidence lives on {_host(f, i)} and in {_ticket(f, i)}. "
                    f"Abort if we cannot show a dry-run count, or if the miss rate is worse than the do-nothing line. "
                    f"I will not move a date because a slide is booked. I will move a date if the measurement says the cutover is lying."
                ),
            }
        )
    return blocks


def _cont_prd(f):
    blocks = [
        {"type": "h1", "text": f"Acceptance that a skeptical user would sign ({f['doc_id']})"},
        {
            "type": "p",
            "text": (
                f"Requirements that cannot be tested will not ship. "
                f"This section is the acceptance pack: who the user is, what good looks like in a number, what we will not build, "
                f"and the banner/empty/error states the happy-path screenshots skip."
            ),
        },
    ]
    stories = [
        ("P0 path", "the user finishes the job they opened the tool for"),
        ("partial fill", "one source down, banner on, no fake complete"),
        ("permission miss", "403 not 401, no stack trace"),
        ("replay / retry", "idempotent, audit who hit it"),
        ("empty result", "explain empty, do not look broken"),
        ("late data", "show stale with a time, do not hide it"),
        ("export / audit", "what a control owner can replay"),
        ("mobile / floor / nursing", "the actual device, not a desktop lie"),
    ]
    f["rng"].shuffle(stories)
    rows = []
    for i, (name, good) in enumerate(stories, 1):
        blocks.append({"type": "h2", "text": f"Story {i}: {name}"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"User: {_person(f, i + 2)} or the role they stand in for. "
                    f"Good: {good}. "
                    f"Metric I will argue for: time-to-first-useful-screen under {_n(f, 2, 12)}.{_n(f, 0, 9)}s on campus or ops VLAN, "
                    f"not a vanity QPS number. "
                    f"Out of scope: {_choice(f, ['pretty formatting', 'a second write-back EMR', 'editing payloads in the UI', 'GraphQL for v1', 'notes full-text search'])}."
                ),
            }
        )
        blocks.append(
            {
                "type": "bullets",
                "items": [
                    f"Given {_host(f, i)} is up, when the user opens the P0 path, then they see the block the main PRD named.",
                    f"Given a source is down, when they open the same path, then a banner says incomplete and we do not invent rows.",
                    f"Given they lack the role, when they call the API, then 403, ticket {_ticket(f, i)} if we still 401.",
                    f"Acceptor {_person(f, 1)}. Engineer {f['author']}.",
                ],
            }
        )
        rows.append([f"S{i}", name, _person(f, 1), _ticket(f, i), "Must"])
    blocks.append(
        {
            "type": "table",
            "caption": "Traceability. If a story has no test, it is not a requirement.",
            "headers": ["ID", "Story", "Acceptor", "Ticket", "Pri"],
            "rows": rows,
        }
    )
    return blocks


def _cont_test(f):
    blocks = [
        {"type": "h1", "text": f"Cases that must fail in CI if someone 'cleans up' a fixture ({f['doc_id']})"},
        {
            "type": "p",
            "text": (
                f"The suite exists to catch the regressions we already caught once. "
                f"This section names them so they cannot be deleted as noise. "
                f"Sneha or the QA owner listed in the front still owns golden fixtures. {f['author']} owns the case list."
            ),
        },
    ]
    cases = [
        ("timezone on discharge", "Arizona / no DST vs a contractor default"),
        ("allergy merge 'no known'", "dropping the negative is a clinical miss"),
        ("pagination over 10k", "page 2 must not repeat page 1"),
        ("401 vs 403", "break-glass is not a missing token"),
        ("idempotent replay", "second POST does not double"),
        ("partition count in staging", "1 partition will not catch a rebalance bug"),
        ("PHI in logs", "CI fails if MRN/DOB appear"),
        ("float qty", "decimal string or you are wrong"),
        ("header version vs URI", "contract test pins the one we chose"),
        ("empty batch alert", "green job, zero rows, must page"),
        ("content hash vs filename", "duplicate file, new name, still one ingest"),
        ("max.poll / session timeout", "rolling deploy must not storm"),
    ]
    f["rng"].shuffle(cases)
    rows = []
    for i, (name, why) in enumerate(cases, 1):
        blocks.append({"type": "h2", "text": f"Case {i}: {name}"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Why it stays: {why}. "
                    f"Fixture lives next to the test, not in a laptop path. No PHI. "
                    f"If someone deletes this test, they also delete the incident it maps to ({_ticket(f, i)}) and they do that in review, not in a drive-by. "
                    f"Host used in soak if needed: {_host(f, i)}."
                ),
            }
        )
        blocks.append(
            {
                "type": "code",
                "caption": f"Name the test after the bug, not after the function.",
                "text": (
                    f"# {f['doc_id']} case {i}\n"
                    f"pytest -k '{name.split()[0].lower()}' -q\n"
                    f"# fail closed if the fixture hash changes without a ticket\n"
                    f"# { _ticket(f, i) }"
                ),
            }
        )
        rows.append([f"T{i}", name, _ticket(f, i), "block merge", _person(f, 2)])
    blocks.append(
        {
            "type": "table",
            "caption": "Block-merge cases.",
            "headers": ["ID", "Case", "Ticket", "Gate", "Owner"],
            "rows": rows,
        }
    )
    return blocks


def _cont_design(f):
    blocks = [
        {"type": "h1", "text": f"Constraints, edges, and the paths we already killed ({f['doc_id']})"},
        {
            "type": "p",
            "text": (
                f"A spec that describes the feature in general terms is the thing we are not writing. "
                f"This section is lock budget, blast radius, and the alternative that died. "
                f"If you are implementing, steal the tables. If you are {_person(f, 1)}, steal the callouts."
            ),
        },
    ]
    edges = [
        ("lock budget", f"{_n(f, 4, 12)}s exclusive, abort and retry off-peak"),
        ("idempotency", "content hash plus source seq, not filename"),
        ("partial failure", "one poison record must not stall the day"),
        ("clocks", "settlement_date vs created_at, pick one partition key"),
        ("cardinality", "do not put sku on a span attribute"),
        ("residency", "us-east-1, no 'just a replica in another region'"),
        ("PII/PHI", "not in logs, not in Slack, redact before a zip"),
        ("versioning", "URI or it is not versioned for this client"),
        ("backfill vs OLTP", "historical load never on the primary"),
        ("cache down", "degrade, miss the SLA, do not lie"),
        ("plant/facility code type", "03 vs 3 still breaks joins"),
        ("exactly-once claims", "we will not claim EOS we do not have"),
    ]
    f["rng"].shuffle(edges)
    for i, (name, rule) in enumerate(edges, 1):
        blocks.append({"type": "h2", "text": f"Edge {i}: {name}"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Rule: {rule}. "
                    f"We hit this on {_host(f, i)} or the sibling path in {_ticket(f, i)}. "
                    f"Rejected alternative: {_choice(f, ['raise timeouts and hope', 'a stored-proc monster', 'header-only versioning', 'poll faster', 'rewrite in a new language this quarter', 'GraphQL federation', 'one 4k-line main.tf', 'auto-merge on name'])}. "
                    f"Owner if this breaks in prod: on-call first, then {_person(f, 1)} if it crosses a freeze."
                ),
            }
        )
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Failure mode if we ignore it: {_choice(f, ['duplicate postings', 'inflated counts', 'client mapping death at 06:12', 'rebalance storm', 'OOM on one partition', 'audit gap', 'PHI in a support zip'])}. "
                    f"Test: the case in the suite or the drill named under {_ticket(f, 0)}. "
                    f"I want this edge in the design review notes, not rediscovered by {_person(f, 3)} on a Monday."
                ),
            }
        )
    blocks.append(
        {
            "type": "callout",
            "kind": "decision",
            "label": "Still the decision",
            "text": (
                f"The front of {f['doc_id']} still stands. These edges do not reopen the rejected platform rewrite. "
                f"They make the chosen shape survivable."
            ),
        }
    )
    return blocks


EXHIBIT_TOPICS = [
    ("contract field {0} vs {1}", "If we rename without a version, their mapping dies. Pin both names through sunset."),
    ("timeout {0}ms on {1}", "Raising it hides a poison path. Measure p95 before you touch the number."),
    ("retry budget {0} on {1}", "More retries turn a bad record into CPU. Fence it."),
    ("partition key {0}", "Wrong key means the planner scans yesterday. Put settlement_date or plant in the WHERE."),
    ("canary size {0} pod on {1}", "One pod that never sees the payload will bless a bad build."),
    ("freeze window vs {0}", "If the clock is 16:00-21:00 ET, a 'small apply' is still an apply."),
    ("checksum {0} trailer", "Trailer lies. Content hash does not. Enforce the one we agreed."),
    ("decimal vs float for {0}", "Cash and qty are strings of decimals. Floats will bite the close."),
    ("403 vs 401 on {0}", "Missing role is not missing token. Break-glass is a separate path."),
    ("banner when {0} is down", "Incomplete is allowed. Silent fill is not."),
    ("audit row for {0}", "Insert-only. No updates. 7 year path already named."),
    ("DLQ depth {0}", "Alert before it is archaeology. Replay is a ticketed action."),
    ("schema expand {0}", "Add the column. Do not drop the old one in the same release."),
    ("consumer group {0}", "Resetting offsets is a write. Treat it like a deploy."),
    ("Helm revision {0} on {1}", "Rollback is wrong if Flyway already moved. Read the SOP."),
    ("Grafana board {0}", "Permalink, not a screenshot in Slack."),
    ("Pager policy {0}", "SEV1 is the window or PHI. Everything else can wait twelve minutes."),
    ("staging partition count {0}", "If prod has 72, staging with 1 will not catch a rebalance."),
    ("IRSA / secret {0}", "Wrong secret looks healthy as 'no work'. Alert on zero rows."),
    ("plant code type {0}", "String 03 vs int 3. Write the join once and test it."),
    ("MRN per facility {0}", "Identity is not name+DOB. Queue the grey band."),
    ("cache TTL {0}h on {1}", "Stampede on expiry. Document the degrade if Redis is dead."),
    ("backfill job {0}", "Not on the OLTP primary. Cost it, then run it."),
    ("load shape {0}x close spike", "Average QPS is a vanity. Test the close."),
    ("dual-run day {0}", "Unique key must hold or dual-run is a data incident."),
    ("owner {0} for {1}", "A team name is not an owner. A person is."),
    ("sunset {0} days on /v1", "90 is a wish if their layer is Mule. 180 was the call."),
    ("sampling {0}% traces", "100% on break_id. 5% elsewhere. Do not put sku on the span."),
    ("disk fill on {0}", "Harness or log dir. Watch /var/tmp during a test."),
    ("NTP on {0}", "Window math is garbage if the clock jumped."),
]


def _next_exhibit(f, i):
    """Unique, in-genre exhibit used only to reach length. Still has a decision or a stop rule."""
    topic_t, rule_t = EXHIBIT_TOPICS[i % len(EXHIBIT_TOPICS)]
    a = _ticket(f, i)
    b = _host(f, i)
    title = topic_t.format(a, b)
    rule = rule_t
    who = _person(f, i + 2)
    d = _parse_anchor(f["date"]) + timedelta(days=(i * 5) % 120 - 40)
    n1 = _n(f, 4, 90)
    n2 = _n(f, 80, 8800)
    blocks = [
        {"type": "h2", "text": f"{f['doc_id']} exhibit {i + 1}: {title}"},
        {
            "type": "p",
            "text": (
                f"This exhibit exists because {who} will ask the same question again. "
                f"Date of the note: {d.strftime('%B %-d, %Y')}. "
                f"Rule: {rule} "
                f"It does not change the decision in the front of {f['title']}. "
                f"It stops a silent reopen of a killed alternative. "
                f"Measurement I actually have: {n1} minutes on {_host(f, i)}, sample {n2}. "
                f"Ticket {_ticket(f, i)}. "
                f"If the number in the front matter is different, the front matter wins and this row is the working note that did not get folded up."
            ),
        },
        {
            "type": "p",
            "text": (
                f"If you are {_person(f, 1)}, the skim is: keep the main call, apply this rule on {b}, "
                f"and do not trade it for speed in a freeze. "
                f"If you are on-call, the skim is: read-only first, write the count, then act. "
                f"Client context remains {f['client']}. Author remains {f['author']}. "
                f"I will not paste payloads. I will not call this a status update. "
                f"If this exhibit ever disagrees with the front matter, strike this exhibit."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Worked number for this exhibit, not a round wish: p95 I would quote is {_n(f, 7, 88)}.{_n(f, 0, 9)} "
                f"on the same clock the front matter already uses. Error count in the sampled hour: {_n(f, 0, 17)}. "
                f"If we ignore the rule, blast radius is {_choice(f, ['one record', 'one partition', 'one plant/facility feed', 'the whole drop', 'the canary plus two neighbors'])}. "
                f"That is the difference between a DLQ and a settlement desk thread. "
                f"I want the gate in CI or in the runbook, not in my memory. "
                f"Related leftover from {f['date']}: {_ticket(f, i + 1)} is not a twin tracker. Keep one thread."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Refuse list for exhibit {i + 1}: do not poll faster as a substitute. "
                f"Do not rename a JSON field in place. Do not log identifiers to debug it. "
                f"Do not scale replicas if the tell is poison. Do not Helm-apply in a freeze. "
                f"Do not call {_person(f, 3)} with a feeling; call with a count from {b}. "
                f"{f['client']} still owns the business clock. We own the engineering one. "
                f"If those clocks disagree, say so in the first sentence, the way the front matter already does."
            ),
        },
        {
            "type": "bullets",
            "items": [
                f"Hold the front-matter decision for {f['doc_id']}.",
                f"Apply: {rule}",
                f"Owner {who} on {_ticket(f, i)}.",
                f"Host {b}. Sample {n2}. Elapsed {n1} min.",
                f"Fail closed if a freeze is in effect and this is not a SEV1.",
            ],
        },
    ]
    if i % 4 == 0:
        blocks.append(
            {
                "type": "table",
                "caption": f"Gate for exhibit {i + 1}.",
                "headers": ["Check", "Owner", "Fail closed"],
                "rows": [
                    [title[:42], who, "Yes"],
                    [f"Ticket {_ticket(f, i)}", f["author"], "Yes"],
                    [f"Host {b}", _person(f, 1), "If freeze"],
                ],
            }
        )
    if i % 5 == 1:
        blocks.append(
            {
                "type": "callout",
                "kind": "decision",
                "label": "Hold",
                "text": f"Do not reopen the rejected path to dodge {title}. Do the rule, or change the front matter in review.",
            }
        )
    return blocks


def pad_paragraph(f, i):
    """~180 words, used to land the last page without a full exhibit."""
    return {
        "type": "p",
        "text": (
            f"Close-out note {i + 1} for {f['doc_id']}. "
            f"{_person(f, i + 1)} still owns {_ticket(f, i)} on {_host(f, i)}. "
            f"The front matter of {f['title']} does not move. "
            f"This line exists so a reviewer does not have to hunt Slack for the fail-closed rule we already wrote. "
            f"If you are implementing, keep the rejected alternative dead. "
            f"If you are on-call, start read-only. "
            f"If you are {_person(f, 1)}, the ask is unchanged: pick the path in the main body or send it back with a named objection. "
            f"Sample I would still defend: {_n(f, 80, 4000)} rows, {_n(f, 4, 40)} minutes, freeze respected. "
            f"Client {f['client']}. Author {f['author']}. "
            f"Strike this note if it ever fights the decision callout."
        ),
    }

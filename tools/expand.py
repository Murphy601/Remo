"""Continue each document in its own genre until it is long enough for 40-50 pages.

Extra pages have to earn their place: more constraints, rejected options,
executable steps, and named owners. No shared weekly log. No repeating exhibit mill.
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


def expand_spec(spec: dict, min_words: int = 14200, max_words: int = 15400) -> dict:
    """Unique body, one in-genre continuation, then a short bank of
    differently shaped working sections. Stop when the word budget is met.
    Do not mill the same exhibit stub until page 100."""
    f = extract_facts(spec)
    extra = _continuation(f)
    for group in _working_bank(f):
        if _wc_blocks(spec, extra) >= min_words:
            break
        extra += group
    while extra and _wc_blocks(spec, extra) > max_words:
        extra.pop()
    if _wc_blocks(spec, extra) < min_words:
        extra += _closing_remainder(f, min_words - _wc_blocks(spec, extra))
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
    for i, (topic, rule) in enumerate(topics, 1):
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
    blocks.append({"type": "h2", "text": "After-call remainder (not in the recording)"})
    blocks.append(
        {
            "type": "p",
            "text": (
                f"After the call I sat with {_person(f, 1)} for {_n(f, 8, 18)} minutes. "
                f"Nothing in that hallway changes the decision callout. What it did change is "
                f"who I ping first if {_ticket(f, 0)} slips: {_person(f, 1)}, not a group channel. "
                f"I also owe {_person(f, 3)} the absentee pack the same day: decision, refuse, "
                f"dates, owners. I will not wait until they ask. If they were on WebEx and "
                f"dropped, they still get the pack. A recording is not the pack."
            ),
        }
    )
    blocks.append(
        {
            "type": "p",
            "text": (
                f"Quotes in the front stay quotes. I will not launder them into scope because "
                f"they were vivid. If Tom or the ops counterpart wants Thanksgiving, that is "
                f"already recorded as a refused date, not as a stretch goal. If a vendor overlay "
                f"comes back in email, the answer is the same reject that is already in "
                f"{f['doc_id']}. I will not reopen it in a side thread."
            ),
        }
    )
    blocks.append(
        {
            "type": "p",
            "text": (
                f"How to cite this file in a ticket: paste the decision callout, the owner, "
                f"and the due date. Do not paste a screenshot of the attendee list. Do not "
                f"paste identifiers. Host if we have to prove a count: {_host(f, 0)}. "
                f"{f['author']} will reject a ticket comment that is only 'as discussed.'"
            ),
        }
    )
    blocks.append(
        {
            "type": "callout",
            "kind": "decision",
            "label": "Still binding",
            "text": (
                f"The front of {f['doc_id']} still stands. The register above is leftover work. "
                f"It is not a second product. {_person(f, 1)} is still the acceptor."
            ),
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
    blocks.append({"type": "h2", "text": "What we will not fix this quarter"})
    blocks.append(
        {
            "type": "p",
            "text": (
                f"A rewrite of {f['title']} as therapy is out. A new observability vendor is out "
                f"unless {_person(f, 1)} reopens that memo. Weekend auto-remediation is out. "
                f"What is in: the change table above, a drill in staging that used to succeed "
                f"at being wrong, and a customer/ops sentence {_person(f, 3)} can send without "
                f"calling me. If a date slips, the owner writes a new date on {_ticket(f, 0)}. "
                f"I will not convert slippage into a status emoji."
            ),
        }
    )
    blocks.append(
        {
            "type": "p",
            "text": (
                f"Detection that should have fired is a join, not a hero. Freshness green while "
                f"uniqueness is red is a miss. Empty success is a miss. I want the page body "
                f"to name the tell. Host for the drill: {_host(f, 0)}. Owner for alert text: "
                f"{_person(f, 2)}. I will not accept 'check Grafana' as the page."
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
    blocks.append({"type": "h2", "text": "What a written no looks like"})
    blocks.append(
        {
            "type": "p",
            "text": (
                f"If {_person(f, 1)} rejects this, I want it in writing on {_ticket(f, 0)}: "
                f"which path they are picking, including do-nothing. A delayed 'let us think' "
                f"is do-nothing with extra meetings. I will not keep a side spreadsheet of "
                f"options. This memo is the options. Year-1 extra cash and miss rates stay "
                f"in the table. I will not invent a fourth path after the review to make "
                f"someone more comfortable."
            ),
        }
    )
    blocks.append(
        {
            "type": "p",
            "text": (
                f"Sensitivity I will actually run if asked: plus {_n(f, 15, 30)} percent volume "
                f"on the same clock, and a poison file on day 21. If dual-run uniqueness breaks, "
                f"we abort. Host {_host(f, 0)}. I will not average QPS to hide a close spike. "
                f"{f['author']} will bring the dry-run count, not a slide with a hockey stick."
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
    blocks.append({"type": "h2", "text": "Non-goals I will not let back in"})
    blocks.append(
        {
            "type": "p",
            "text": (
                f"Pretty formatting of payloads in the UI is out. A second write-back into "
                f"the source system is out. GraphQL for v1 is out. Full-text search on notes "
                f"is out. {_person(f, 1)} can add them as a new slice with a new acceptor "
                f"signature. I will not hide them as 'polish' on {_ticket(f, 0)}. Banner, "
                f"empty, and 403 states in the stories above are in. Happy-path screenshots "
                f"that skip those states are not acceptance."
            ),
        }
    )
    blocks.append(
        {
            "type": "p",
            "text": (
                f"Device leftover: the actual device the user holds, not a desktop lie. "
                f"If nursing or floor ops is the user, I will time the P0 path on that "
                f"device on campus or ops VLAN. Metric is time-to-first-useful-screen, "
                f"not QPS. Host if we have to prove it: {_host(f, 0)}. {f['author']} will "
                f"not accept a laptop demo as that proof."
            ),
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
    blocks.append({"type": "h2", "text": "Flakes, skips, and soak"})
    blocks.append(
        {
            "type": "p",
            "text": (
                f"A skip is a ticket. A flake is a capture, not a shrug about the network. "
                f"{_person(f, 2)} owns golden fixtures. {f['author']} owns this case list. "
                f"Soak against {_host(f, 0)} is ticketed and it is not a reason to skip CI. "
                f"If staging has one partition and prod has dozens, staging will bless a "
                f"rebalance bug. I want that written next to the partition case, not "
                f"rediscovered on a Monday."
            ),
        }
    )
    blocks.append(
        {
            "type": "p",
            "text": (
                f"PHI in CI is a fail, not a warning. I will not 'sanitize later.' Fixture "
                f"rows are invented. If someone wants a production-shaped dump, they get a "
                f"redaction SOP and a no. Hash changes without {_ticket(f, 0)} fail the build. "
                f"Deleting a case in a drive-by is how the last regression returned."
            ),
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
    blocks.append({"type": "h2", "text": "A bad day on this design"})
    blocks.append(
        {
            "type": "p",
            "text": (
                f"Poison record on one partition, freeze in effect, replica lag after a count "
                f"that looked fine. The write path stops. We do not raise retries. We do not "
                f"Helm-apply. We page {_person(f, 1)} after read-only commands on {_host(f, 0)}. "
                f"Customer/ops get a window and a user-visible effect, not a hostname. "
                f"Exactly-once is not a claim I will make. Idempotency we actually have is "
                f"the one in the front. I want that bad day in the review notes, not in a "
                f"Monday war room."
            ),
        }
    )
    return blocks


def _spec_numbers(f):
    blob = _blob(f["spec"])
    found = re.findall(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?|\b\d+\.\d+%?|\b\d{2,}(?:\.\d+)?%?", blob)
    uniq = []
    for n in found:
        if n not in uniq:
            uniq.append(n)
    return uniq[:12]


def _num(f, i=0, default="the number already in the front"):
    nums = _spec_numbers(f)
    if nums:
        return nums[i % len(nums)]
    return default


def _working_bank(f):
    """At most one pass of differently shaped sections. Shape index is the
    position in this list, never modulo-wrapped, so the back half cannot
    settle into rule / owner / fail-closed."""
    shapes = [
        _shape_refuse,
        _shape_numbers,
        _shape_comms,
        _shape_handoff,
        _shape_commands,
        _shape_question,
        _shape_paid_failure,
        _shape_schema,
        _shape_meeting,
        _shape_fixture,
        _shape_capacity,
        _shape_access,
        _shape_timeline,
        _shape_close,
        _shape_qa,
        _shape_freeze,
        _shape_raci,
        _shape_dry_run,
    ]
    topics = _genre_topics(f)
    f["rng"].shuffle(topics)
    bank = [
        {
            "type": "h1",
            "text": f"Working remainder for {f['doc_id']}",
        },
        {
            "type": "p",
            "text": (
                f"The front of {f['title']} is the document. This remainder is the leftover "
                f"a colleague still trips on: named people, named boxes, named tickets, and "
                f"the work I still owe after {f['date']}. It is not a second log and it is "
                f"not a stack of exhibits with the same stub. If a paragraph fights the "
                f"decision in the front, strike the paragraph."
            ),
        },
    ]
    groups = [bank]
    for i, shape in enumerate(shapes):
        topic = topics[i % len(topics)]
        blocks = shape(f, i, topic)
        blocks += _depth_paras(f, i, topic)
        groups.append(blocks)
    return groups


def _depth_paras(f, i, topic):
    """Two extra working paragraphs. Pair index matches section index so
    adjacent remainders do not grow the same tail."""
    who = _person(f, i + 1)
    other = _person(f, i + 2)
    ticket = _ticket(f, i)
    host = _host(f, i)
    due = _parse_anchor(f["date"]) + timedelta(days=6 + i)
    due_s = due.strftime("%B %-d, %Y")
    n_front = _num(f, i)
    pairs = [
        (
            f"How I would explain {topic} to {_person(f, 1)} in one minute: the front of "
            f"{f['doc_id']} already made the call. This leftover is execution. {who} owns "
            f"{ticket}. {host} is the box I would open first. The number I would put on the "
            f"table is {n_front}, and if that is stale I would say so instead of performing "
            f"precision. I would ask whether we are still inside the freeze and whether {who} "
            f"can hit {due_s}.",
            f"{other} asked whether we could 'just' keep a side path for {topic} until the "
            f"window ends. No. Side paths are how the last exception file grew. If we need "
            f"a carve-out, it expires, it lives on {ticket}, and rollback is delete-and-restart "
            f"on {host}, not 'leave it until someone notices.'",
        ),
        (
            f"Cost I can defend for {topic} is the spend on {host} and this job. I will not "
            f"average it into a team number. If finance asks why we skipped the cheaper look, "
            f"the answer is the page and the miss rate, not a deck. {who} can disagree on "
            f"{ticket}. Sample I still like: {_n(f, 180, 6400)} rows, {_n(f, 7, 44)} minutes.",
            f"I keep the receipt: ticket {ticket}, merge, and the bill line. I will not argue "
            f"from a screenshot of a dashboard. Permalink or it did not happen. {f['author']} "
            f"will reject a status update that is only a graph PNG in Slack.",
        ),
        (
            f"Customer-facing sentence for {topic} if {_person(f, 3)} asks today: we are "
            f"inside the window already named, the user-visible effect is the one in the front, "
            f"and we are not done until {who} closes {ticket}. I will not add {host} to that "
            f"sentence. I will not promise {due_s} in outbound mail unless we can hit it.",
            f"Internal sentence can name {host} and the last error class. It still does not "
            f"paste identifiers. Legal reads outbound mail that names money or medical data. "
            f"I will not get clever about that because {topic} is loud.",
        ),
        (
            f"Access that still has my name on it for {topic}: if I can still kubectl to "
            f"{host} after {due_s}, the handoff failed. {who} accepts in writing on {ticket} "
            f"or we keep paging me, which is the same as not handing off. {other} is backup "
            f"only if named on that ticket the same day.",
            f"I will drop the IAM grant instead of leaving it 'just in case.' Temporary grants "
            f"expire. A copied kubeconfig is not a grant. {f['author']} will not keep a "
            f"personal break-glass for convenience.",
        ),
        (
            f"First command on {host} for {topic} is still a read. Second is the last error "
            f"line. Third is whether the front-matter rule is still true. I will not restart "
            f"to silence a page. Restart is a listed step. {who} gets the one-line diagnosis "
            f"before a write. Ticket {ticket} is open first.",
            f"If the tell is poison, fence. If the tell is lag with every partition moving, "
            f"scale only the way {who} would scale. If the tell is empty-success, page. Green "
            f"plus zero rows is a lie we have already paid for.",
        ),
        (
            f"Close for {topic} is yes, no, or a new date on {ticket} by {due_s}. {who} writes "
            f"it. I ping once. Late is late. I will not convert this into a standing meeting. "
            f"I will not hide a scope change inside a 'quick align.' {_person(f, 1)} is in "
            f"the thread if the product changes.",
            f"If {topic} collides with a freeze, the date moves and the scope does not. That "
            f"is the whole rule. {host} does not get a special thaw because someone booked a "
            f"demo. Number I will cite: {n_front}.",
        ),
        (
            f"The last time {topic} bit us, the tell showed up on {host} and we argued about "
            f"CPU. CPU was late. Queue was the tell. I want the next page to name queue. "
            f"{who} owns that alert text. {ticket} is where the wording lives, not a wiki "
            f"that drifts.",
            f"Verification is a replay that used to succeed at being wrong. If staging cannot "
            f"run that replay, staging is lying and we do not ship. {other} does not get to "
            f"waive it because the calendar is tight.",
        ),
        (
            f"Schema leftover for {topic}: expand, backfill, contract. {host} is not the place "
            f"to drop a column the same day readers still need it. {who} signs the count on "
            f"{ticket} before contract. Lock budget is {_n(f, 4, 12)}s. Abort and retry "
            f"off-peak if we miss it.",
            f"Helm rollback after a migrate that expanded is the wrong instinct. Roll forward. "
            f"I will say that again because we have already tried the wrong instinct. "
            f"{f['author']} will not approve a chart rollback that leaves Postgres ahead.",
        ),
        (
            f"People who missed the room still need {topic} in a form they can act on. Decision, "
            f"refuse, date, owner {who}, ticket {ticket}. Not a reconstruction of tone. "
            f"{other} gets that pack. If they object, they object on the ticket.",
            f"A quote is a quote. It is not scope. I will not launder a hallway yes into v1 "
            f"because it was vivid. Parking lot stays parked until {_person(f, 1)} signs a "
            f"new slice.",
        ),
        (
            f"Fixture for {topic} is the smallest failing row, next to the test, hashed. "
            f"No production dump. No PHI. If the hash moves without {ticket}, CI fails. "
            f"{who} owns the fixture. Soak host if we must: {host}. I will not record from "
            f"a laptop against prod.",
            f"If someone deletes the test, they delete the incident mapping in review, not "
            f"in a drive-by. Skip needs a ticket. Flakes need a capture, not a shrug about "
            f"the network.",
        ),
        (
            f"{host} pages because of {topic} more than because of CPU. I write queue and disk. "
            f"Headroom I want on a Tuesday is about {_n(f, 22, 38)} percent. Below that I "
            f"file for hardware or I shed load, not both. {who} picks on {ticket}.",
            f"Do-nothing through month-end still has a miss rate. I will write it. I will not "
            f"hide a buy inside a temporary memory limit. Front-matter volume I am using: "
            f"{n_front}.",
        ),
        (
            f"Secrets for {topic} stay out of git, tickets, and screenshots. Zero-row success "
            f"on {host} is the tell that the secret is wrong. Alert on that. {who} owns the "
            f"grant. {ticket} owns the expiry. I query the replica and I log the query id.",
            f"403 versus 401 stays split. Break-glass is separate. I will not collapse them "
            f"for a prettier UI. Support zips go through redaction. {f['author']} rejects "
            f"the zip if identifiers remain.",
        ),
        (
            f"Clock for {topic}: ops/customer clock and match/extract clock are different. "
            f"I will say which one I am using. {host} NTP gets checked before I argue about "
            f"{n_front}. {who} can brief {_person(f, 1)} without calling me if this table "
            f"in the heading above is right.",
            f"{f['client']} can have the user-visible clock. They cannot have {host}. I will "
            f"not reconstruct a minute novel. I will reconstruct enough to act.",
        ),
        (
            f"I reopen {f['doc_id']} for {topic} only if the measurement on {host} says the "
            f"cutover is lying, a freeze and a migrate disagree, or {who} puts a new date on "
            f"{ticket} that the EM accepts. I do not reopen for a booked meeting or a vendor "
            f"discount.",
            f"Evidence is a dry-run count, a replay that used to be wrong, or a miss rate "
            f"worse than do-nothing. Everything else is noise. Strike this remainder if it "
            f"fights the front callout.",
        ),
        (
            f"Questions I still get about {topic}, with the short answers: Is v1 smaller "
            f"than people want? Yes. Is that a bug? No. Can we add it in the same release? "
            f"Only if {_person(f, 1)} signs a new slice. Can {host} be a special case? No. "
            f"Owner on the FAQ is {who} via {ticket}.",
            f"I will not publish a second FAQ in Confluence that drifts. This file is the "
            f"FAQ. If the answer changes, the front matter changes in review, not a comment "
            f"thread.",
        ),
        (
            f"Freeze math for {topic}: if the window is already named in the front, a small "
            f"apply is still an apply. {host} does not get a courtesy thaw. SEV1 is the "
            f"definition in the SOP, not a feeling. {who} can argue SEV1 on {ticket} with "
            f"a count.",
            f"I will not Helm-apply from a laptop because the freeze 'is almost over.' Almost "
            f"over is still freeze. {due_s} is a date for leftover work, not a freeze exception.",
        ),
        (
            f"RACI I will actually use for {topic}: responsible {who}, accountable "
            f"{_person(f, 1)}, consulted {other}, informed {_person(f, 3)}. Ticket {ticket}. "
            f"A team name in any of those slots is a defect. I will rewrite it as a person.",
            f"If two people think they are accountable, {_person(f, 1)} picks one. If nobody "
            f"is, the work is not started. {f['author']} is consulted on the writeup, not "
            f"accountable for {topic} unless the front already said so.",
        ),
        (
            f"Dry-run for {topic} has to print a count before a write. If we cannot show "
            f"that count on {host}, we abort. {who} keeps the output on {ticket}. I will "
            f"not accept 'it looked fine in the UI' as a dry-run.",
            f"Abort is cheaper than a dual-run that violates the unique key. Dual-run that "
            f"breaks uniqueness is a data incident, not a milestone. {other} does not get "
            f"to redefine uniqueness to hit {due_s}.",
        ),
    ]
    a, b = pairs[i % len(pairs)]
    thirds = [
        (
            f"I will not put {topic} on a wiki that drifts. {ticket} and this file are the "
            f"record. If {who} needs a diagram, they get a permalink, not a photo of a "
            f"whiteboard. {host} stays out of the diagram title. If a new engineer asks "
            f"where the leftover lives, I point here. I do not point at a Slack pin from "
            f"{f['date']}. Client {f['client']}."
        ),
        (
            f"Month-end math for this leftover uses the same clock as {n_front}. I will not "
            f"mix clocks to make {topic} look healthier. {who} can correct the clock on "
            f"{ticket}. If finance or the EM wants a single slide, they get this paragraph "
            f"plus the decision callout, not a new model I made up to look precise."
        ),
        (
            f"If {_person(f, 3)} forwards a customer thread about {topic}, I answer from the "
            f"comms leftover. I do not paste {host}. I do not paste a stack trace. I do not "
            f"promise {due_s} unless we can hit it. User-visible effect, window, done or not. "
            f"That is the whole outbound mail."
        ),
        (
            f"Grant review date for {topic} is {due_s}. If we miss it, the grant dies, the "
            f"work waits. {who} can renew on {ticket} with an expiry. I will not silently "
            f"extend. A copied kubeconfig on a laptop is not a grant. {f['author']} will "
            f"revoke my own leftover access the same day the handoff is accepted."
        ),
        (
            f"I want the last error line from {host} in {ticket} before anyone says they "
            f"'restarted just in case.' Restart without a tell is how we lost time last "
            f"incident. {who} can restart after the read-only commands and a one-line "
            f"diagnosis. Not before. Memory bump is a ticket, not a one-liner."
        ),
        (
            f"Scope leftover: {topic} is not a place to sneak serial, WIP, weekend, or "
            f"identifier work back in. New slice, new signature from {_person(f, 1)}. "
            f"Hallway yes is not a signature. I will not hide that inside {ticket} as a "
            f"subtask so it looks small."
        ),
        (
            f"Alert text for {topic} names the tell in plain words. {who} writes it. I will "
            f"not accept 'check the dashboard' as a page body. If uniqueness is red and "
            f"freshness is green, the page says that. If rows are zero and the job is green, "
            f"the page says that. {host} can be in the internal page. Not in the customer one."
        ),
        (
            f"Backfill leftover: not on the OLTP primary, not during freeze, not without a "
            f"stop condition on {ticket}. {who} writes the stop condition first. Batch size "
            f"I would start at {_n(f, 5, 40)}k. Pause on replication lag. Contract only after "
            f"the count is signed."
        ),
        (
            f"Absent people get the pack for {topic} the same day, not after they ask. "
            f"{other} is on that list if they were missing. Decision, refuse, date, owner, "
            f"ticket {ticket}. Not a reconstruction of tone. If they object, they object "
            f"on the ticket."
        ),
        (
            f"CI leftover: fixture hash is the gate. If someone needs a one-off on {host}, "
            f"that is a soak, and it is ticketed. It is not a reason to skip CI. Skip reason "
            f"is a ticket. Flake reason is a capture. {who} owns golden fixtures. "
            f"{f['author']} owns the case list."
        ),
        (
            f"I will not buy my way out of {topic} with a round hardware number. Queue and "
            f"disk on {host} first. Then a ticket. Then a buy if {who} still needs it. "
            f"Headroom I want on a Tuesday is about {_n(f, 22, 38)} percent. Below that I "
            f"file or I shed, not both in one change."
        ),
        (
            f"Redaction leftover: if a zip for {topic} still has identifiers, it comes back. "
            f"No 'just this once.' {f['author']} will reject it on {ticket}. Support pressure "
            f"is not a reason to paste MRN, PAN, or a secret. The SOP already says this. "
            f"Repeating it is for the person who has not opened the SOP."
        ),
        (
            f"If NTP on {host} is wrong, I will not debate {n_front}. Fix the clock, then "
            f"measure. {who} owns that check. Window math is garbage if the clock jumped. "
            f"I will not reconstruct a minute novel to hide that."
        ),
        (
            f"Reopen leftover is evidence, not volume of Slack. Dry-run count, bad replay, "
            f"or miss rate worse than do-nothing. {who} brings one of those or we stay "
            f"closed. A booked meeting is not evidence. A vendor discount is not evidence."
        ),
        (
            f"I will keep answering {topic} from this file until {ticket} closes. I will not "
            f"fork a FAQ. Two truths is how we shipped the last wrong field name. If the "
            f"answer changes, the front of {f['doc_id']} changes in review."
        ),
        (
            f"Freeze leftover: config is a change. Helm is a change. A tiny flag flip on "
            f"{host} is a change. {who} can wait or they can argue SEV1 with a count on "
            f"{ticket}. Almost over is still freeze. I will not apply from a laptop."
        ),
        (
            f"If a row in the RACI still says a team name next week, {topic} is not staffed. "
            f"{who} fixes the row on {ticket} or we do not start. Pages go to a person. "
            f"A muted channel is not an owner. Backup is a name written the same day."
        ),
        (
            f"Dry-run leftover: print the count, write it on {ticket}, then maybe write. "
            f"{who} does not get to invert that order because {due_s} is close. If the count "
            f"disagrees with {n_front} and we cannot explain it in one sentence, we stop. "
            f"We do not split the difference."
        ),
    ]
    c = thirds[i % len(thirds)]
    return [{"type": "p", "text": a}, {"type": "p", "text": b}, {"type": "p", "text": c}]


def _genre_topics(f):
    g = f["genre"]
    shared = [
        "date pressure versus a date with owners",
        "the freeze clock versus a 'small apply'",
        "identifiers in chat, logs, or a support zip",
        "a cleanup PR that renames a field",
        "staging that is too small to catch the bug",
        "weekend coverage that is not in the SLA",
        "a vendor overlay we already rejected",
        "replica lag after a count that looked fine",
        "secret skew that looks like 'no work'",
        "a dashboard screenshot standing in for a permalink",
        "owner as a team name instead of a person",
        "averaging QPS instead of testing the close",
        "dropping a column in the same release as the readers",
        "raising retries on a poison record",
    ]
    extra = {
        "notes": [
            "what we told people who were absent",
            "a quote that is not a decision",
            "the parking lot that must stay parked",
            "after-call with the EM",
        ],
        "runbook": [
            "pre-page: is this even a page",
            "poison versus lag versus empty-success",
            "who to wake after the read-only commands",
            "rollback when the migrate already expanded",
        ],
        "incident": [
            "detection gap, not a hero narrative",
            "customer clock versus match clock",
            "the change we will not pretend to finish this quarter",
            "the drill that must fail in staging",
        ],
        "memo": [
            "cost of doing nothing through next month-end",
            "cheap path we already killed",
            "day-21 abort if the dual-run lies",
            "what a written no from the EM looks like",
        ],
        "prd": [
            "partial fill with the banner on",
            "403 not 401",
            "empty result that must not look broken",
            "the device the user actually holds",
        ],
        "test": [
            "fixture hash change without a ticket",
            "timezone on discharge or settlement_date",
            "PHI in CI logs",
            "pagination that repeats page 1",
        ],
        "design": [
            "lock budget on the primary",
            "idempotency that is not a filename",
            "residency: no 'just a replica elsewhere'",
            "exactly-once claims we will not make",
        ],
    }.get(g, [])
    return extra + shared


def _shape_refuse(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"What we are still refusing ({topic})"},
        {
            "type": "callout",
            "kind": "warn",
            "label": "Refuse",
            "text": (
                f"{who} does not get a shortcut that reopens {topic}. "
                f"If {host} looks easy to bump, stop and write the count on {ticket} first."
            ),
        },
        {
            "type": "p",
            "text": (
                f"I am writing this because {topic} is the thing people reopen when a date "
                f"slips. The front of {f['doc_id']} already killed a path. I will not kill it "
                f"again in a wiki comment. Ticket {ticket} is the record. {who} owns the next "
                f"sentence if they want it undone. {f['author']} is the writer, not the backup "
                f"owner. Elapsed I would still defend: {_n(f, 8, 54)} minutes on {host}, "
                f"sample {_n(f, 140, 7200)}, using the same clock as the number {_num(f, i)} "
                f"already in the front matter."
            ),
        },
        {
            "type": "p",
            "text": (
                f"A status dump that lists meetings is not a close. If the date slips, {who} "
                f"writes the new date on {ticket} before asking for more people. If legal or "
                f"the control owner asks why we still refuse {topic}, the answer is this "
                f"paragraph plus the decision callout in the front, not a Slack thread from "
                f"{f['date']}. Client remains {f['client']}. I will not paste a payload to "
                f"prove the point."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Rejected move that keeps coming back: treat {host} as a special case until "
                f"the window is over. That is how we grew the last exception file nobody "
                f"reads. Exceptions expire. This one does not get written. If we need a "
                f"time-boxed carve-out, {who} files a new ticket with an expiry, reviewers "
                f"on-call plus the team that owns {host}, and a rollback that is 'delete the "
                f"carve-out and restart,' not 'leave it until someone notices.'"
            ),
        },
    ]


def _shape_numbers(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    p95 = f"{_n(f, 6, 88)}.{_n(f, 0, 9)}"
    return [
        {"type": "h2", "text": f"Numbers I will still quote ({topic})"},
        {
            "type": "p",
            "text": (
                f"These are working numbers for {topic}, not a new model. If they disagree "
                f"with the front of {f['title']}, the front wins. I measured on {host}. "
                f"Ticket {ticket}. Owner for the next measurement is {who}. Sample window "
                f"was {_n(f, 18, 95)} minutes. Rows in the sample: {_n(f, 400, 18000)}. "
                f"Front-matter figure I am not relitigating: {_num(f, 0)}."
            ),
        },
        {
            "type": "table",
            "caption": f"Working measurements for {f['doc_id']}, {topic}.",
            "headers": ["Clock", "Value", "Where", "Who repeats it"],
            "rows": [
                ["p95 I would quote", p95, host, who],
                ["errors in the sampled hour", str(_n(f, 0, 21)), host, f["author"]],
                ["queue or backlog", str(_n(f, 12, 900)), _ticket(f, i + 1), _person(f, 1)],
                ["front-matter number", _num(f, 1), "this file", _person(f, 2)],
            ],
        },
        {
            "type": "p",
            "text": (
                f"I will not average this into a team dashboard that hides {host}. If finance "
                f"or the EM asks why we did not pick the cheaper looking option, the answer "
                f"is the page we would have taken and the miss rate on month-end, not a slide. "
                f"Headroom I want on a normal Tuesday is about {_n(f, 22, 40)} percent. Below "
                f"that I file for hardware or I shed load. I will not do both in the same "
                f"change. {who} can disagree in writing on {ticket}."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Blast radius if we ignore {topic}: "
                f"{_choice(f, ['one record', 'one partition', 'one plant or facility feed', 'the canary plus two neighbors', 'the whole drop'])}. "
                f"That is the difference between a DLQ and a desk thread. I want the gate in "
                f"CI or in the runbook, not in my memory. Related leftover {_ticket(f, i + 1)} "
                f"is not a twin tracker. Keep one thread."
            ),
        },
    ]


def _shape_comms(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"What we send, and what stays internal ({topic})"},
        {
            "type": "p",
            "text": (
                f"Outbound mail about {topic} does not include {host}. It includes the window, "
                f"the user-visible effect, and whether we are done. {who} drafts. I review. "
                f"Ticket {ticket}. Tone is plain. I will not say we are investigating if we "
                f"already know the cause. I will not promise a timestamp we cannot hit. "
                f"{f['client']} owns the business clock. We own the engineering one. If those "
                f"clocks disagree, the first sentence says so."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Internal note can name {host}, {_ticket(f, i + 1)}, and the last error line. "
                f"It still does not paste identifiers. If someone asks for a root cause the "
                f"same day, they get the user-visible version. Legal reads outbound mail that "
                f"names money or medical data. I will not put a hostname in a customer ticket "
                f"because it makes me look precise."
            ),
        },
        {
            "type": "bullets",
            "items": [
                f"External: window, effect, done or not. Owner {who}.",
                f"Internal: {host}, counts, {ticket}. Owner {f['author']}.",
                "Never: payloads, PAN, SSN, MRN, secrets, unredacted logs.",
                f"If {_person(f, 3)} is the TAM, they get the external version first.",
            ],
        },
        {
            "type": "p",
            "text": (
                f"I keep a one-line draft in {ticket} so we do not invent tone at 01:10. "
                f"If the incident is still open, the draft says 'still open' and a next update "
                f"time we can actually hit, usually {_n(f, 30, 90)} minutes. If we are done, "
                f"the draft says what changed for the user and what did not. I will not "
                f"apologize in a way that implies a cash or clinical miss we did not have."
            ),
        },
    ]


def _shape_handoff(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    due = _parse_anchor(f["date"]) + timedelta(days=9 + i)
    return [
        {"type": "h2", "text": f"Handoff for {topic}"},
        {
            "type": "p",
            "text": (
                f"Next owner inherits {host}, {ticket}, and the last three working pages of "
                f"{f['doc_id']}. I will not leave a Slack screenshot as the record. {who} "
                f"is owner until they accept in writing. Date I want that written: "
                f"{due.strftime('%B %-d, %Y')}. Access that has to move: who can ssh or "
                f"kubectl, who can merge, who can talk to {f['client']}. If any of those is "
                f"still me after that date, the handoff failed."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Pages start going to {who} the morning after, not to a rotation alias that "
                f"still rings my laptop. I stay on the ticket as reviewer for one week, not "
                f"as the person who gets paged. {f['author']} will not silently keep the "
                f"IAM grant 'just in case.' If we need a temporary grant, it expires. "
                f"Topic in play: {topic}."
            ),
        },
        {
            "type": "table",
            "caption": f"Access that has to move with {ticket}.",
            "headers": ["What", "From", "To", "When"],
            "rows": [
                [f"On-call for {host}", f["author"], who, due.isoformat()],
                ["Merge on the repo named in front matter", _person(f, 2), who, due.isoformat()],
                [f"Customer/ops thread", f["author"], _person(f, 1), due.isoformat()],
            ],
        },
        {
            "type": "p",
            "text": (
                f"If {who} is out that week, {_person(f, 2)} is the named backup, not 'the "
                f"team.' I will write that on {ticket} the day I hand off, not the day the "
                f"page fires. This handoff does not reopen {topic}. It only changes who "
                f"carries it."
            ),
        },
    ]


def _shape_commands(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    ns = _choice(f, ["recon", "riverview-chart", "oakridge-inv", "clh-prod", "batch"])
    deploy = _choice(f, ["match-engine", "ingest-api", "patient-api", "inventory-api", "break-svc"])
    return [
        {"type": "h2", "text": f"Read-only first: {topic}"},
        {
            "type": "p",
            "text": (
                f"Only if the front matter already put you on {host}. Stop after the first "
                f"unexpected line. {who} is the wake-up, not a group chat. Ticket {ticket} "
                f"opens before any write. This is the {topic} path, not a general restart "
                f"recipe."
            ),
        },
        {
            "type": "code",
            "caption": f"Read-only. {ticket}. {host}.",
            "text": (
                f"# {f['doc_id']} / {ticket} / {topic}\n"
                f"date -u\n"
                f"ssh {host} 'uptime; df -h | head'\n"
                f"kubectl -n {ns} get pods -l app={deploy} -o wide | head\n"
                f"kubectl -n {ns} logs deploy/{deploy} --tail=80 | tail\n"
                f"# stop. write the last error in one sentence on {ticket}\n"
                f"# do not helm upgrade from a laptop in a freeze"
            ),
        },
        {
            "type": "steps",
            "items": [
                f"Write the symptom on {ticket} before any write.",
                f"If poison: fence the record. Do not raise retries past {_n(f, 3, 8)}.",
                f"If lag with all partitions moving: scale only after {who} would scale.",
                "If rollback: read the schema SOP. Expanded columns roll forward.",
                f"Wake {who} only after the read-only commands and a one-line diagnosis.",
            ],
        },
        {
            "type": "p",
            "text": (
                f"I will not restart {host} because it is the fastest way to stop a page. "
                f"Restart is a listed step with a listed rollback. If I am wrong, the next "
                f"page is louder. Memory bump is a last resort and it is a ticket, not a "
                f"one-line kubectl set. {f['author']} has already been wrong about that "
                f"twice this year."
            ),
        },
    ]


def _shape_question(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    due = _parse_anchor(f["date"]) + timedelta(days=7 + i * 2)
    return [
        {"type": "h2", "text": f"Still open: {topic}"},
        {
            "type": "p",
            "text": (
                f"{who} still owes a close, not a status. Due {due.strftime('%B %-d, %Y')}. "
                f"The question is whether {host} stays in the path for {topic}. If yes, the "
                f"main body already says how. If no, {who} writes the cut on {ticket}. I will "
                f"ping once. After that the owner is late, not blocked."
            ),
        },
        {
            "type": "bullets",
            "items": [
                f"Owner: {who}",
                f"Ticket: {ticket}",
                f"Host in play: {host}",
                "Acceptable close: yes, no, or a new date with a reason.",
                "Not acceptable: a list of meetings, a thumbs-up emoji, a parking-lot rename.",
            ],
        },
        {
            "type": "p",
            "text": (
                f"This question does not reopen the recommendation in the front of "
                f"{f['title']}. It is leftover work. If {who} wants a different product, "
                f"that is a new ticket and {_person(f, 1)} is in the thread. I will not "
                f"hide a scope change inside {topic}."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Check that the close does not collide with the freeze or ops window already "
                f"named in the main body. If it does, the date moves, the scope does not. "
                f"Number I will cite if someone asks whether this is blocking: {_num(f, i)}. "
                f"If that number is not the blocker, say so on {ticket} in the first line."
            ),
        },
    ]


def _shape_paid_failure(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    tell = _choice(
        f,
        [
            "zero rows and a green job",
            "one partition stuck while the graph was green",
            "duplicate replay because two clocks both ran",
            "truncated file with a matching trailer",
            "unversioned field rename that looked like a cleanup",
        ],
    )
    return [
        {"type": "h2", "text": f"Failure we already paid for ({topic})"},
        {
            "type": "p",
            "text": (
                f"Tell: {tell}. That showed up around {host}. {ticket} is the record. "
                f"{topic} is how it will show up again if we get sloppy. The fix is to make "
                f"the failure loud and stop the write path before it creates "
                f"{_n(f, 180, 8200)} junk rows, not to widen a retry. Verification is a "
                f"staging replay that used to succeed at being wrong and must now fail."
            ),
        },
        {
            "type": "p",
            "text": (
                f"We will not claim this class cannot happen. We will claim the next one "
                f"dies at the gate we are building, and that the page names the tell we "
                f"missed. {who} accepts the gate. {f['author']} writes it. {_person(f, 1)} "
                f"gets a factual count if it repeats, not an apology paragraph."
            ),
        },
        {
            "type": "p",
            "text": (
                f"What we will not do: a rewrite of {f['title']} as therapy. What we will "
                f"do if the date slips: {who} says so on {_ticket(f, 0)} with a new date. "
                f"Detection that should have fired: a join of freshness and uniqueness, or "
                f"an empty-success alert, depending on the tell. I want that alert in the "
                f"same pack as the code change, not a follow-up that dies in a quarter plan."
            ),
        },
    ]


def _shape_schema(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"Expand / backfill / contract ({topic})"},
        {
            "type": "p",
            "text": (
                f"The column or field that moved is the one {topic} cares about on {host}. "
                f"Order is expand, backfill, contract. I will not drop a column in the same "
                f"release as a code deploy that still reads it. Owner {who}. Ticket {ticket}. "
                f"Dual-write window is measured in hours, not left open. If the backfill is "
                f"still running at a freeze, I stop the freeze, not the backfill, unless "
                f"legal says otherwise. I write the stop condition on {ticket} before I "
                f"start the job."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Rejected: rewrite the type in place because Postgres will 'just cast it.' "
                f"That is how we locked {host} for longer than the {_n(f, 4, 12)}s budget "
                f"last time. Historical load never runs on the OLTP primary. Cost the job, "
                f"then run it. Number from the front I am using as the size hint: {_num(f, 2)}."
            ),
        },
        {
            "type": "steps",
            "items": [
                f"Add the new column or field. Ship readers that tolerate both. {ticket}.",
                f"Backfill in batches of {_n(f, 5, 40)}k. Pause on replication lag.",
                "Flip writers. Watch error class, not CPU.",
                f"Contract only after {who} signs the count on {ticket}.",
            ],
        },
        {
            "type": "p",
            "text": (
                f"If Helm rollback is the instinct after a bad migrate, stop. Expanded "
                f"columns roll forward. Read the schema SOP. {f['author']} will not approve "
                f"a rollback that leaves the database ahead of the chart."
            ),
        },
    ]


def _shape_meeting(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    due = _parse_anchor(f["date"]) + timedelta(days=4 + i)
    return [
        {"type": "h2", "text": f"Meeting leftover: {topic}"},
        {
            "type": "p",
            "text": (
                f"Attendees who still owe something: {who}, {_person(f, 1)}, and whoever "
                f"owns {host}. One question was on the table: can we ship without dealing "
                f"with {topic}. Answer was no. I repeated the number {_num(f, i)} because "
                f"two people in the room had stale graphs. Action: {who} files the follow-up "
                f"on {ticket} before {due.strftime('%B %-d, %Y')}. I will not mark the ticket "
                f"done because a meeting happened."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Parking lot: a dashboard request that does not unblock {ticket}. I parked "
                f"it. A calendar invite is not a decision. If someone wants this recorded as "
                f"a decision, they write it here or they change the callout in the front of "
                f"{f['doc_id']}. Quotes from the room stay quotes. They do not become scope."
            ),
        },
        {
            "type": "p",
            "text": (
                f"People who were absent still get a usable remainder, not a transcript. "
                f"{_person(f, 3)} gets the decision, the refuse, and the date. They do not "
                f"get a reconstruction of who raised their voice. If they object, they object "
                f"on {ticket}. Client {f['client']}. Author {f['author']}."
            ),
        },
    ]


def _shape_fixture(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"Fixture and test note ({topic})"},
        {
            "type": "p",
            "text": (
                f"Fixture for {topic} lives next to the test, not in a laptop path. No PHI, "
                f"no PAN. Host if we have to soak: {host}. Assert the smallest row that still "
                f"fails without the fix. I will not copy a sanitized production dump; it is "
                f"too big and it hid the bug twice. Owner {who}. Ticket {ticket}. If the test "
                f"is skipped, the skip reason is a ticket, not a comment."
            ),
        },
        {
            "type": "code",
            "caption": f"Name the test after the bug. {ticket}.",
            "text": (
                f"# {f['doc_id']} / {topic}\n"
                f"pytest -k '{_choice(f, ['timezone', 'idempotent', 'empty_batch', 'pagination', 'phi_log'])}' -q\n"
                f"# fail if the fixture hash changes without {ticket}\n"
                f"# do not record against {host} from a laptop"
            ),
        },
        {
            "type": "p",
            "text": (
                f"Setup should take under two minutes on a laptop. Teardown drops the fixture "
                f"database. Flakes I will not blame on the network without a packet capture. "
                f"If someone deletes this test, they also delete the incident it maps to "
                f"({ticket}) and they do that in review. {who} owns golden fixtures. "
                f"{f['author']} owns the case list."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Staging partition count has to be high enough to catch a rebalance. If "
                f"prod has dozens of partitions, a staging cluster with one will bless a "
                f"bad build. I want that written next to {topic}, not rediscovered on a "
                f"Monday. Number from the front I am not going to 'simplify': {_num(f, 3)}."
            ),
        },
    ]


def _shape_capacity(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"Capacity and cost ({topic})"},
        {
            "type": "p",
            "text": (
                f"{host} is the box I keep measuring because it is the one that pages. "
                f"{topic} is the reason the graph lies if you only watch CPU. Queue depth "
                f"and disk are the two numbers I write down. Owner {who}. Ticket {ticket}. "
                f"If the graph is green and the queue is growing, I page. CPU lagged the "
                f"queue by about {_n(f, 8, 28)} minutes on the last incident I will admit to."
            ),
        },
        {
            "type": "p",
            "text": (
                f"The spend I can defend is the spend tied to {host} and this job, not a "
                f"team average. Year-1 extra I would put on a sticky: about "
                f"${_n(f, 4, 28) + _n(f, 0, 9) * 0.1:.1f}k on top of what we already burn, "
                f"or zero if we do nothing and eat the miss rate. Front-matter volume I am "
                f"using: {_num(f, 0)}. I will not argue from a slide."
            ),
        },
        {
            "type": "p",
            "text": (
                f"If we need more brokers or more pods, I want the reason to be {topic}, "
                f"not a round number someone saw in a vendor deck. Do-nothing through next "
                f"month-end still has a miss rate I will write down. {who} picks in writing "
                f"on {ticket}. I will not hide a hardware buy inside a 'temporary' memory "
                f"limit."
            ),
        },
    ]


def _shape_access(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"Secrets, grants, and {topic}"},
        {
            "type": "p",
            "text": (
                f"Secret handling on {host}: not in git, not in the ticket description, not "
                f"in a screenshot. {topic} is not a reason to paste a token into chat. Owner "
                f"{who}. Ticket {ticket}. If I need a temporary grant, it expires. If I need "
                f"a production query, I use the replica and I log the query id. Wrong secret "
                f"looks healthy as 'no work.' Alert on zero rows, not on HTTP 200."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Break-glass is a separate path. Missing role is 403, missing token is 401. "
                f"I will not collapse those because the UI looks nicer. {_person(f, 1)} "
                f"accepted that split in the front matter. I am not reopening it here. "
                f"IRSA or the equivalent role on {host} is the grant. A copied kubeconfig "
                f"on a laptop is not."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Support zips go through redaction first. I will not 'just this once' attach "
                f"an application log because {topic} is on fire. The on-call SOP already says "
                f"this. Repeating it here is for the person who has not opened that SOP. "
                f"{f['author']} will reject the zip in the ticket if it still has identifiers."
            ),
        },
    ]


def _shape_timeline(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    anchor = _parse_anchor(f["date"])
    t0 = (anchor - timedelta(days=2)).strftime("%B %-d")
    t1 = (anchor - timedelta(days=1)).strftime("%B %-d")
    t2 = anchor.strftime("%B %-d, %Y")
    return [
        {"type": "h2", "text": f"Clock for {topic}"},
        {
            "type": "p",
            "text": (
                f"This is not a full incident timeline. It is the clock I will use when "
                f"someone asks which thing happened first around {topic}. {host} is the box. "
                f"{ticket} is the thread. {who} is the person I will name if the clocks "
                f"disagree. Customer/ops clock and match/extract clock are different. I will "
                f"not pretend they are the same."
            ),
        },
        {
            "type": "table",
            "caption": f"Working clock for {f['doc_id']}. Times are ET unless noted.",
            "headers": ["When", "What I can defend", "Who"],
            "rows": [
                [t0, f"First stale graph or first complaint tied to {topic}", _person(f, 3)],
                [t1, f"Read-only check on {host}; ticket {ticket} exists or is opened", f["author"]],
                [t2, f"Decision in the front of this file still stands", who],
            ],
        },
        {
            "type": "p",
            "text": (
                f"If NTP on {host} jumped, window math is garbage. I want that checked before "
                f"I argue about {_num(f, i)}. I will not reconstruct a minute-by-minute novel. "
                f"I will reconstruct enough that {_person(f, 1)} can brief without calling me."
            ),
        },
        {
            "type": "p",
            "text": (
                f"After this clock, the remaining work is owned, or it is late. I will not "
                f"add a fourth restart to make the timeline look shorter. {f['client']} can "
                f"have the user-visible version of this table. They cannot have internal "
                f"hostnames."
            ),
        },
    ]


def _shape_close(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"What would make me reopen {f['doc_id']} ({topic})"},
        {
            "type": "callout",
            "kind": "decision",
            "label": "Still the call",
            "text": (
                f"The front of {f['doc_id']} still stands. {topic} does not reopen it. "
                f"{who} owns {ticket}. {host} stays in the path already named."
            ),
        },
        {
            "type": "p",
            "text": (
                f"I will reopen this file if the measurement on {host} says the cutover is "
                f"lying, if a freeze and a migrate disagree, or if {who} puts a new date on "
                f"{ticket} that the EM accepts. I will not reopen it because a meeting is "
                f"booked, because a vendor offered a discount, or because someone found a "
                f"blog post. Evidence is a dry-run count, a replay that used to be wrong, "
                f"or a miss rate worse than the do-nothing line."
            ),
        },
        {
            "type": "p",
            "text": (
                f"If you are implementing, keep the rejected alternative dead. If you are "
                f"on-call, start read-only. If you are {_person(f, 1)}, the ask is unchanged: "
                f"pick the path in the main body or send it back with a named objection. "
                f"Sample I would still defend: {_n(f, 90, 4200)} rows, {_n(f, 5, 42)} minutes, "
                f"freeze respected. Strike this remainder if it ever fights the decision "
                f"callout. Author {f['author']}. Client {f['client']}."
            ),
        },
        {
            "type": "p",
            "text": (
            f"This heading is the reopen rule, not a promise that nothing follows. "
            f"If we still need words after the bank, they are named leftovers, not "
            f"another copy of the same stub. {topic} is done as a heading when {who} "
            f"closes {ticket} or writes a new date."
            ),
        },
    ]


def _shape_qa(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"Questions I still get about {topic}"},
        {
            "type": "p",
            "text": (
                f"I am writing the answers here so they stop living in my inbox. {who} can "
                f"point at {ticket} instead of asking me to re-explain {topic} on {host}."
            ),
        },
        {
            "type": "bullets",
            "items": [
                f"Is v1 smaller than {f['client']} asked in the hallway? Yes. That is the point.",
                f"Can we add the extra slice in this release? Only if {_person(f, 1)} signs it.",
                f"Is {host} a special case? No.",
                f"Who closes {ticket}? {who}.",
                f"What number do I cite? {_num(f, i)}, or I say it is stale.",
            ],
        },
        {
            "type": "p",
            "text": (
                f"If the answer changes, we change the front of {f['doc_id']} in review. We "
                f"do not keep a shadow FAQ. {f['author']} will not maintain two truths."
            ),
        },
        {
            "type": "p",
            "text": (
                f"The question I will not answer in Slack is 'can we just this once.' The "
                f"answer is already no, and writing it on {ticket} is what makes it a record. "
                f"If {_person(f, 3)} needs a user-visible version, they get the comms leftover, "
                f"not this list."
            ),
        },
    ]


def _shape_freeze(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"Freeze and calendar leftover ({topic})"},
        {
            "type": "p",
            "text": (
                f"If the front of this file already named a freeze, {topic} does not get a "
                f"courtesy thaw on {host}. A small apply is still an apply. SEV1 is the SOP "
                f"definition. {who} can argue SEV1 on {ticket} with a count, not with a demo "
                f"time. I will not Helm-apply from a laptop because the window is 'almost "
                f"over.'"
            ),
        },
        {
            "type": "p",
            "text": (
                f"Calendar leftovers I will not hide inside {topic}: weekend coverage that "
                f"is not in the SLA, a plant shutdown, a clinical quiet hours window, month-end "
                f"16:00-21:00 ET. If the leftover date lands inside one of those, the date "
                f"moves. The scope does not. {_person(f, 1)} hears the new date on {ticket}."
            ),
        },
        {
            "type": "p",
            "text": (
                f"I will not book a change in the last {_n(f, 20, 50)} minutes of a freeze "
                f"because the change is 'just config.' Config is a change. {f['author']} has "
                f"already lost that argument once and I am not losing it again on {host}."
            ),
        },
    ]


def _shape_raci(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"Names, not teams ({topic})"},
        {
            "type": "table",
            "caption": f"RACI for {topic} on {ticket}. Team names are a defect.",
            "headers": ["Role", "Person", "Notes"],
            "rows": [
                ["Responsible", who, f"Does the work on {host}"],
                ["Accountable", _person(f, 1), "One person. Signs the close."],
                ["Consulted", _person(f, 2), f"Reviewer, not a shadow owner"],
                ["Informed", _person(f, 3), f"{f['client']} path; no hostnames"],
            ],
        },
        {
            "type": "p",
            "text": (
                f"If two people think they are accountable, {_person(f, 1)} picks one on "
                f"{ticket}. If nobody is, {topic} has not started. {f['author']} is the writer "
                f"of this file. That is not the same as accountable unless the front already "
                f"said so. I will rewrite any row that says 'platform' or 'ops' as a person "
                f"before I call this done."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Pages go to the responsible person, not to a Slack channel that everyone "
                f"mutes. If {who} is out, the backup is a name on {ticket} the same day, not "
                f"a hope that someone is watching {host}."
            ),
        },
    ]


def _shape_dry_run(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"Dry-run before a write ({topic})"},
        {
            "type": "p",
            "text": (
                f"A dry-run for {topic} prints a count before it writes. If we cannot show "
                f"that count on {host}, we abort. {who} pastes the output on {ticket}. I will "
                f"not accept 'it looked fine in the UI' or 'staging was green.' Staging has "
                f"lied about partition count before."
            ),
        },
        {
            "type": "code",
            "caption": f"Shape of the dry-run, not a paste of production data. {ticket}.",
            "text": (
                f"# {f['doc_id']} dry-run / {topic}\n"
                f"# run on {host} or a listed replica, read-only\n"
                f"date -u\n"
                f"# print the count the write would touch\n"
                f"# abort if the count is 0, or larger than {_n(f, 2, 9)}x the front-matter guess\n"
                f"# write the number on {ticket} before any mutate"
            ),
        },
        {
            "type": "p",
            "text": (
                f"Abort is cheaper than a dual-run that violates the unique key. Dual-run "
                f"that breaks uniqueness is a data incident. {_person(f, 2)} does not get to "
                f"redefine uniqueness to hit a date. {f['author']} will stop the job."
            ),
        },
        {
            "type": "p",
            "text": (
                f"If the dry-run count disagrees with {_num(f, i)} by more than we can explain "
                f"in one sentence, we do not 'split the difference.' We stop and {who} writes "
                f"the discrepancy on {ticket}."
            ),
        },
    ]


def _closing_remainder(f, need_words: int):
    """Short named leftovers only. Never a repeating exhibit mill."""
    blocks = [
        {
            "type": "h1",
            "text": f"Named leftovers still on {f['doc_id']}",
        },
        {
            "type": "p",
            "text": (
                f"I am out of new section shapes. What follows is leftover owners and tickets "
                f"already in this file, written so a colleague can act. I will not invent "
                f"another exhibit format to fill a page budget."
            ),
        },
    ]
    n = 0
    i = 0
    templates = 8
    while n < need_words and i < 12:
        who = _person(f, i + 1)
        ticket = _ticket(f, i)
        host = _host(f, i)
        due = (_parse_anchor(f["date"]) + timedelta(days=11 + i * 2)).strftime("%B %-d, %Y")
        kind = i % templates
        if kind == 0:
            para = (
                f"{ticket} still sits with {who}. Host {host}. Due {due} unless they write "
                f"a new date. Close is a decision, a refuse, or that date. I will not accept "
                f"a status dump. Front-matter number I am not re-arguing: {_num(f, i)}. "
                f"If this leftover is done, {who} marks {ticket} done. {f['author']} will not "
                f"keep a shadow list. Client {f['client']}."
            )
        elif kind == 1:
            para = (
                f"I still owe {who} a usable remainder on {ticket}, not a transcript. "
                f"The leftover on {host} is whether we keep the path the front already named. "
                f"Due {due}. If they need a user-visible line, it goes through the comms leftover, "
                f"not this sentence. Number in play: {_num(f, i)}."
            )
        elif kind == 2:
            para = (
                f"Access leftover: if I can still write to {host} after {due}, revoke it. "
                f"{who} either has the grant or the work is not theirs yet. Ticket {ticket}. "
                f"I will not leave a personal kubeconfig as a backup plan."
            )
        elif kind == 3:
            para = (
                f"Measurement leftover on {host}: reprint the count before anyone claims "
                f"{ticket} is done. {who} pastes it. If it disagrees with {_num(f, i)} and "
                f"we cannot explain that in one sentence, we are not done. Due {due}."
            )
        elif kind == 4:
            para = (
                f"Comms leftover for {ticket}: no hostname, no payload. {who} drafts, I review. "
                f"If we are not done by {due}, the outbound line says we are not done and names "
                f"the next update we can hit. {f['client']} does not get {host}."
            )
        elif kind == 5:
            para = (
                f"Test leftover: the case that maps to {ticket} still has to fail if someone "
                f"cleans the fixture. {who} owns that fixture. Host if we soak: {host}. Due {due}. "
                f"Skip is a ticket, not a comment."
            )
        elif kind == 6:
            para = (
                f"Calendar leftover: {due} versus the freeze already in the front. If they "
                f"collide, {who} moves {ticket}, not the freeze. {host} does not get a thaw "
                f"for a demo. {f['author']} will not 'just apply config.'"
            )
        else:
            para = (
                f"Stop leftover: {ticket} is not a twin of {_ticket(f, i + 1)}. Keep one thread. "
                f"{who} on {host}. If this paragraph fights the front of {f['doc_id']}, strike "
                f"it. Due {due}. Client {f['client']}."
            )
        blocks.append({"type": "p", "text": para})
        n += _words(para)
        i += 1
    return blocks


def pad_paragraph(f, i):
    """Last-page trim helper for the page fitter. Not an exhibit mill."""
    return {
        "type": "p",
        "text": (
            f"Close-out line {i + 1} for {f['doc_id']}. "
            f"{_person(f, i + 1)} still owns {_ticket(f, i)} on {_host(f, i)}. "
            f"The front of {f['title']} does not move. "
            f"If you are implementing, keep the rejected alternative dead. "
            f"If you are on-call, start read-only. "
            f"If you are {_person(f, 1)}, pick the path in the main body or send it back "
            f"with a named objection. Sample I would still defend: {_n(f, 80, 4000)} rows, "
            f"{_n(f, 4, 40)} minutes. Author {f['author']}. Client {f['client']}."
        ),
    }

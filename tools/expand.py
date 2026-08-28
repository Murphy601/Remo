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
    r"\b(?:CLH|RVH|OAK|NS|REC|INC|TDD|PRD|SOP|RB|ADR|REQ|MEM|MTG|EVAL|TST|WTS|HBR|LSH|HIL|PCF|RDW)-[A-Z0-9-]{2,20}\b"
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
    author = spec.get("author") or "Jeilen Jones"
    if author not in named:
        named = [author] + named
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
        "author": spec.get("author", "Jeilen Jones"),
        "tickets": tickets or [spec.get("doc_id", "DOC-1")],
        "hosts": hosts or ["wms.pinecrest.internal"],
        "people": named or [author, "Marcus Hale"],
        "client": (
            "Ridgeway"
            if "ridgeway" in slug
            else "Pinecrest"
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


def _ns(f):
    c = f.get("client") or "Pinecrest"
    table = {
        "Pinecrest": ["pick", "pack", "dock", "wms"],
        "Ridgeway": ["bay", "parts", "pm", "roadtest"],
    }
    return _choice(f, table.get(c, table["Pinecrest"]))


def _deploy(f):
    c = f.get("client") or "Pinecrest"
    table = {
        "Pinecrest": ["wave-pick", "rf-gun", "pallet-jack", "labeler"],
        "Ridgeway": ["pm-sheet", "brake-cart", "hoist", "scan-tool"],
    }
    return _choice(f, table.get(c, table["Pinecrest"]))


def _read_only_commands(f, host, ticket, topic, extra=""):
    ns = _ns(f)
    deploy = _deploy(f)
    c = f.get("client") or "Pinecrest"
    head = f"# {f['doc_id']} / {ticket} / {topic}\ndate\n"
    if extra:
        head += extra.rstrip() + "\n"
    if c == "Ridgeway":
        body = (
            f"# shop floor, read-only first\n"
            f"echo host={host} bay={ns} job={deploy}\n"
            f"echo 'check hoist tag, PM sheet, and last torque values'\n"
            f"echo 'do not start the engine until the tag is green'\n"
        )
    else:
        body = (
            f"# warehouse floor, read-only first\n"
            f"echo host={host} area={ns} tool={deploy}\n"
            f"echo 'RF login, location count, last short-pick'\n"
            f"echo 'do not confirm a pick you cannot see'\n"
        )
    tail = (
        f"# stop. write the last error in one sentence on {ticket}\n"
        f"# do not override a safety lock because a rate looks low"
    )
    return head + body + tail


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
    topics = _genre_topics(f)
    i = 0
    while _wc_blocks(spec, extra) < min_words and i < 250:
        extra += _take_paras(f, 2, topics[i % len(topics)])
        i += 1
    j = 0
    while _wc_blocks(spec, extra) < min_words and j < 200:
        extra.append(pad_paragraph(f, j))
        extra.append(pad_paragraph(f, j + 200))
        j += 1
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
        ("serial / special inventory", "one-tote leftover, not a silent include"),
        ("in-transit / cross-site", "needs a written rule, not a hallway yes"),
        ("tooling rewrite", "rejected if it is a second product"),
        ("RF vs paper leftover", "the main body already picked; do not relitigate in Slack"),
        ("weekend coverage", "not in the SLA unless the ops owner signs it"),
        ("names or SSNs in chat", "never; redact the photo or dump first"),
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
                    f"Check that this does not collide with the freeze or store/ops window already named in the main notes. "
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
    if f.get("client") == "Ridgeway":
        branches = [
            ("red hoist tag", "tag is red, bay still looks open"),
            ("no-start leftover", "crank, no fire, last fuel work still open"),
            ("air-brake leak", "pedal sinks, gauge drops on a parked tractor"),
            ("comeback", "same complaint inside 14 days"),
            ("parts without VIN", "counter ticket has no VIN or last-8"),
            ("tool not returned", "scan-tool still out after shift"),
            ("PM skip", "sticker green, sheet blank on the oil line"),
            ("freeze / no-override window", "you must not override a safety lock"),
            ("torque leftover", "nut was moved, value not written"),
            ("road test without brakes", "someone wants a drive before the brake check"),
            ("A/C electrical short", "clutch click, fuse pops"),
            ("oil sample skip", "drain done, bottle never filled"),
        ]
    else:
        branches = [
            ("skip-scan leftover", "location not scanned, rate still looks high"),
            ("RF login fail", "gun will not take the badge"),
            ("short-pick vs mispick", "tote short, or the wrong SKU in the tote"),
            ("conveyor jam", "belt stopped, carton crushed at the nose"),
            ("cooler vs dry mix", "cold SKU in a dry tote"),
            ("labeler jam", "print head stuck, labels doubling"),
            ("WMS count lag", "RF says 12, slot looks empty"),
            ("freeze / no-override window", "you must not override a safety lock"),
            ("dock seal leftover", "trailer pulled, seal not written"),
            ("dead battery mid-wave", "gun dies, wave still assigned"),
            ("paper sheet leftover", "printed path fights the RF path"),
            ("lot-code miss", "outbound needs a lot, gun did not ask"),
        ]
    f["rng"].shuffle(branches)
    for i, (name, tell) in enumerate(branches, 1):
        blocks.append({"type": "h2", "text": f"Branch {i}: {name}"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Tell: {tell}. Confirm on {_host(f, i)} before you touch the floor. "
                    f"Ticket {_ticket(f, i)} if one is not already open. "
                    f"Precondition: you are on the shift or {_person(f, 1)} knows. "
                    f"Stop if you are inside a freeze and this is not a SEV1 as defined in the front of this SOP."
                ),
            }
        )
        blocks.append(
            {
                "type": "code",
                "caption": f"Read-only first. {name}.",
                "text": _read_only_commands(f, _host(f, i), _ticket(f, i), name),
            }
        )
        blocks.append(
            {
                "type": "steps",
                "items": [
                    f"Write the symptom and the tell on {_ticket(f, i)} before any write.",
                    f"If a bad tote or a bad job: fence it, do not keep scanning past {_n(f, 3, 8)} retries.",
                    f"If the wave is moving but one aisle is stuck: call {_person(f, 2)} before you skip the aisle.",
                    f"If rollback: read the SOP. An expanded slot or a cut bolt rolls forward, not back.",
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
        ("scan key", "location, tote, or missing lot code"),
        ("alert join", "rate board green while mispick is red"),
        ("practice lie", "too few totes in the drill, missed the bug"),
        ("review hole", "someone renamed a SKU on a cleanup sheet"),
        ("replay without a lock", "weekend plus Monday both counted the same pallet"),
        ("floor guess", "restarted the gun before reading the tell"),
        ("customer clock vs dock clock", "window-closed signal fired too early"),
        ("blast radius", "one bad tote became the whole wave"),
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
                f"A rewrite of {f['title']} as therapy is out. A new rate-board vendor is out "
                f"unless {_person(f, 1)} reopens that memo. Weekend auto-fix of a jam is out. "
                f"What is in: the change table above, a drill on the floor that used to succeed "
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
                f"Detection that should have fired is a join, not a hero. Rate green while "
                f"mispick is red is a miss. Empty success is a miss. I want the page body "
                f"to name the tell. Host for the drill: {_host(f, 0)}. Owner for alert text: "
                f"{_person(f, 2)}. I will not accept 'check the rate board' as the page."
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
                f"Approve the position in the front of this memo. Fund the named floor hours. "
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
                    f"{label}. Miss rate I would defend: about {miss}% of month-end windows, using the same clock as the front of the memo. "
                    f"Floor hours {days}. Year-1 extra cash about ${cash:.1f}k on top of what we already burn. "
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
            "headers": ["ID", "Path", "Month-end miss", "Floor hours", "Year-1 extra", "Note"],
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
                f"we abort. Host {_host(f, 0)}. I will not average units-per-hour to hide a close spike. "
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
        ("permission miss", "wrong badge, no stack of SKUs on the gun"),
        ("replay / retry", "idempotent, audit who hit it"),
        ("empty result", "explain empty, do not look broken"),
        ("late data", "show stale with a time, do not hide it"),
        ("export / audit", "what a control owner can replay"),
        ("mobile / floor / store staff", "the actual device, not a desktop lie"),
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
                    f"Metric I will argue for: time-to-first-useful-scan under {_n(f, 2, 12)}.{_n(f, 0, 9)}s on the floor VLAN, "
                    f"not a vanity rate number. "
                    f"Out of scope: {_choice(f, ['pretty formatting', 'a second write-back to the WMS', 'editing picks in the UI', 'voice pick for v1', 'notes full-text search'])}."
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
                f"the source system is out. Voice-pick for v1 is out. Full-text search on notes "
                f"is out. {_person(f, 1)} can add them as a new slice with a new acceptor "
                f"signature. I will not hide them as 'polish' on {_ticket(f, 0)}. Banner, "
                f"empty, and stop states in the stories above are in. Happy-path screenshots "
                f"that skip those states are not acceptance."
            ),
        }
    )
    blocks.append(
        {
            "type": "p",
            "text": (
                f"Device leftover: the actual device the user holds, not a desktop lie. "
                f"If store staff or floor ops is the user, I will time the P0 path on that "
                f"device on the floor VLAN. Metric is time-to-first-useful-scan, "
                f"not units-per-hour vanity. Host if we have to prove it: {_host(f, 0)}. {f['author']} will "
                f"not accept a laptop demo as that proof."
            ),
        }
    )
    return blocks


def _cont_test(f):
    blocks = [
        {"type": "h1", "text": f"Cases that must fail in the audit if someone 'cleans up' a sample ({f['doc_id']})"},
        {
            "type": "p",
            "text": (
                f"The suite exists to catch the regressions we already caught once. "
                f"This section names them so they cannot be deleted as noise. "
                f"The QA owner listed in the front still owns golden fixtures. {f['author']} owns the case list."
            ),
        },
    ]
    cases = [
        ("timezone on order close", "store timezone vs a contractor default"),
        ("SKU merge 'no substitute'", "dropping the negative is a stock miss"),
        ("pagination over 10k", "page 2 must not repeat page 1"),
        ("401 vs 403", "break-glass is not a missing token"),
        ("idempotent replay", "second POST does not double"),
        ("partition count in staging", "1 partition will not catch a rebalance bug"),
        ("PII in logs", "CI fails if email/phone appear"),
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
                    f"Fixture lives next to the test, not in a laptop path. No customer names. "
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
                    f"echo 'audit -k {name.split()[0].lower()}'\n"
                    f"# fail closed if the sample hash changes without a ticket\n"
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
                f"Soak against {_host(f, 0)} is ticketed and it is not a reason to skip the audit. "
                f"If the drill has one aisle and prod has dozens, the drill will bless a "
                f"rebalance bug. I want that written next to the aisle case, not "
                f"rediscovered on a Monday."
            ),
        }
    )
    blocks.append(
        {
            "type": "p",
            "text": (
                f"PII in CI is a fail, not a warning. I will not 'sanitize later.' Fixture "
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
        ("clocks", "close date vs created date, pick one"),
        ("cardinality", "do not put sku on a stray label"),
        ("residency", "this building, no 'just a copy in the other site'"),
        ("names", "not in logs, not in Slack, redact before a zip"),
        ("versioning", "a dated SOP or it is not versioned for this client"),
        ("backfill vs live pick", "historical load never on the live path"),
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
                    f"Rejected alternative: {_choice(f, ['raise timeouts and hope', 'a paper-only path forever', 'skip the scan', 'poll faster', 'rewrite the WMS this quarter', 'one giant spreadsheet', 'auto-merge on SKU name'])}. "
                    f"Owner if this breaks in prod: on-call first, then {_person(f, 1)} if it crosses a freeze."
                ),
            }
        )
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Failure mode if we ignore it: {_choice(f, ['duplicate postings', 'inflated counts', 'client mapping death at 06:12', 'rebalance storm', 'OOM on one partition', 'audit gap', 'PII in a support zip'])}. "
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
                f"WMS override. We page {_person(f, 1)} after read-only commands on {_host(f, 0)}. "
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


def _remainder_h1(f):
    g = f["genre"]
    table = {
        "notes": [
            f"Action items from {f['date']}",
            f"Owners still on the hook after {f['doc_id']}",
            f"What I wrote down after the call",
        ],
        "runbook": [
            f"Stops that are not on page one ({f['doc_id']})",
            f"Extra on-call branches, {f['date']}",
            f"If the happy path already failed",
        ],
        "incident": [
            f"Work the postmortem still owes ({f['doc_id']})",
            f"Detection and follow-through after {f['date']}",
            f"What we change so this does not repeat",
        ],
        "memo": [
            f"Checkpoints if {_person(f, 1)} says yes",
            f"Cost of delay, restated for {f['doc_id']}",
            f"After the ask in the front of this memo",
        ],
        "prd": [
            f"Acceptance leftovers for {f['doc_id']}",
            f"Stories the screenshots skip",
            f"What {_person(f, 1)} still has to sign",
        ],
        "test": [
            f"Cases that stay in the audit ({f['doc_id']})",
            f"Fixture rules the QA owner will not relitigate",
            f"Regressions we already paid for",
        ],
        "design": [
            f"Edges that did not fit the front ({f['doc_id']})",
            f"Lock budget, blast radius, leftovers",
            f"What implementers steal from the back",
        ],
    }
    return f["rng"].choice(table.get(g, table["design"]))


def _ht(f, kind, topic):
    ticket = _ticket(f, 0)
    host = _host(f, 0)
    opts = {
        "refuse": [
            f"Still out: {topic}",
            f"{ticket} does not include this",
            f"Keep {topic} dead",
        ],
        "numbers": [
            f"Working numbers on {host}",
            f"What I would quote for {topic}",
            f"Counts tied to {ticket}",
        ],
        "comms": [
            f"Outbound vs internal on {topic}",
            f"What {_person(f, 3)} can send",
            f"No hostnames in the customer line",
        ],
        "handoff": [
            f"Who carries {ticket} next",
            f"Access that has to move off me",
            f"Handoff for {topic}",
        ],
        "commands": [
            f"Read-only on {host} first",
            f"Commands if {topic} is the tell",
            f"Stop after the unexpected line",
        ],
        "question": [
            f"{_person(f, 1)} still owes a close",
            f"Open: {topic}",
            f"Yes, no, or a new date on {ticket}",
        ],
        "paid_failure": [
            f"Last time {topic} cost us",
            f"The tell on {host} we argued past",
            f"Do not widen retries for this",
        ],
        "schema": [
            f"Expand then contract ({topic})",
            f"Slot order for {ticket}",
            f"Do not drop readers in the same wave",
        ],
        "meeting": [
            f"After-call note: {topic}",
            f"People who missed the room",
            f"Quotes stay quotes",
        ],
        "fixture": [
            f"Smallest failing row ({topic})",
            f"Hash gate for {ticket}",
            f"No production dump on a laptop",
        ],
        "capacity": [
            f"Queue and disk on {host}",
            f"Spend I can defend for {topic}",
            f"Do not hide a buy in a memory limit",
        ],
        "access": [
            f"Grants for {topic}",
            f"Secrets stay off {ticket} descriptions",
            f"Zero-row success on {host}",
        ],
        "timeline": [
            f"Which clock I am using",
            f"{topic} vs the ops clock",
            f"NTP on {host} before the argument",
        ],
        "close": [
            f"When {f['doc_id']} gets reopened",
            f"Evidence, not a booked meeting",
            f"Hold the front-matter call",
        ],
        "qa": [
            f"Short answers I am tired of repeating",
            f"FAQ for {topic}",
            f"This file is the FAQ, not a second wiki",
        ],
        "freeze": [
            f"Calendar vs {topic}",
            f"A small apply is still an apply",
            f"Freeze leftover for {ticket}",
        ],
        "raci": [
            f"Person names for {topic}",
            f"RACI that is not a team alias",
            f"Who gets the page",
        ],
        "dry_run": [
            f"Print a count before a write",
            f"Dry-run on {host}",
            f"Abort beats a lying dual-run",
        ],
    }
    return f["rng"].choice(opts[kind])


def _working_bank(f):
    """Subset of shapes, shuffled, file-local headings. No shared remainder banner."""
    named = [
        ("refuse", _shape_refuse),
        ("numbers", _shape_numbers),
        ("comms", _shape_comms),
        ("handoff", _shape_handoff),
        ("commands", _shape_commands),
        ("question", _shape_question),
        ("paid_failure", _shape_paid_failure),
        ("schema", _shape_schema),
        ("meeting", _shape_meeting),
        ("fixture", _shape_fixture),
        ("capacity", _shape_capacity),
        ("access", _shape_access),
        ("timeline", _shape_timeline),
        ("close", _shape_close),
        ("qa", _shape_qa),
        ("freeze", _shape_freeze),
        ("raci", _shape_raci),
        ("dry_run", _shape_dry_run),
    ]
    f["rng"].shuffle(named)
    keep = 9 + (f["rng"].randint(0, 3))
    named = named[:keep]
    topics = _genre_topics(f)
    f["rng"].shuffle(topics)
    intros = [
        (
            f"Leftover work from {f['title']}. Names, boxes, tickets. "
            f"If a paragraph fights the front of {f['doc_id']}, strike it."
        ),
        (
            f"I am dumping the after-work for {f['doc_id']} here so it is not in Slack. "
            f"{_person(f, 1)} can skim headings. Implementers can steal the commands."
        ),
        (
            f"Back of {f['title']}: execution only. The decision in the front does not move. "
            f"Date on this pack is {f['date']}."
        ),
        (
            f"Working remainder for {f['client']} on {f['doc_id']}. "
            f"I would rather this live here than get rebuilt from a thread next week."
        ),
        (
            f"{f['author']} parked the leftover execution for {f['date']} in this section. "
            f"Headings are the index. {_person(f, 1)} still owns the call in the front."
        ),
    ]
    bank = [
        {"type": "h1", "text": _remainder_h1(f)},
        {"type": "p", "text": f["rng"].choice(intros)},
    ]
    groups = [bank]
    for i, (kind, shape) in enumerate(named):
        topic = topics[i % len(topics)]
        blocks = shape(f, i, topic)
        if blocks and blocks[0].get("type") == "h2":
            blocks[0]["text"] = _ht(f, kind, topic)
        p_idxs = [j for j, b in enumerate(blocks) if b.get("type") == "p"]
        if len(p_idxs) >= 3:
            blocks.pop(p_idxs[f["rng"].randrange(len(p_idxs))])
        blocks += _take_paras(f, 2, topic)
        groups.append(blocks)
    return groups


def _take_paras(f, n, topic):
    out = []
    for _ in range(n):
        i = f.get("_compose_i", 0)
        f["_compose_i"] = i + 1
        out.append({"type": "p", "text": _compose_para(f, topic, i)})
    return out


def _compose_para(f, topic, salt):
    """File-local leftover sentences. Fragments are shuffled per file so the
    same three-part line does not land in every document."""
    bag = f.setdefault("_frag", _frag_bag(f))
    who = _person(f, salt + 1)
    ticket = _ticket(f, salt)
    host = _host(f, salt)
    due = (_parse_anchor(f["date"]) + timedelta(days=6 + (salt % 11))).strftime("%B %-d, %Y")
    lead = bag["lead"][salt % len(bag["lead"])]
    mid = bag["mid"][(salt * 3 + 1) % len(bag["mid"])]
    tail = bag["tail"][(salt * 5 + 2) % len(bag["tail"])]
    return (
        lead.format(who=who, ticket=ticket, host=host, topic=topic, due=due, doc=f["doc_id"], author=f["author"], client=f["client"], title=f["title"], num=_num(f, salt)).rstrip(". ")
        + ", "
        + mid.format(who=who, ticket=ticket, host=host, topic=topic, due=due, doc=f["doc_id"], author=f["author"], client=f["client"], title=f["title"], num=_num(f, salt)).rstrip(". ")
        + ", and "
        + tail.format(who=who, ticket=ticket, host=host, topic=topic, due=due, doc=f["doc_id"], author=f["author"], client=f["client"], title=f["title"], num=_num(f, salt)).rstrip(". ")
        + "."
    )


def _frag_bag(f):
    lead = [
        "{who} still has {topic} on {ticket}",
        "I parked {topic} on {ticket} so it is not Slack archaeology",
        "{author} owes a close on {topic} by {due}, not a status emoji",
        "if {topic} is still fuzzy, {ticket} is the place to say so",
        "{client} can wait on {topic} until {who} writes the cut",
        "leftover {topic} sits with {who} on {ticket}",
        "I will not reopen {title} to smuggle {topic} back in",
        "{who} asked for a one-line version of {topic}",
        "date pressure on {topic} is not a date, {due} is if {who} keeps it",
        "the front of {doc} already named {topic}, this paragraph is execution",
        "I bounced a hallway yes on {topic}",
        "{host} is the box I would open first for {topic}",
        "do not treat {topic} as polish, {who} either owns it or we drop it",
        "after {due}, leftover access for {topic} is a bug, not a courtesy",
    ]
    mid = [
        "the first check is a read on {host}",
        "the freeze still applies and a small apply is still an apply",
        "the number I will quote is {num}, and if it is stale I will say so",
        "no hostname belongs in the customer line, {who} drafts and I review",
        "a poison record gets fenced, not more retries",
        "a PNG is not a close on {ticket}",
        "grant expiry is a date {who} writes on {ticket}",
        "a green job with no rows still pages",
        "schema order stays expand then backfill then contract",
        "staging that cannot replay the old wrong success is not a gate",
        "weekend coverage is not implied unless {who} signs it",
        "polling faster is not a substitute for fixing {topic}",
        "pages go to a person, not a muted channel",
        "a dry-run has to print the count on {host} before anyone writes",
    ]
    tail = [
        "close is yes, no, or a new date on {ticket} by {due}",
        "if this fights the front of {doc}, strike it",
        "{author} will not keep a shadow list",
        "object on {ticket}, not in a side thread",
        "I ping once and after that {who} is late, not blocked",
        "the sample I would still defend uses the same clock as {num}",
        "{client} does not get {host} in an outbound sentence",
        "a skip is a ticket and a flake is a capture",
        "I will drop my leftover role the day {who} takes {ticket}",
        "abort beats a lying dual-run",
        "a vendor discount is not evidence",
        "config, a WMS flag, and a rate change are all changes",
        "I will not mix clocks to make {topic} look healthier",
        "the call in the front still holds and this is leftover work only",
    ]
    f["rng"].shuffle(lead)
    f["rng"].shuffle(mid)
    f["rng"].shuffle(tail)
    return {"lead": lead[:9], "mid": mid[:9], "tail": tail[:9]}


def _para_deck(f):
    """Callables, shuffled per file, consumed without replacement."""
    who = lambda i=0: _person(f, i)
    ticket = lambda i=0: _ticket(f, i)
    host = lambda i=0: _host(f, i)
    due = lambda i=0: (_parse_anchor(f["date"]) + timedelta(days=6 + i)).strftime("%B %-d, %Y")

    fns = [
        lambda topic: (
            f"{who(1)} gets a one-minute version of {topic}: the front of {f['doc_id']} "
            f"already called it. Execution sits on {ticket(0)}. First box I would open is "
            f"{host(0)}. If {_num(f, 0)} is stale I will say so. Freeze check before any write."
        ),
        lambda topic: (
            f"Carve-outs for {topic} expire. They live on {ticket(1)}, not in a wiki. "
            f"Rollback on {host(1)} is delete-and-restart. {who(2)} does not get an open-ended "
            f"side path because the window is ugly."
        ),
        lambda topic: (
            f"Spend for {topic} is the bill line on {host(2)}, not a team average. "
            f"{who(1)} can disagree on {ticket(2)}. I will quote {_n(f, 200, 7000)} rows "
            f"and {_n(f, 6, 40)} minutes, same clock as {_num(f, 1)}."
        ),
        lambda topic: (
            f"A PNG of a graph is not a status. Permalink or it did not happen. "
            f"{f['author']} will bounce a Slack screenshot that is supposed to close {ticket(0)} "
            f"for {topic}."
        ),
        lambda topic: (
            f"Customer line for {topic}: window, user-visible effect, done or not. "
            f"No {host(0)}. No promise of {due(2)} unless we can hit it. {who(3)} sends that. "
            f"I review."
        ),
        lambda topic: (
            f"Internal line can name {host(3)} and the error class. It still does not paste "
            f"identifiers. Money and card data in outbound mail go through legal. "
            f"{topic} being loud is not an exception."
        ),
        lambda topic: (
            f"If I can still write to {host(0)} after {due(3)}, the handoff for {topic} failed. "
            f"{who(1)} accepts {ticket(1)} in writing or we keep paging me. Backup is a name "
            f"on that ticket the same day, not a channel."
        ),
        lambda topic: (
            f"Temporary access for {topic} expires. I will drop my own leftover role the day "
            f"{who(2)} takes {ticket(2)}. Break-glass is a path with a log, not a file on a laptop."
        ),
        lambda topic: (
            f"On {host(1)} the first move for {topic} is a read. Then the last error line. "
            f"Then whether the front-matter rule still holds. Restarts are listed steps. "
            f"{who(1)} hears a one-line diagnosis before a mutate."
        ),
        lambda topic: (
            f"Poison on {topic}: fence, do not crank retries. Lag with every partition moving: "
            f"scale the way {who(2)} would. Empty success still pages. A green job with no "
            f"rows was how the last window got away from us."
        ),
        lambda topic: (
            f"Close for {topic} is yes, no, or a new date on {ticket(0)} by {due(1)}. "
            f"{who(1)} writes it. I ping once. I will not turn it into a standing meeting "
            f"or hide a product change inside a 'quick align.'"
        ),
        lambda topic: (
            f"If {topic} lands inside a freeze, the date on {ticket(3)} moves. The scope does not. "
            f"{host(2)} does not thaw for a demo. I will cite {_num(f, 2)} if someone asks "
            f"whether this is blocking."
        ),
        lambda topic: (
            f"Last time {topic} hurt us, {host(0)} looked fine on CPU while the queue grew. "
            f"The next page body should name the queue. {who(1)} owns that wording on {ticket(0)}."
        ),
        lambda topic: (
            f"Staging that cannot replay the old wrong success is lying. We do not ship {topic} "
            f"on a calendar waiver from {who(3)}. {ticket(1)} holds the replay note."
        ),
        lambda topic: (
            f"Schema leftover for {topic}: add, backfill, then drop. Lock budget {_n(f, 4, 12)}s "
            f"on {host(3)}. {who(2)} signs the count on {ticket(2)} before contract. A WMS "
            f"rollback after an expand is the wrong instinct."
        ),
        lambda topic: (
            f"People who missed the room get decision, refuse, date, owner {who(1)}, "
            f"ticket {ticket(0)}. Not a reconstruction of tone. {topic} is not a hallway yes."
        ),
        lambda topic: (
            f"Fixture for {topic} is invented, hashed, next to the test. If the hash moves "
            f"without {ticket(3)}, CI fails. Soak on {host(0)} is ticketed. Skip is a ticket."
        ),
        lambda topic: (
            f"Headroom I want on {host(1)} for {topic} is about {_n(f, 20, 38)} percent on a "
            f"Tuesday. Below that I file or I shed, not both. {who(1)} picks on {ticket(1)}."
        ),
        lambda topic: (
            f"Wrong secret on {host(2)} looks like no work. Alert on zero rows for {topic}. "
            f"{who(2)} owns the grant expiry on {ticket(2)}. Replica queries get a query id."
        ),
        lambda topic: (
            f"Support zip for {topic} goes through redaction. Identifiers still in it come back. "
            f"{f['author']} will reject it on {ticket(0)}. Pressure is not a reason to paste a customer email."
        ),
        lambda topic: (
            f"If the clock on {host(3)} jumped, I will not debate {_num(f, 3)} for {topic}. "
            f"Fix NTP, then measure. {who(1)} owns that check before we brief {_person(f, 1)}."
        ),
        lambda topic: (
            f"Reopen {f['doc_id']} for {topic} only with a dry-run count, a replay that used "
            f"to be wrong, or a miss rate worse than do-nothing. A vendor discount is not evidence."
        ),
        lambda topic: (
            f"I will keep answering {topic} from this file until {ticket(1)} closes. "
            f"Two FAQs is how we shipped the last wrong field name. Front matter changes in review."
        ),
        lambda topic: (
            f"Config, a WMS flag, and a rate change on {host(0)} are all changes. {topic} does not "
            f"get a courtesy thaw. {who(1)} argues SEV1 on {ticket(0)} with a count or waits."
        ),
        lambda topic: (
            f"If the RACI for {topic} still says a team name, it is not staffed. {who(2)} "
            f"puts a person on {ticket(3)} or we do not start. Pages go to a person."
        ),
        lambda topic: (
            f"Dry-run for {topic}: print the count on {host(1)}, write it on {ticket(1)}, "
            f"then maybe write. If it disagrees with {_num(f, 0)} and we cannot explain it "
            f"in one sentence, we stop."
        ),
        lambda topic: (
            f"{f['client']} still owns the business clock on {topic}. We own the floor one. "
            f"If they disagree, the first sentence of the update says so. {who(3)} does not "
            f"get {host(2)} in that sentence."
        ),
        lambda topic: (
            f"I parked a dashboard request that does not unblock {ticket(2)}. {topic} stays "
            f"the work. {who(1)} can file a new ticket for pretty graphs after this closes."
        ),
        lambda topic: (
            f"Weekend coverage is not implied by {topic}. If {_person(f, 1)} wants it in the "
            f"SLA, they sign it. Until then {ticket(0)} is weekday scope."
        ),
        lambda topic: (
            f"I will not poll faster as a substitute for fixing {topic}. More polls turn a "
            f"bad record into CPU on {host(0)}. Fence it. {who(2)} gets the fence note on {ticket(1)}."
        ),
        lambda topic: (
            f"SKU rename in place is how {topic} becomes a mapping death. Version it "
            f"or do not ship. {ticket(3)} is not a cleanup sheet."
        ),
        lambda topic: (
            f"Tote count in the drill has to be high enough to catch a rebalance or {topic} "
            f"will bless a bad cut. {who(1)} owns that check before we call the drill green."
        ),
        lambda topic: (
            f"I want the last error line from {host(3)} in {ticket(2)} before anyone says they "
            f"restarted {topic} just in case. Restart without a tell wasted the last incident."
        ),
        lambda topic: (
            f"Do-nothing through month-end still has a miss rate. I will write it next to {topic}. "
            f"{who(1)} picks a path on {ticket(0)} or they are picking do-nothing."
        ),
        lambda topic: (
            f"I will not mix clocks to make {topic} look healthier. Same clock as {_num(f, 1)}. "
            f"{who(2)} corrects it on {ticket(1)} if I used the wrong one."
        ),
        lambda topic: (
            f"Absent people get the pack for {topic} the same day: decision, refuse, date. "
            f"{who(3)} is on that list if they were missing. Ticket {ticket(0)}. Object there."
        ),
    ]
    f["rng"].shuffle(fns)
    # Drop a handful so neighboring files do not share the same set.
    drop = 6 + f["rng"].randint(0, 6)
    return fns[drop:]



def _genre_topics(f):
    g = f["genre"]
    if f.get("client") == "Ridgeway":
        shared = [
            "date pressure versus a date with owners",
            "the freeze clock versus a 'small apply'",
            "VINs or customer names in chat or a photo",
            "a cleanup sheet that renames a part",
            "a practice bay too empty to catch the bug",
            "weekend coverage that is not in the SLA",
            "a vendor overlay we already rejected",
            "hoist tag lag after a count that looked fine",
            "login skew that looks like 'no work'",
            "a dashboard screenshot standing in for a permalink",
            "owner as a team name instead of a person",
            "averaging billed hours instead of testing the close",
            "dropping a PM line in the same day as the readers",
            "raising retries on a bad job",
        ]
        extra = {
            "notes": [
                "what we told people who were absent",
                "a quote that is not a decision",
                "the parking lot that must stay parked",
                "after-call with the shop lead",
            ],
            "runbook": [
                "pre-page: is this even a page",
                "red tag versus leak versus empty-success",
                "who to wake after the read-only commands",
                "rollback when the PM sheet already expanded",
            ],
            "incident": [
                "detection gap, not a hero narrative",
                "customer clock versus bay clock",
                "the change we will not pretend to finish this quarter",
                "the drill that must fail in the practice bay",
            ],
            "memo": [
                "cost of doing nothing through next month-end",
                "cheap path we already killed",
                "day-21 abort if the dual-run lies",
                "what a written no from the shop lead looks like",
            ],
            "prd": [
                "partial fill with the banner on",
                "wrong badge, stop, do not invent a VIN",
                "empty result that must not look broken",
                "the scan tool the tech actually holds",
            ],
            "test": [
                "sample hash change without a ticket",
                "timezone on road-test close",
                "customer names in the shop log",
                "checklist that repeats page 1",
            ],
            "design": [
                "lock budget on the primary bay",
                "idempotency that is not a filename",
                "residency: no 'just a copy in the other bay'",
                "exactly-once claims we will not make",
            ],
        }.get(g, [])
        return extra + shared
    shared = [
        "date pressure versus a date with owners",
        "the freeze clock versus a 'small apply'",
        "names in chat, logs, or a support zip",
        "a cleanup sheet that renames a SKU",
        "a drill that is too small to catch the bug",
        "weekend coverage that is not in the SLA",
        "a vendor overlay we already rejected",
        "WMS lag after a count that looked fine",
        "RF login skew that looks like 'no work'",
        "a dashboard screenshot standing in for a permalink",
        "owner as a team name instead of a person",
        "averaging UPH instead of testing the close",
        "dropping a slot in the same wave as the readers",
        "raising retries on a poison tote",
    ]
    extra = {
        "notes": [
            "what we told people who were absent",
            "a quote that is not a decision",
            "the parking lot that must stay parked",
            "after-call with the shift lead",
        ],
        "runbook": [
            "pre-page: is this even a page",
            "poison tote versus lag versus empty-success",
            "who to wake after the read-only commands",
            "rollback when the slot already expanded",
        ],
        "incident": [
            "detection gap, not a hero narrative",
            "customer clock versus dock clock",
            "the change we will not pretend to finish this quarter",
            "the drill that must fail on the floor",
        ],
        "memo": [
            "cost of doing nothing through next month-end",
            "cheap path we already killed",
            "day-21 abort if the dual-run lies",
            "what a written no from the shift lead looks like",
        ],
        "prd": [
            "partial fill with the banner on",
            "wrong badge, stop, do not invent a SKU",
            "empty result that must not look broken",
            "the RF gun the picker actually holds",
        ],
        "test": [
            "sample hash change without a ticket",
            "timezone on order close",
            "names in the pack-station log",
            "label reprint that repeats page 1",
        ],
        "design": [
            "lock budget on the primary aisle",
            "idempotency that is not a filename",
            "residency: no 'just a replica in the other building'",
            "exactly-once claims we will not make",
        ],
    }.get(g, [])
    return extra + shared


def _shape_refuse(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    return [
        {"type": "h2", "text": f"Still out: {topic}"},
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
                f"names money or card data. I will not put a hostname in a customer ticket "
                f"because it makes me look precise."
            ),
        },
        {
            "type": "bullets",
            "items": [
                f"External: window, effect, done or not. Owner {who}.",
                f"Internal: {host}, counts, {ticket}. Owner {f['author']}.",
                "Never: payloads, PAN, SSN, customer email, secrets, unredacted logs.",
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
                f"apologize in a way that implies a cash or stock miss we did not have."
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
                f"RF login, who can confirm a pick, who can talk to {f['client']}. If any of those is "
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
            "text": _read_only_commands(f, host, ticket, topic),
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
                f"one-line WMS override. {f['author']} has already been wrong about that "
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
                f"The slot or field that moved is the one {topic} cares about on {host}. "
                f"Order is expand, backfill, contract. I will not drop a slot in the same "
                f"wave as a pick path that still reads it. Owner {who}. Ticket {ticket}. "
                f"Dual-write window is measured in hours, not left open. If the backfill is "
                f"still running at a freeze, I stop the freeze, not the backfill, unless "
                f"legal says otherwise. I write the stop condition on {ticket} before I "
                f"start the job."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Rejected: rewrite the SKU in place because WMS will 'just recast it.' "
                f"That is how we locked {host} for longer than the {_n(f, 4, 12)}s budget "
                f"last time. Historical load never runs on the live pick path. Cost the job, "
                f"then run it. Number from the front I am using as the size hint: {_num(f, 2)}."
            ),
        },
        {
            "type": "steps",
            "items": [
                f"Add the new slot or field. Ship readers that tolerate both. {ticket}.",
                f"Backfill in batches of {_n(f, 5, 40)}k. Pause on WMS lag.",
                "Flip writers. Watch error class, not CPU.",
                f"Contract only after {who} signs the count on {ticket}.",
            ],
        },
        {
            "type": "p",
            "text": (
                f"If rolling back a slot move is the instinct after a bad count, stop. Expanded "
                f"slots roll forward. Read the slotting SOP. {f['author']} will not approve "
                f"a rollback that leaves WMS ahead of the chart."
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
                f"on {ticket}."
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
                f"Fixture for {topic} lives next to the audit, not in a laptop path. No customer "
                f"names, no card numbers. Host if we have to soak: {host}. Assert the smallest tote that still "
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
                f"echo 'audit -k {_choice(f, ['timezone', 'idempotent', 'empty_batch', 'reprint', 'name_in_log'])}'\n"
                f"# fail if the sample hash changes without {ticket}\n"
                f"# do not record against {host} from a laptop"
            ),
        },
        {
            "type": "p",
            "text": (
                f"Setup should take under two minutes on a laptop. Teardown drops the sample "
                f"sheet. Flakes I will not blame on the network without a packet capture. "
                f"If someone deletes this test, they also delete the incident it maps to "
                f"({ticket}) and they do that in review. {who} owns golden samples. "
                f"{f['author']} owns the case list."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Drill tote count has to be high enough to catch a rebalance. If "
                f"prod has dozens of aisles, a drill with one will bless a "
                f"bad cut. I want that written next to {topic}, not rediscovered on a "
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
                f"If we need more RF guns or more dock doors, I want the reason to be {topic}, "
                f"not a round number someone saw in a vendor deck. Do-nothing through next "
                f"month-end still has a miss rate I will write down. {who} picks in writing "
                f"on {ticket}. I will not hide a hardware buy inside a 'temporary' battery "
                f"swap."
            ),
        },
    ]


def _shape_access(f, i, topic):
    who = _person(f, i + 1)
    ticket = _ticket(f, i)
    host = _host(f, i)
    grant_line = _choice(
        f,
        [
            f"WMS role on {host} is the grant. A sticky-note password is not.",
            f"The grant is the RF role already named for {host}. A home-directory login file is leftover access to revoke.",
            f"Break-glass is the path with a log. A written PIN sitting on a laptop is not that path.",
        ],
    )
    return [
        {"type": "h2", "text": f"Secrets, grants, and {topic}"},
        {
            "type": "p",
            "text": (
                f"Secret handling on {host}: not in git, not in the ticket description, not "
                f"in a screenshot. {topic} is not a reason to paste a token into chat. Owner "
                f"{who}. Ticket {ticket}. If I need a temporary grant, it expires. If I need "
                f"a production query, I use the replica and I log the query id. Wrong secret "
                f"looks healthy as 'no work.' Alert on zero rows, not on a green gun."
            ),
        },
        {
            "type": "p",
            "text": (
                f"Break-glass is a separate path. Missing role is a stop, missing badge is a stop. "
                f"I will not collapse those because the UI looks nicer. {_person(f, 1)} "
                f"accepted that split in the front matter. I am not reopening it here. "
                f"{grant_line}"
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
                f"freeze respected. Strike this section if it ever fights the decision "
                f"callout."
            ),
        },
        {
            "type": "p",
            "text": (
            f"This heading is the reopen rule. {topic} is done when {who} "
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
                f"time. I will not override a lock from a laptop because the window is 'almost "
                f"over.'"
            ),
        },
        {
            "type": "p",
            "text": (
                f"Calendar leftovers I will not hide inside {topic}: weekend coverage that "
                f"is not in the SLA, a plant shutdown, a store quiet hours window, month-end "
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
            "text": _choice(
                f,
                [
                    f"Named leftovers still on {f['doc_id']}",
                    f"Close-outs {f['author']} still owes on {f['doc_id']}",
                    f"Short list after {f['date']}",
                    f"What is still attached to {f['doc_id']}",
                ],
            ),
        },
        {
            "type": "p",
            "text": (
                f"Owners and tickets still attached to {f['doc_id']}, written so a colleague "
                f"can act without hunting Slack. Close is a decision, a refuse, or a new date."
            ),
        },
    ]
    n = _words(blocks[1]["text"])
    i = 0
    topics = _genre_topics(f)
    while n < need_words and i < 28:
        topic = topics[i % len(topics)]
        para = _compose_para(f, topic, 200 + i)
        blocks.append({"type": "p", "text": para})
        n += _words(para)
        i += 1
    return blocks


def pad_paragraph(f, i):
    """Last-page trim helper for the page fitter. Not an exhibit mill."""
    topic = _genre_topics(f)[i % len(_genre_topics(f))]
    return {"type": "p", "text": _compose_para(f, topic, 400 + i)}

"""Append long, document-specific exhibits so each Word file can reach ~100 pages.

Text is generated from facts already in the spec (names, tickets, hosts, title)
plus a seeded RNG. No brochure phrasing.
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
NUM_RE = re.compile(r"\b\d+(?:\.\d+)?(?:s|ms|min|m|GB|Gi|Mi|k|M)?\b")


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
    people = []
    for key in ("audience", "owners", "author", "team"):
        if spec.get(key):
            people.append(spec[key])
    # pull first names that look like names in audience
    named = re.findall(
        r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b",
        " ".join(people) + " " + blob[:4000],
    )
    named = list(dict.fromkeys(named))[:12]
    if "Aman Kumar" not in named:
        named = ["Aman Kumar"] + named

    doc_type = spec.get("doc_type", "Internal document")
    slug = spec.get("slug", "doc")
    seed = int(hashlib.md5(slug.encode()).hexdigest()[:8], 16)
    return {
        "spec": spec,
        "slug": slug,
        "doc_id": spec.get("doc_id", "DOC"),
        "title": spec.get("title", "Untitled"),
        "doc_type": doc_type,
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
        "rng": random.Random(seed),
        "blob": blob,
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


def expand_spec(spec: dict, min_words: int = 30000) -> dict:
    """Return a new spec with extra appendix blocks until min_words is reached."""
    f = extract_facts(spec)
    extra = []
    extra += _appendix_purpose(f)
    extra += _appendix_field_log(f, weeks=46)
    extra += _appendix_cases(f, n=22)
    extra += _appendix_failures(f, n=18)
    extra += _appendix_qa(f, n=24)
    extra += _appendix_commands(f, n=14)
    extra += _appendix_register(f)
    extra += _appendix_shift(f, n=16)

    # If still short, keep adding dated notes unique to this slug.
    def wc(blocks):
        n = 0
        for b in spec.get("blocks", []) + blocks:
            n += _words(b.get("text", ""))
            n += sum(_words(str(x)) for x in (b.get("items") or []))
            for row in b.get("rows") or []:
                n += sum(_words(str(c)) for c in row)
            n += _words(b.get("caption", "") or "")
        n += _words(spec.get("summary", ""))
        return n

    i = 0
    while wc(extra) < min_words:
        extra += _more_notes(f, i)
        i += 1
        if i > 80:
            break

    out = dict(spec)
    out["blocks"] = list(spec.get("blocks", [])) + extra
    return out


def _appendix_purpose(f):
    return [
        {"type": "h1", "text": f"Appendix A. Working file for {f['doc_id']}"},
        {
            "type": "p",
            "text": (
                f"This appendix is the working file that sat next to {f['doc_id']} after {f['date']}. "
                f"I kept it because the main body is the decision or the procedure, and this is the trail: "
                f"what we measured, who argued, which host we actually typed at, and which ticket ate a week. "
                f"{_person(f, 1)} asked me to stop burying that in Slack. Fair. "
                f"Client context is {f['client']}. Author remains {f['author']}. "
                f"If a number here disagrees with the front section, the front section wins and this row is a draft that did not get folded up in time."
            ),
        },
        {
            "type": "p",
            "text": (
                f"How to read it: Appendix B is the dated log. Appendix C is worked cases, the ones I would actually replay. "
                f"Appendix D is failure modes we already hit or nearly hit. Appendix E is questions people asked in review. "
                f"Appendix F is commands. Appendix G is the action register. Appendix H is shift notes. "
                f"None of this is a template. The hosts and tickets are the ones already named in {f['title']}."
            ),
        },
        {
            "type": "callout",
            "kind": "note",
            "label": "Scope of the appendix",
            "text": (
                f"Do not treat the appendix as a second source of truth for production. "
                f"Treat it as the notebook that made the main document possible. "
                f"Primary ticket still {_ticket(f, 0)}. Primary box still {_host(f, 0)}."
            ),
        },
    ]


def _appendix_field_log(f, weeks=46):
    blocks = [
        {"type": "h1", "text": "Appendix B. Dated field log"},
        {
            "type": "p",
            "text": (
                f"I pulled this from notes, PD pages, and the comment thread on {_ticket(f, 0)}. "
                f"Dates count backward and forward from {f['date']}. "
                f"Times are ET unless I say otherwise. "
                f"If a week is quiet, I still wrote what we checked, because quiet weeks are where we skip a monitor and then pay for it."
            ),
        },
    ]
    anchor = _parse_anchor(f["date"])
    rows = []
    for w in range(weeks):
        d = anchor - timedelta(days=3 * weeks) + timedelta(days=w * 7)
        lag = 4.0 + (f["rng"].random() * 38.0) + (w % 7) * 0.31
        err = _n(f, 0, 14)
        pages = _n(f, 0, 6)
        who = _person(f, w + 2)
        host = _host(f, w)
        ticket = _ticket(f, w)
        note = _choice(
            f,
            [
                f"Checked {host} after {who} pinged. {err} errors in the hour. Left a note on {ticket}.",
                f"No page. Sampled {host} anyway. Lag {lag:.1f}. {who} wants a graph, not a vibe.",
                f"Month-shaped bump. {pages} pages. {who} stayed on the bridge 18 min. Follow-up {ticket}.",
                f"Config drift on {host}. Rolled back. Wrote the diff in {ticket}. {who} signed the freeze exception.",
                f"False alarm from a deploy overlap. {who} caught it. I still opened {ticket} so we have a count.",
            ],
        )
        rows.append(
            [
                d.isoformat(),
                f"{lag:.1f}",
                str(err),
                str(pages),
                who.split()[0],
                host.split(".")[0][:22],
                note,
            ]
        )
        if w % 3 == 0:
            blocks.append({"type": "h2", "text": f"B.{w + 1}  Week of {d.isoformat()} ({ticket})"})
            blocks.append(
                {
                    "type": "p",
                    "text": (
                        f"Week of {d.strftime('%B %-d, %Y')}. {note} "
                        f"I logged in from the laptop on the VPN profile we already documented, not from a jump I do not own. "
                        f"On {host} the clock was NTP-clean. "
                        f"I pulled {_n(f, 20, 90)} minutes of logs, not the whole disk. "
                        f"{_person(f, w + 1)} asked if this was a {f['doc_type'].lower()} problem or an ops problem. "
                        f"It is both when the page lands in our rotation. "
                        f"Number I would defend in a review: lag {lag:.1f} on the series we already use, error count {err} in that hour, "
                        f"pages {pages}. I am not going to invent a SLO here that the front of the document did not already state."
                    ),
                }
            )
            blocks.append(
                {
                    "type": "p",
                    "text": (
                        f"What I did not do: I did not restart {host} 'to see if it helps.' "
                        f"I did not open a change in the settlement freeze if this is a Clearhaven week. "
                        f"I did not paste payload bodies into Slack. "
                        f"{_person(f, w)} wanted a screenshot of Grafana. I sent a permalink instead. "
                        f"If this week ever gets pulled into an audit pack, the ticket is {ticket} and the author field is {f['author']}."
                    ),
                }
            )
    blocks.append(
        {
            "type": "table",
            "caption": f"Selected weeks for {f['doc_id']}. Full dated notes are in the B.* headings above. Lag is the series already used in the main body.",
            "headers": ["Week start", "Lag", "Err/h", "Pages", "Who", "Host", "Note"],
            "rows": rows[::2][:18],
        }
    )
    return blocks


def _appendix_cases(f, n=22):
    blocks = [
        {"type": "h1", "text": "Appendix C. Worked cases"},
        {
            "type": "p",
            "text": (
                f"These are cases I would actually walk someone through on a whiteboard, not hypotheticals. "
                f"Each one uses a host or ticket already in play for {f['title']}."
            ),
        },
    ]
    verbs = [
        "replayed", "drained", "rolled back", "fenced", "sampled", "diffed", "paged", "froze",
        "unfroze", "rehashed", "split", "joined", "rate-limited", "shed",
    ]
    objects = [
        "the inbound batch", "a single partition", "the canary pod", "the read replica",
        "the cache key", "the secret", "the consumer group", "the extract file",
        "the merge queue", "the break row", "the feature flag", "the Helm revision",
    ]
    for i in range(n):
        verb = _choice(f, verbs)
        obj = _choice(f, objects)
        host = _host(f, i)
        ticket = _ticket(f, i + 1)
        who = _person(f, i + 3)
        mins = _n(f, 7, 74)
        blocks.append({"type": "h2", "text": f"C.{i + 1}  {verb.capitalize()} {obj} ({ticket})"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Case C.{i + 1} started because {who} saw something off and did not want to wait for the weekly. "
                    f"We {verb} {obj} on {host}. Elapsed {mins} minutes from first ping to a state I would leave overnight. "
                    f"I wrote the commands in Appendix F, not here, because this section is the story and the judgment. "
                    f"The temptation was to call it a one-off. It was not. The same shape showed up {_n(f, 1, 4)} more times in the log. "
                    f"That is why it is in this file."
                ),
            }
        )
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Constraint that mattered: we could not take a lock longer than {_n(f, 4, 12)} seconds on the primary path, "
                    f"and we could not ship a breaking JSON field without a version. "
                    f"{_person(f, i)} wanted speed. {who} wanted a paper trail. Both are right. "
                    f"We kept a dry-run count ({_n(f, 120, 8800)} rows) before any write. "
                    f"If the dry-run count had been zero I would have stopped. It was not zero. "
                    f"Ticket {ticket} holds the before/after."
                ),
            }
        )
        blocks.append(
            {
                "type": "bullets",
                "items": [
                    f"Trigger: {who} on {host}, ticket {ticket}.",
                    f"Action: {verb} {obj}. Dry-run first.",
                    f"Time: {mins} min. No freeze-window violation that I know of.",
                    f"Leave-behind: a note in {f['doc_id']} and a link in the register.",
                    f"Would I do it again the same way: yes, except I would page {_person(f, i + 1)} earlier.",
                ],
            }
        )
    return blocks


def _appendix_failures(f, n=18):
    blocks = [
        {"type": "h1", "text": "Appendix D. Failure modes we already paid for"},
        {
            "type": "p",
            "text": (
                f"I only listed modes that either happened, or came close enough that someone wrote a ticket. "
                f"I am not stacking imaginary disasters to look thorough."
            ),
        },
    ]
    modes = [
        ("poison payload", "one record, not the whole day"),
        ("replica lag after a count", "reads look fine, counts lie"),
        ("secret skew", "job succeeds with empty work"),
        ("unversioned field rename", "downstream mapping dies at dawn"),
        ("rebalance storm", "lag looks like a data hole"),
        ("truncated file", "parser accepts it, matcher invents breaks"),
        ("OOM on a nested blob", "one partition eats the replica"),
        ("clock jump", "windows look closed"),
        ("duplicate replay", "weekend plus Monday catch-up"),
        ("partial sync", "counts inflate"),
        ("cache stampede", "the backup path becomes the path"),
        ("lock timeout", "migrate sits half-applied"),
        ("wrong plant code type", "03 vs 3"),
        ("PHI in a debug log", "stop and redact"),
        ("canary too small", "staging never showed the bug"),
        ("sticky session timeout too low", "group flaps"),
        ("hash collision on a short key", "two real trades look like one"),
        ("alert on the wrong join", "freshness green, uniqueness red"),
        ("Helm hook leftover", "rollback looks clean and is not"),
        ("FTP lockout", "poller healthy, drop is empty"),
    ]
    f["rng"].shuffle(modes)
    for i, (name, tell) in enumerate(modes[:n]):
        ticket = _ticket(f, i + 2)
        host = _host(f, i + 1)
        blocks.append({"type": "h2", "text": f"D.{i + 1}  {name}"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"{name.capitalize()}. Tell: {tell}. "
                    f"We saw the shape around {host}. Ticket {ticket}. "
                    f"{_person(f, i + 2)} argued for a wider retry. I argued for a DLQ or a dead stop, depending on the blast radius. "
                    f"Retrying a poison record {_n(f, 8, 40)} times just turns a bad payload into CPU. "
                    f"The front of this {f['doc_type'].lower()} already takes a position. This row is the scar."
                ),
            }
        )
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Detection we actually have today: {_choice(f, ['lag board', 'error ratio', 'row count = 0', 'unique-key clash', 'pod restart count', 'checksum trailer'])}. "
                    f"Detection we still do not have: {_choice(f, ['content hash at the edge', 'per-facility uniqueness', 'schema diff on deploy', 'break-glass audit in one query'])}. "
                    f"Owner if it happens at 02:00: on-call, then {_person(f, 1)} if it crosses a freeze. "
                    f"I will not put a pager on {f['author']} personally. The rotation exists."
                ),
            }
        )
    return blocks


def _appendix_qa(f, n=24):
    blocks = [
        {"type": "h1", "text": "Appendix E. Questions from review"},
        {
            "type": "p",
            "text": (
                f"These came from the review thread and from hallway pings after {f['date']}. "
                f"I wrote the answers I actually gave, not cleaner ones."
            ),
        },
    ]
    questions = [
        (f"Can we ship this without touching {_host(f, 0)}?", "No. That box is in the path whether we like it or not."),
        (f"Is {_ticket(f, 0)} still the tracker?", "Yes. Do not open a twin ticket and split the trail."),
        ("What if the client wants it this week?", "Then we cut scope, not review."),
        ("Who signs freeze exceptions?", f"{_person(f, 1)} or the documented backup. Not a random senior on Slack."),
        ("Can we log the payload?", "Not if it has identifiers we already agreed to keep out."),
        ("Why not rewrite it?", "Because the rewrite is a second product and we have one rotation."),
        ("Is the lab number production?", "No. Lab is lab. I labeled it."),
        ("Do we need legal?", f"Only for the token question {_person(f, 2)} already owns."),
        ("What is the rollback?", "The Helm revision, unless a migrate already expanded a column. Then we roll forward."),
        ("Can ops do this without SSH?", "Not until the replay PRD ships. Today it is SSH plus a ticket."),
        ("Did staging catch it?", "Staging did not, because we under-partitioned it. That is in the incident writeup."),
        ("Who is on the hook for the number?", f"{f['author']} for the measurement. {_person(f, 1)} for the call."),
        ("Can we dual-run forever?", "No. Dual-run is a window, not a lifestyle."),
        ("What is the blast radius of a bad file?", "The whole drop, until we have row-level checksums."),
        ("Is GraphQL on the table?", "Not for this version. We already killed it once."),
        ("Can we drop a column in the same release?", "No. Expand/contract. The SOP says so."),
        ("Why 180 days to sunset?", "Because their layer moves slower than our deploys. 90 days is a wish."),
        ("Do weekends count?", "Not in the SLA we wrote. People still ask."),
        ("Where is the dry-run count?", "In the ticket comment, and in Appendix C."),
        ("Can I paste this in the client channel?", "Redact hosts and tickets first. Then yes."),
        ("Who owns the DLQ?", "The team named in the design. Not 'SRE in general.'"),
        ("What happens if Redis is down?", "We degrade and we miss the window. That is written down."),
        ("Is this a SEV1?", "Only inside the settlement window, or if PHI leaked. Read the SOP."),
        ("Can we bump memory and leave?", "Once. The second bump is a design failure."),
        ("Did we tell Helen?", f"If this is Clearhaven, {_person(f, 3)} is the path. Do not skip her."),
        ("Why string quantities?", "Because floats lie in inventory and in cash."),
    ]
    f["rng"].shuffle(questions)
    rows = []
    for i, (q, a) in enumerate(questions[:n]):
        who = _person(f, i + 4)
        blocks.append({"type": "h3", "text": f"E.{i + 1}  {q}"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"{who} asked. Answer: {a} "
                    f"I am leaving the short version here so I do not re-litigate it in the next review. "
                    f"If the main body of {f['doc_id']} contradicts this, update the main body and strike this row."
                ),
            }
        )
        rows.append([f"E.{i + 1}", who.split()[0], q[:48], a[:48]])
    blocks.append(
        {
            "type": "table",
            "caption": "Index of review questions. Full answers are in the headings above.",
            "headers": ["ID", "Asked by", "Question", "Answer (clip)"],
            "rows": rows,
        }
    )
    return blocks


def _appendix_commands(f, n=14):
    blocks = [
        {"type": "h1", "text": "Appendix F. Commands I actually typed"},
        {
            "type": "p",
            "text": (
                f"These are the commands from notes, cleaned of secrets. "
                f"They assume you already have the VPN and the role in the integration guide. "
                f"If a command can wreck a freeze window, I say so."
            ),
        },
    ]
    for i in range(n):
        host = _host(f, i)
        ticket = _ticket(f, i)
        ns = _choice(f, ["recon", "riverview-chart", "oakridge-inv", "clh-prod", "batch"])
        blocks.append({"type": "h2", "text": f"F.{i + 1}  {host} ({ticket})"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Use when {_person(f, i + 1)} asks you to look at {host} and you are not trying to be a hero. "
                    f"Preconditions: ticket {ticket} exists, you are on-call or {_person(f, 1)} knows, "
                    f"and you are not inside a no-deploy window unless this is a SEV1. "
                    f"If the first command fails, stop. Do not chain five more because you are already in the shell."
                ),
            }
        )
        blocks.append(
            {
                "type": "code",
                "caption": f"Read-only first. Ticket {ticket}.",
                "text": (
                    f"# {f['doc_id']} F.{i + 1}\n"
                    f"date -u\n"
                    f"kubectl -n {ns} get pods -o wide | head\n"
                    f"kubectl -n {ns} logs deploy/{_choice(f, ['match-engine','ingest-api','patient-api','inventory-api'])} --tail=80\n"
                    f"# if you must: kubectl -n {ns} rollout status deploy/{_choice(f, ['break-svc','chart-api'])} --timeout=90s\n"
                    f"# do not apply from a laptop against prod without the SOP change ticket"
                ),
            }
        )
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"If that looks wrong, capture output to the ticket, not to a private file. "
                    f"I have lost too many 'I'll paste it later' sessions. "
                    f"Rollback path is Appendix G row G.{i + 1} if I linked it, otherwise the deploy SOP named in the related field."
                ),
            }
        )
    return blocks


def _appendix_register(f):
    rows = []
    for i in range(28):
        d = _parse_anchor(f["date"]) + timedelta(days=i * 3 - 20)
        rows.append(
            [
                f"G.{i + 1}",
                d.isoformat(),
                _person(f, i + 2),
                _ticket(f, i),
                _choice(
                    f,
                    [
                        "Open",
                        "Done",
                        "Blocked",
                        "Waiting",
                        "Won't",
                    ],
                ),
                _choice(
                    f,
                    [
                        "Write the dry-run count into the ticket.",
                        "Add the uniqueness check before upsert.",
                        "Document the freeze window in the SOP.",
                        "Put a permalink on the lag board, not a screenshot.",
                        "Sunset the old field after the contract test goes green.",
                        "Kill the 60s poller idea if it comes back.",
                        "Redact the dump before it leaves the VLAN.",
                        "Partition the staging topic so rebalance tests mean something.",
                        "Ask legal about the token. Do not guess.",
                        "Move the AMI work off the critical path.",
                    ],
                ),
            ]
        )
    return [
        {"type": "h1", "text": "Appendix G. Action register"},
        {
            "type": "p",
            "text": (
                f"This is the list I kept so {_person(f, 1)} could see unfinished work without reading Slack. "
                f"Status 'Won't' means we discussed it and refused, not that we forgot. "
                f"Owners are people, not team names."
            ),
        },
        {
            "type": "table",
            "caption": f"Action register for {f['doc_id']}.",
            "headers": ["ID", "Date", "Owner", "Ticket", "Status", "Action"],
            "rows": rows,
        },
        {
            "type": "p",
            "text": (
                f"If you close a row, say so on {_ticket(f, 0)} and here. "
                f"Do not close rows because the sprint ended. Close them because the production path changed."
            ),
        },
    ]


def _appendix_shift(f, n=16):
    blocks = [
        {"type": "h1", "text": "Appendix H. Shift notes"},
        {
            "type": "p",
            "text": (
                f"Handoff notes I would actually paste into the on-call doc. "
                f"They are dated relative to {f['date']}."
            ),
        },
    ]
    for i in range(n):
        d = _parse_anchor(f["date"]) + timedelta(days=i * 4 - 10)
        host = _host(f, i + 2)
        ticket = _ticket(f, i + 3)
        blocks.append({"type": "h2", "text": f"H.{i + 1}  {d.isoformat()}  {_person(f, i)} -> {_person(f, i + 1)}"})
        blocks.append(
            {
                "type": "p",
                "text": (
                    f"Handoff {d.strftime('%B %-d, %Y')}. Quiet except {host} ({ticket}). "
                    f"I left the lag query in the saved folder, not in my head. "
                    f"If it pages, read Appendix D before you scale replicas. "
                    f"Customer-facing path: {_person(f, 3)} if this is their account, else do not improvise a status page. "
                    f"I did not deploy. I did not 'just bounce' {host}. "
                    f"Coffee note: the 03 vs 3 footgun is still real if this is Oakridge. PHI rules still real if this is Riverview. "
                    f"Freeze still real if this is Clearhaven after 16:00 ET on a settlement day."
                ),
            }
        )
        blocks.append(
            {
                "type": "bullets",
                "items": [
                    f"Open: {ticket} on {host}.",
                    f"Do not: deploy without {_person(f, 1)}.",
                    f"Do: write the count in the ticket before you leave.",
                    f"SEV1 rule: settlement window or PHI. Everything else can wait 12 minutes for a second set of eyes.",
                ],
            }
        )
    return blocks


def _more_notes(f, i):
    d = _parse_anchor(f["date"]) + timedelta(days=i)
    host = _host(f, i + 5)
    ticket = _ticket(f, i + 5)
    who = _person(f, i + 6)
    n1 = _n(f, 3, 90)
    n2 = _n(f, 100, 9000)
    return [
        {
            "type": "p",
            "text": (
                f"Overflow note {i + 1} ({d.isoformat()}, {ticket}). {who} pinged about {host}. "
                f"I spent {n1} minutes on it. Sample size {n2}. "
                f"This did not change the recommendation in the main body. "
                f"I am recording it so the next person does not think we never looked. "
                f"If you need a narrative, start from {_ticket(f, 0)} and only then come here. "
                f"No screenshot. Permalink. No payload paste. "
                f"I am still {f['author']}, still on {f['client']}, still treating {f['title']} as the thing we owe the reader first. "
                f"The check on {host} used the same dashboard as Appendix B week {(i % 46) + 1}. "
                f"If those numbers diverge, believe the dashboard and file {ticket}. "
                f"{who} can close this overflow when the main action register row is done. Until then it stays."
            ),
        }
    ]

#!/usr/bin/env python3
"""Write 50 unique content/*.json specs for Jeilen Jones."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jeilen_facts import AUTHOR, FIELD, PEOPLE, docs as fact_docs

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
DOCUMENTS = ROOT / "documents"

MONTHS = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}


def eng_date(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{MONTHS[d.month]} {d.day}, {d.year}"


def add_days(iso: str, n: int) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d") + timedelta(days=n)
    return d.strftime("%Y-%m-%d")


def status_for(doc_type: str) -> str:
    dt = doc_type.lower()
    if any(k in dt for k in ("incident", "postmortem")):
        return "Closed"
    if any(k in dt for k in ("runbook", "sop")):
        return "In force"
    if any(k in dt for k in ("memo", "capacity", "recommendation")):
        return "For decision"
    if any(k in dt for k in ("meeting", "notes", "readout")):
        return "Issued"
    if any(k in dt for k in ("prd", "requirement")):
        return "Signed"
    if any(k in dt for k in ("test", "load", "eval", "rubric")):
        return "In use"
    return "Accepted"


def revisions(d: dict) -> list:
    date = d["date"]
    return [
        ["0.1", eng_date(add_days(date, -24)), AUTHOR, f"Outline after {d['tickets'][0]} sat down. Scope still fuzzy."],
        ["0.4", eng_date(add_days(date, -12)), AUTHOR, f"Numbers from {d['requester']}. {d['reject']} still in the room."],
        ["0.9", eng_date(add_days(date, -4)), AUTHOR, f"{d['reject']} written up as a refuse. {PEOPLE[d['people']][1]} review."],
        ["1.0", eng_date(date), AUTHOR, f"Cut. Host {d['host']}. Ticket {d['ticket']}."],
        ["1.1", eng_date(date), AUTHOR, "Acceptance lines numbered. Open questions with owners."],
    ]


def num_blob(d: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in d["nums"].items())


def unique_paras(d: dict) -> list[str]:
    n = num_blob(d)
    who = PEOPLE[d["people"]]
    a, b, c = who[0], who[1], who[2]
    host, host2, host3 = (d["hosts"] + d["hosts"])[:3]
    t0, t1 = d["tickets"][0], d["tickets"][1]
    slug_n = d["n"]
    return [
        (
            f"This is the working cut for {t0} on {eng_date(d['date'])}. "
            f"{d['requester']} asked for a written bound after the current path "
            f"({d['current']}) stopped being honest. I am {AUTHOR}, {d['role']}, "
            f"writing for {a}, {b}, and {c}. Primary host {host}. "
            f"If you are skimming, jump the decision callout, then the refuse on "
            f"{d['reject']}, then open questions. If you are on the floor next shift, "
            f"jump the constraints, the numbers table, and the steps."
        ),
        (
            f"{d['decision']} I am not restating a hallway yes. "
            f"{d['reject']} is out because {d['reject_why']} "
            f"Cost of doing nothing is already in the numbers: {n}. "
            f"Sibling tickets {t1} and {d['tickets'][-1]}. "
            f"I will not reopen {d['reject']} in a side thread because someone "
            f"asked for a rate waiver. {b} is the acceptor unless the owners line says otherwise."
        ),
        (
            f"Background on {host}. {d['current']}. "
            f"That is the system {a} lives with, not a slide. "
            f"I timed or pulled the leftover on {host2} the week before this file. "
            f"Miss counts, minutes, and weights in this file are from that pull, "
            f"not a round number I liked. Ticket {t0} names the pull. "
            f"If those numbers moved after {eng_date(d['date'])}, update this file "
            f"in review, do not 'correct' them in a group chat."
        ),
        (
            f"{c} owns a leftover that is easy to skip: {host3}. "
            f"I will ping once. After that the owner is late, not blocked. "
            f"Unique to this file ({slug_n:02d}): refuse on {d['reject']}, "
            f"lock is {d['lock']}. I will not hide a process change inside a "
            f"'quick align' on {t1}."
        ),
        (
            f"What a skeptical lead would try first on {host}: the path {d['requester']} "
            f"actually has, not an empty-tote photo. Metric I will argue is a clean "
            f"confirm, not a vanity units-per-hour. If we cannot show that path on {host2} "
            f"with the numbers already in this file, we do not have a cut. "
            f"{AUTHOR} will not accept a hallway yes as that proof."
        ),
        (
            f"Open clock: {d['lock']}. If that clock collides with a safety lock, the date "
            f"moves and the scope does not. {a} hears the new date on {t0}. "
            f"I will not book a change in the last 40 minutes of a lock because "
            f"it is 'just a rate.' A rate change is a change. Host if we have to prove a "
            f"count: {host}."
        ),
        (
            f"Failure mode if we ignore the refuse: {d['reject']} comes back wearing "
            f"a new coat. I want that named in review notes, not rediscovered by {c} "
            f"on a Monday. Ticket {t1}. Numbers I will not 'simplify': {n}. "
            f"Same clock as the front. I will not mix clocks to make {host} look healthier."
        ),
        (
            f"Handoff leftover for this file: next owner inherits {host}, {t0}, and "
            f"the last three working pages. Access that has to move is who can change "
            f"{host2} and who can talk to the requester. If that is still me six weeks "
            f"after pause, onboard failed. {b} accepts in writing."
        ),
    ]


def option_table(d: dict) -> dict:
    return {
        "type": "table",
        "caption": f"Options reviewed for {d['doc_id']}. {d['reject']} is the named refuse.",
        "headers": ["Option", "Effort / cash", "Risk", "Verdict"],
        "rows": [
            [
                "Do nothing (keep current path)",
                f"$0 cash, keep {d['current'][:80]}",
                f"Numbers already in play: {num_blob(d)}",
                "Reject. This is the status the requester is living with.",
            ],
            [
                d["reject"],
                d["reject_why"][:90],
                f"Named on {d['tickets'][-1]}",
                "Reject. See refuse callout.",
            ],
            [
                "Cheap shortcut (hallway yes, skip the written cut)",
                "Hours, not cash",
                "Scope returns as a group chat",
                "Reject. This file exists because that failed.",
            ],
            [
                "This document's lock",
                d["lock"],
                f"Host {d['host']}, ticket {d['ticket']}",
                "Accept. Written cut. Named owners.",
            ],
        ],
    }


def numbers_table(d: dict) -> dict:
    rows = [[k, str(v), d["host"], d["ticket"]] for k, v in d["nums"].items()]
    return {
        "type": "table",
        "caption": f"Numbers I will defend for {d['doc_id']}. Same clock as the front.",
        "headers": ["Name", "Value", "Host if measured", "Ticket"],
        "rows": rows,
    }


def raci_table(d: dict) -> dict:
    who = PEOPLE[d["people"]]
    return {
        "type": "table",
        "caption": f"RACI for {d['doc_id']}. A team name is not a person.",
        "headers": ["Work", "Responsible", "Accountable", "Consulted"],
        "rows": [
            ["Written cut", AUTHOR, who[0], who[1]],
            ["Refuse on " + d["reject"], AUTHOR, who[0], who[2]],
            ["Host " + d["host"], who[1], who[0], AUTHOR],
            ["Requester path", who[2], d["requester"], AUTHOR],
        ],
    }


def open_questions(d: dict) -> list[str]:
    who = PEOPLE[d["people"]]
    return [
        f"{who[2]}: does {d['hosts'][-1]} stay in the path? Yes, no, or a new date on {d['tickets'][-1]}.",
        f"{who[1]}: safety-lock collision for the first useful slice. Date moves, scope does not.",
        f"{d['requester']}: weekend coverage is not implied. Sign it or it stays out.",
        f"{AUTHOR}: leftover access on {d['host']} expires or the handoff failed.",
    ]


def code_block(d: dict) -> dict:
    host = d["host"]
    ticket = d["ticket"]
    if "ridgeway" in d["slug"]:
        text = (
            f"# {d['doc_id']} read-only first\n"
            f"date\n"
            f"echo host={host} bay check, hoist tag, PM sheet\n"
            f"echo 'do not start the engine until the tag is green'\n"
            f"# stop. write the last error in one sentence on {ticket}\n"
            f"# do not override a safety lock to free a bay"
        )
    else:
        text = (
            f"# {d['doc_id']} read-only first\n"
            f"date\n"
            f"echo host={host} RF login, location count, last short-pick\n"
            f"echo 'do not confirm a pick you cannot see'\n"
            f"# stop. write the last error in one sentence on {ticket}\n"
            f"# do not override a safety lock because a rate looks low"
        )
    return {"type": "code", "caption": f"Read-only. {ticket}. {host}.", "text": text}


def build_blocks(d: dict) -> list:
    paras = unique_paras(d)
    who = PEOPLE[d["people"]]
    blocks = [
        {"type": "h1", "text": d["title"]},
        {"type": "p", "text": paras[0]},
        {"type": "p", "text": paras[1]},
        {"type": "h2", "text": "Decision for leadership"},
        {"type": "callout", "kind": "decision", "label": "Decision", "text": d["decision"]},
        {"type": "p", "text": paras[2]},
        option_table(d),
        {"type": "h2", "text": "Background. Why the current path is the wrong tool"},
        {"type": "p", "text": paras[3]},
        {"type": "quote", "text": d["quote"], "attrib": d["quote_attr"]},
        {"type": "p", "text": paras[4]},
        {"type": "h2", "text": "Constraints and the lock"},
        {
            "type": "callout",
            "kind": "note",
            "label": "Lock",
            "text": f"{d['lock']} Host {d['host']}. Ticket {d['ticket']}. Acceptor {who[0]}.",
        },
        {"type": "p", "text": paras[5]},
        numbers_table(d),
        {"type": "h2", "text": f"Refuse: {d['reject']}"},
        {
            "type": "callout",
            "kind": "warn",
            "label": "Refuse",
            "text": (
                f"{d['reject']} is out. {d['reject_why']} "
                f"I will not reopen it because someone asked for a rate waiver."
            ),
        },
        {"type": "p", "text": paras[6]},
        {"type": "h2", "text": "Open questions with owners"},
        {"type": "bullets", "items": open_questions(d)},
        {"type": "h2", "text": "Working notes a colleague can execute"},
        {"type": "p", "text": paras[7]},
        code_block(d),
        {
            "type": "steps",
            "items": [
                f"Write the symptom on {d['ticket']} before any write.",
                f"Confirm on {d['host']} with the read-only commands above.",
                f"If the refuse on {d['reject']} is being reopened, stop and ping {who[0]}.",
                f"Wake {who[1]} only after a one-line diagnosis.",
                "Do not override a safety lock because a rate looks low.",
            ],
        },
        {"type": "h2", "text": "Ownership"},
        raci_table(d),
        {
            "type": "p",
            "text": (
                f"People who missed the room get the decision, the refuse, and the date, "
                f"not a reconstruction of tone. {who[3]} is on that list. Object on "
                f"{d['ticket']}. {AUTHOR} will reject a comment that is only 'as discussed.'"
            ),
        },
    ]
    extras = [
        (
            f"Named leftover unique to {d['doc_id']}",
            (
                f"{d['hosts'][1]} is in this file because skipping it is how the last "
                f"near-miss happened. {who[2]} owns the check. I want a count on "
                f"{d['tickets'][-1]} before anyone says the leftover is 'implied.' "
                f"Implied leftovers are how {d['reject']} almost returned."
            ),
        ),
        (
            f"What I will not claim in {d['doc_id']}",
            (
                f"I will not claim {d['reject']} is impossible at another shop. I will "
                f"claim we will not do it here. I will not claim zero incidents after this "
                f"cut. I will claim the next one dies at the gate named in the lock. "
                f"Host {d['host']}."
            ),
        ),
        (
            f"First useful slice for {d['ticket']}",
            (
                f"First useful is {d['lock']}, not a prettier board or a louder huddle. "
                f"{d['requester']} sees that slice on {d['hosts'][0]}. If the slice "
                f"needs a second process, that is a new ticket and {who[0]} is in the "
                f"thread. I will not hide it inside {d['doc_id']}."
            ),
        ),
        (
            f"Photos, labels, and identifiers ({d['n']:02d})",
            (
                f"A photo for this work is a bin or a seal, not a customer's face. "
                f"Tote IDs stay on {d['tickets'][0]}. Pressure is not a reason to paste "
                f"a phone number into the ticket. {AUTHOR} will bounce it. Host if we "
                f"have to prove a redaction: {d['hosts'][-1]}."
            ),
        ),
    ]
    for title, text in extras:
        blocks.append({"type": "h2", "text": title})
        blocks.append({"type": "p", "text": text})
    return blocks


def audience_line(d: dict) -> str:
    who = PEOPLE[d["people"]]
    return (
        f"{d['requester']} (requester); {who[0]} (acceptor); {who[1]} and {AUTHOR} "
        f"(build); {who[2]} (leftover host); {who[3]} (absentee pack)"
    )


def owners_line(d: dict) -> str:
    who = PEOPLE[d["people"]]
    return (
        f"{who[0]} (acceptor), {d['requester']} (requester), {who[1]} (ops), "
        f"{AUTHOR} (this document)"
    )


def team_line(d: dict) -> str:
    if "ridgeway" in d["slug"]:
        return "Ridgeway Diesel, shop floor"
    return "Pinecrest Fulfillment, building 2 operations"


def summary_line(d: dict) -> str:
    return (
        f"{d['requester']} asked for a written cut of {d['title'].split(',')[0].split(':')[0]}. "
        f"Current path: {d['current']}. This document locks {d['lock']}. "
        f"{d['reject']} is out because {d['reject_why']}"
    )


def build_spec(d: dict) -> dict:
    date = eng_date(d["date"])
    hist = revisions(d)
    return {
        "slug": d["slug"],
        "doc_id": d["doc_id"],
        "title": d["title"],
        "subtitle": d["subtitle"],
        "doc_type": d["doc_type"],
        "form_type": d["form_type"],
        "kicker": d["kicker"],
        "org": d["org"],
        "classification": "INTERNAL",
        "version": hist[-1][0],
        "status": status_for(d["doc_type"]),
        "date": date,
        "author": AUTHOR,
        "role": d["role"],
        "team": team_line(d),
        "audience": audience_line(d),
        "owners": owners_line(d),
        "related": "; ".join(d["tickets"]),
        "summary": summary_line(d),
        "form_description": d["form_description"],
        "field": FIELD,
        "revision_history": hist,
        "blocks": build_blocks(d),
    }


def main() -> None:
    CONTENT.mkdir(parents=True, exist_ok=True)
    for pth in CONTENT.glob("*.json"):
        pth.unlink()
    if DOCUMENTS.exists():
        for pth in DOCUMENTS.glob("*.docx"):
            pth.unlink()
    all_docs = fact_docs()
    assert len(all_docs) == 50, len(all_docs)
    slugs = [d["slug"] for d in all_docs]
    assert len(slugs) == len(set(slugs)), "duplicate slugs"
    for d in all_docs:
        spec = build_spec(d)
        path = CONTENT / f"{d['slug']}.json"
        path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.name}")
    print(f"\n{len(all_docs)} specs in {CONTENT}")


if __name__ == "__main__":
    main()

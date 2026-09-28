# Tech Titans API — proof of concept

Flask + SQLite, stdlib `sqlite3` (no ORM). Mirrors the JSON shapes already
used by the static site's `js/data/*.js` files, so a future frontend could
`fetch()` this instead of importing hardcoded JS objects.

`podcast_sheet_parser.py` is bundled here so the whole pipeline can run
from one place: xlsx -> parser -> JSON -> this API's DB.

## Setup

```
python3 -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

# get the JSON, then seed from it -- or use --sample to test without a real sheet
python podcast_sheet_parser.py "Tech Titans Podcast Master Sheet.xlsx" -o ./output
python seed_from_podcast_sheet.py --from-json ./output/"Tech Titans Podcast Master Sheet.json"
# or:
python seed_from_podcast_sheet.py --sample

python app.py                   # runs on http://localhost:5000
```

Re-running `--from-json` is safe and expected — it's meant to be re-run
every time the sheet updates. Episodes are matched by (project, episode
title) and UPSERTed: sheet-owned columns get refreshed, but
`idea_approved`, `finalising_approved`, `synopsis`, and `drive_id` are
never touched by import, so GUI edits to those survive a re-import.
`--sample` is `INSERT OR IGNORE` and just no-ops on a second run.

## How an episode's stage is derived

Per spec: episodes carry two flags the sheet has no equivalent for —
`idea_approved` and `finalising_approved` — set only through the API/GUI.
Stage is gated sequentially: `derive.py` won't read `script_status` at all
until `idea_approved` is true, won't read `recording_status` until script
is `Completed`, and so on. Concretely: an episode can show real progress in
the spreadsheet (script done, recording underway) and still report stage 0
here until a human confirms the idea was actually approved. Tested — see
`derive.py`'s docstring for the exact rule and the reasoning for gating
every step, not just the one it was explicitly specified for.

`estimatedRelease` on the API is the sheet's "Publish Date" column
specifically (not "Finish Date," which is captured as
`estimated_finish_date` but not currently surfaced anywhere) — "Publish"
maps directly to "when does this go live," which is what the site's
estimate is answering. Worth confirming that's the right one if "Finish"
turns out to mean something else in practice.

## Endpoints

| Method | Path                                | Notes |
|--------|-------------------------------------|-------|
| GET    | `/api/people`                        | |
| GET    | `/api/people/<slug>`                  | |
| POST   | `/api/people`                         | requires `slug`, `name`, `dept` |
| PUT    | `/api/people/<slug>`                  | partial update |
| DELETE | `/api/people/<slug>`                  | |
| GET    | `/api/production/projects`            | summary list |
| GET    | `/api/production/projects/<slug>`     | includes episodes (each with a stable `id`) |
| GET    | `/api/admin/production/projects/<slug>` | same, plus raw sheet statuses + manual flags — used by the admin GUI only |
| PUT    | `/api/production/episodes/<id>`       | `ideaApproved`, `finalisingApproved`, `synopsis`, `driveId` ONLY — sheet-owned fields aren't editable here, they come from the next import |
| GET    | `/api/coding/projects`                | |
| GET    | `/api/coding/projects/<slug>`         | |
| POST   | `/api/coding/projects`                | requires `slug`, `title` |
| PUT    | `/api/coding/projects/<slug>`         | partial update |
| DELETE | `/api/coding/projects/<slug>`         | |

Production PROJECTS (title/blurb/about/formUrl) are still read-only —
those are manual fields too (the sheet only gives an episode-level title),
just not wired up to write yet. Same pattern as the coding endpoints,
held off pending confirmation this shape is right.

## Admin GUI

Served by this same Flask app (same origin, so no CORS involved):

- `http://localhost:5000/admin/episodes` — idea/finalising approval, synopsis, Drive file ID
- `http://localhost:5000/admin/people` — add / edit / delete people

Coding-project admin isn't built yet (its API CRUD exists, the page doesn't).

## Running it together with the site

Two processes, two ports:

```
# terminal 1 — the API
python app.py                                  # http://localhost:5000

# terminal 2 — the static site, served from ITS root (it uses /root-relative paths)
cd ../tech-titans-site && python -m http.server 8080
```

The site's `js/api.js` has one constant, `API_BASE = 'http://localhost:5000'`.
That's the only thing to change when hosting is decided.

Known consequences of the site reading from the API:

- **The site now needs the API up.** Data pages (Production, Coding, project
  and person pages) show a "couldn't load — is the API running?" message if
  it's down. Home and 3D Printing don't depend on it. The fully-static
  version had no such dependency.
- **An empty DB means empty pages.** People, coding projects and project
  blurbs/about text are manual-only, so nothing appears until they're added
  (production projects/episodes arrive via the sheet import).
- **Won't work from a public site yet.** A visitor's browser calling
  `localhost:5000` hits *their own* machine, and an https page can't call an
  http API anyway. Public hosting needs the API reachable over https.

## What this deliberately does NOT do yet

- **No auth.** Every write endpoint is open. Fine for local testing, not
  safe on a network anyone else can reach.
- **CORS is local-dev only.** `app.py` allows any `http(s)://localhost:<port>`
  / `127.0.0.1:<port>` origin and nothing else. Fine for two local servers;
  once hosting is decided, replace `_LOCAL_ORIGIN` with the real site origin.
- **Date header names are assumed, not confirmed.** `PUBLISH_DATE_KEYS`/
  `FINISH_DATE_KEYS` in `seed_from_podcast_sheet.py` try a few likely
  normalized keys (confirmed working against a synthetic sheet using
  "Publish Date"/"Finish Date" as literal headers) and print a warning if
  none match. If the real sheet uses different header text, add the real
  key to those lists.
- **No Tkinter GUI yet** — this API is what it would talk to.
- **SQLite, single file.** Fine at this scale.

## What IS verified, not just asserted

Ran the actual `podcast_sheet_parser.py` against a synthetic workbook,
imported its real output, and confirmed: correct project/episode grouping,
correct stage gating (including the "real progress in the sheet, stage
still 0 because idea_approved isn't set" case), the PUT endpoint correctly
unlocking a gated stage, and a re-import correctly preserving manually-set
flags instead of overwriting them.

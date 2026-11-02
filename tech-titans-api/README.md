# tech-titans-api

Flask + SQLite (stdlib `sqlite3`, no ORM). Serves the site's data and hosts
the admin pages people use to edit it. Doesn't parse the sheet itself -
that's `tech-titans-parse/`, one folder up.

Run from the repo root (`python tech-titans-api/app.py`), not from inside
this folder - see the root README for why and for the full two-terminal
setup with the site.

## Files

```
app.py                      routes: /api/*, /admin/*
db.py                       sqlite3 connection + init
schema.sql                  table definitions
derive.py                   episode stage/state derivation - read this
                              before touching anything stage-related
seed_from_podcast_sheet.py  --sample and --from-json (the parser's output)
admin/                      the admin pages (plain HTML/CSS/JS, Flask
                              serves them as static files)
```

## Endpoints

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/people` | |
| GET | `/api/people/<slug>` | |
| POST | `/api/people` | requires `slug`, `name`, `dept` |
| PUT | `/api/people/<slug>` | partial update |
| DELETE | `/api/people/<slug>` | |
| GET | `/api/production/projects` | summary list |
| GET | `/api/production/projects/<slug>` | includes episodes, each with a stable `id` |
| GET | `/api/admin/production/projects/<slug>` | same, plus raw sheet statuses + manual flags - admin GUI only |
| PUT | `/api/production/episodes/<id>` | `ideaApproved`, `finalisingApproved`, `synopsis`, `driveId` **only** - sheet-owned fields aren't editable here, they come back on the next import regardless |
| GET | `/api/coding/projects` | |
| GET | `/api/coding/projects/<slug>` | |
| POST | `/api/coding/projects` | requires `slug`, `title` |
| PUT | `/api/coding/projects/<slug>` | partial update |
| DELETE | `/api/coding/projects/<slug>` | |

Production PROJECTS (title/blurb/about/formUrl) are still read-only - no
write endpoint yet, same reason Coding-project admin has no page yet:
built the CRUD pattern once (Coding), haven't repeated it everywhere.

## Admin pages

Same Flask app, same origin, no CORS involved:

- `/admin/episodes` - idea/finalising approval, synopsis, Drive file ID
- `/admin/people` - add / edit / delete people

No login on either page. Anyone who can reach the port can edit data.

## Seeding

```
python seed_from_podcast_sheet.py --sample              # placeholder data, no sheet needed
python seed_from_podcast_sheet.py --from-json <path>     # tech-titans-parse's output
```

Safe to re-run `--from-json` every time the sheet changes: episodes are
matched by (project, episode title) and UPSERTed. Only the sheet-owned
columns (statuses, priority, dates) get refreshed -
`idea_approved`/`finalising_approved`/`synopsis`/`drive_id` are never
touched by import, so admin edits survive a re-import. `--sample` uses
`INSERT OR IGNORE` and just no-ops the second time.

`member_list` from the sheet is never imported. People is manual-only,
Production included, by design.

## How an episode's stage is derived

`idea_approved` and `finalising_approved` are flags the sheet has no
equivalent for - set only through `/admin/episodes`. Stage is gated
sequentially: `derive.py` won't read `script_status` at all until
`idea_approved` is true, won't read `recording_status` until script is
`Completed`, and so on down the ladder. Concretely: an episode can show
real progress in the spreadsheet (script done, recording underway) and
still report stage 0 here until a human confirms the idea was actually
approved. The exact rule, and the reasoning for gating every step and not
just the one it was originally specified for, is in `derive.py`'s
docstring - read that before changing the stage logic, not this file.

`estimatedRelease` in the API response is the sheet's "Publish Date"
column specifically - "Finish Date" is captured as
`estimated_finish_date` but not currently shown anywhere. If "Finish"
turns out to be the more relevant one in practice, that's a one-line
change in `app.py`'s `row_to_episode`.

## Limits

- **No auth.** Every write endpoint and both admin pages are open to
  anyone who can reach the port. Fine for local use, not safe on a
  network anyone else can reach.
- **`app.run(debug=True)`.** Flask's debugger lets arbitrary code run if
  something crashes with the right conditions. Turn this off before this
  ever runs anywhere other than your own machine.
- **CORS is local-dev only** - `_LOCAL_ORIGIN` in `app.py` allows
  `localhost`/`127.0.0.1` on any port and nothing else.
- **Date header names are assumed, not confirmed.** `PUBLISH_DATE_KEYS`/
  `FINISH_DATE_KEYS` in `seed_from_podcast_sheet.py` try a few likely
  normalized keys - confirmed working against a synthetic sheet using
  "Publish Date"/"Finish Date" as the literal headers, not the real one.
  A mismatch prints a warning during import rather than failing silently.
- **SQLite, single file, no migrations.** Changing `schema.sql` after the
  fact means hand-editing or deleting `instance/tech_titans.db` - there's
  no migration tooling.

## What's actually been tested, not just written

Ran the real `podcast_sheet_parser.py` against a synthetic workbook (not
a hand-written fake JSON) and imported its actual output. Confirmed:
correct project/episode grouping, correct stage gating (including the
"sheet shows progress, stage still 0 because idea_approved isn't set"
case), the PUT endpoint correctly unlocking a gated stage, and a
re-import correctly preserving manually-set flags instead of overwriting
them. No automated test suite - this was manual, run-it-and-check
verification, documented here so it isn't repeated by accident.

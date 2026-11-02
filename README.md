# Tech Titans

Code for the Tech Titans student tech group: the website, the API behind it, and the parser for the Podcast Master Sheet.

Code only. Nothing here is hosted.

## Layout

```
tech-titans-site/    the website. Vanilla HTML/CSS/JS, no build step
tech-titans-api/     Flask + SQLite API, plus the admin pages
tech-titans-parse/   Podcast Master Sheet (.xlsx) -> JSON
requirements.txt     Python deps for api + parse (Flask, openpyxl)
```

The site only talks to the API. The API gets its data from two places: the sheet (through the parser) and the admin pages.

## Run it

```bash
python -m venv venv
venv\Scripts\activate          # mac/linux: source venv/bin/activate
pip install -r requirements.txt
```

Two terminals, both from the repo root:

```bash
python tech-titans-api/app.py                       # API + admin  -> http://localhost:5000
cd tech-titans-site && python -m http.server 8080   # site        -> http://localhost:8080
```

You can also use the included `dev.sh` to do these two at the same time, this is only avaliable for Unix systems:

```bash
chmod +x dev.sh
./dev.sh
```

- Serve the site from inside its own folder. It uses root-relative paths (`/css/...`), so serving from the repo root breaks it.
- The API has to be running. Data pages show a "couldn't load" message without it. Home and 3D Printing don't need it.
- First run the database is empty, so the pages are empty. For placeholder data:

```
python tech-titans-api/seed_from_podcast_sheet.py --sample
```

## Loading the real sheet

```
python tech-titans-parse/podcast_sheet_parser.py "Master Sheet.xlsx" -o output
python tech-titans-api/seed_from_podcast_sheet.py --from-json "output/Master Sheet.json"
```

The parser writes a `.json` and a readable `.txt` report into `output/`. Re-run both commands whenever the sheet changes. Re-importing refreshes the sheet's fields (statuses, dates) and never touches the manual ones. Only Production episodes are imported; the sheet's Member List is ignored on purpose.

## Who edits what

| What | Where |
| --- | --- |
| Script / recording / editing / publish status, target dates | The sheet, then re-import |
| Idea approved, finalising approved, synopsis, Drive file ID | `http://localhost:5000/admin/episodes` |
| People | `http://localhost:5000/admin/people` |
| Coding projects | API only, no admin page yet (see `tech-titans-api/README.md`) |
| Production project blurb / about / form link | Not editable yet. Projects imported from the sheet start blank |
| Department names and descriptions, Home text | Hardcoded in `tech-titans-site/js/` |

## Episode stages

An episode's stage (0-6) is derived, not stored. Two steps are manual because the sheet has no equivalent: "idea approved" and "finalising". The rules, and why each step is gated on the one before it, are in `tech-titans-api/derive.py`.

The stage list exists in three places. Change them together:

- `tech-titans-site/js/data/config.js`
- `tech-titans-api/admin/episodes.js`
- `tech-titans-api/derive.py`

## Limits

Read before changing anything.

- No auth on the API or the admin pages, and `app.py` runs with `debug=True`. Local use only. Don't put it on a network other people can reach.
- CORS only allows `localhost` / `127.0.0.1`, and the site's API address is hardcoded (`API_BASE` in `tech-titans-site/js/api.js`). It can't be hosted publicly as-is.
- The sheet's date columns are assumed to be headed "Publish Date" and "Finish Date". If yours differ, the seed script prints a warning and no estimated dates show. Add the real names to `PUBLISH_DATE_KEYS` / `FINISH_DATE_KEYS` in `seed_from_podcast_sheet.py`.
- Only "Publish Date" is shown on the site as the release estimate. "Finish Date" is stored but not displayed.
- No test suite.

## Don't commit data

`tech-titans-api/instance/` (the database), the parser's `output/`, and the `.xlsx` contain real member and episode data. `.gitignore` covers them. Keep it that way.

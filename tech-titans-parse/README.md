# tech-titans-parse

Reads the Podcast Master Sheet (`.xlsx`) and writes a `.json` and a plain-text
`.txt` report. The API's `seed_from_podcast_sheet.py` reads the `.json`.

Nothing here talks to the API, the site, or the network. One file in,
two files out.

## Run

```
python podcast_sheet_parser.py "Master Sheet.xlsx" -o output
```

Writes `output/Master Sheet.json` and `output/Master Sheet.txt`.

## What it expects

Three sheets: Member List, Project List, Meeting Dates. Only Project List
is actually used downstream right now (by the seed script) - Member List
and Meeting Dates get parsed and reported on, but nothing reads them yet.

Project List's `Project` column has to be `<Show Title> - <Episode Title>`,
e.g. `H.E.A.R.T - Honor`. The parser splits this into `project_title` and
`episode_title`. Multiple rows with the same show title become one show
with several episodes downstream.

Controlled values it checks (flags anything else as a warning rather than
failing): `script_status` / `recording_status` / `editing_status` - Not
Started, In Progress, Completed. `ready_status` - Ready, Not Ready.
`publish_status` - Published, Not Published. `priority` - P0-P3. `guest` -
Have, Do Not Have.

Every record also gets `_complete` (bool) and `_validation_warnings` (list)
added by the parser - that's how the seed script decides what to flag.

## Publish Date / Finish Date

The seed script wants two date columns off Project List - the sheet's
projected publish date and projected finish date - for the site's release
estimate. This parser doesn't hardcode their names; whatever your header
row says becomes the key (lowercased, spaces to underscores). Confirmed
working with headers literally named `Publish Date` / `Finish Date` → keys
`publish_date` / `finish_date`. If your real sheet uses different header
text, the seed script won't find them and says so - see its README.

## Output shape

```
{
  "metadata": {...},
  "data": {
    "project_list":  {"sheet_name": "Project List",  "records": [...]},
    "member_list":   {"sheet_name": "Member List",   "records": [...]},
    "meeting_dates": {"sheet_name": "Meeting Dates",  "records": [...]}
  }
}
```

`seed_from_podcast_sheet.py` reads `data.project_list.records`.

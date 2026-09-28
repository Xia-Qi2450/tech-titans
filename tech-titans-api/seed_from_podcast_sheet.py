"""
Seeds the SQLite DB.

  python seed_from_podcast_sheet.py --sample
      Small built-in placeholder dataset, matching the shapes already used
      as placeholders in the static site's js/data/*.js. Lets you test the
      API without needing a real spreadsheet export.

  python seed_from_podcast_sheet.py --from-json path/to/export.json
      Imports Production episodes from podcast_sheet_parser.py's real JSON
      output (verified against the actual script, not guessed).

      Reads data["data"]["project_list"]["records"]. Each record's
      project_title/episode_title (already split by the parser) become a
      production_project + episode row. Safe to re-run: existing episodes
      are matched by (project, episode title) and UPDATED rather than
      duplicated, and only the sheet-owned columns are touched --
      idea_approved, finalising_approved, synopsis and drive_id are never
      written here, since those are GUI/API-only fields.

      member_list is intentionally NOT imported -- people stays manual-only
      even for Production, per instruction.

      "Publish Date"/"Finish Date" column headers are assumed to produce
      normalized keys "publish_date"/"finish_date" (confirmed against a
      synthetic sheet using those exact header names, not your real one).
      If your sheet uses different header text, PUBLISH_DATE_KEYS /
      FINISH_DATE_KEYS below won't find a match and this prints a warning
      naming the record -- add the real key to those lists if that happens.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from db import get_db, init_db

PUBLISH_DATE_KEYS = ["publish_date", "projected_publish_date", "estimated_publish_date"]
FINISH_DATE_KEYS = ["finish_date", "projected_finish_date", "estimated_finish_date"]


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.strip().lower()).strip("-")
    return s or "untitled"


def first_present(record, candidate_keys):
    for key in candidate_keys:
        if record.get(key):
            return record[key]
    return None


def seed_sample(conn):
    conn.execute(
        "INSERT OR IGNORE INTO people (slug,name,role,dept,is_teacher,bio) VALUES (?,?,?,?,?,?)",
        ("teacher-1", "REPLACE Teacher Name", "Teacher-in-charge", "production", 1,
         "REPLACE — what this teacher oversees in the department."),
    )
    conn.execute(
        "INSERT OR IGNORE INTO people (slug,name,role,dept,is_teacher,bio) VALUES (?,?,?,?,?,?)",
        ("member-1", "REPLACE Member One", "Host / Producer", "production", 0, "REPLACE — short bio."),
    )

    conn.execute(
        """INSERT OR IGNORE INTO production_projects (slug,title,status,featured,blurb,about,form_url)
           VALUES (?,?,?,?,?,?,?)""",
        ("heart", "H.E.A.R.T.", "active", 1,
         "A discussion series on our school values, with teacher interviews on each one.",
         "Each episode takes one school value, unpacks what it means to us as students, "
         "then brings in a teacher to give their own perspective on it.", ""),
    )
    proj_id = conn.execute("SELECT id FROM production_projects WHERE slug='heart'").fetchone()["id"]

    conn.execute(
        """INSERT OR IGNORE INTO episodes
           (project_id,title,script_status,recording_status,editing_status,ready_status,publish_status,
            priority,idea_approved,finalising_approved,synopsis,drive_id)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (proj_id, "Honor", "Completed", "Completed", "Completed", "Ready", "Published",
         "P1", 1, 1, "REPLACE — synopsis for the Honor episode.", "REPLACE_DRIVE_FILE_ID"),
    )
    conn.execute(
        """INSERT OR IGNORE INTO episodes
           (project_id,title,script_status,recording_status,editing_status,ready_status,publish_status,
            priority,idea_approved,estimated_publish_date,estimated_finish_date)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (proj_id, "REPLACE — next value", "Completed", "In Progress", "Not Started", "Not Ready",
         "Not Published", "P2", 1, "2026-10-15", "2026-10-10"),
    )
    conn.commit()

    conn.execute(
        """INSERT OR IGNORE INTO coding_projects
           (slug,title,status,featured,blurb,description,how_to_use,github_url,website_url,stage,estimated_release)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        ("replace-project-two", "REPLACE Project Two", "unfinished", 1,
         "REPLACE — one-line summary for the department index card.",
         "REPLACE — what this tool or website is meant to do once finished.",
         "REPLACE — how to use it so far, or what to expect once it's complete.",
         "https://github.com/REPLACE_ORG/REPLACE_REPO_2", "https://REPLACE.example.com",
         2, "2026-10-08"),
    )
    conn.commit()


def seed_from_podcast_json(conn, path):
    payload = json.loads(Path(path).read_text())
    try:
        records = payload["data"]["project_list"]["records"]
    except (KeyError, TypeError):
        sys.exit(
            "Expected data.project_list.records in the JSON (podcast_sheet_parser.py's real shape) "
            "-- got something else. Is this the right file?"
        )

    seen_projects = {}
    missing_dates = 0
    incomplete_or_flagged = 0

    for record in records:
        title = (record.get("project_title") or "").strip()
        episode = (record.get("episode_title") or "").strip()
        if not title:
            print(f"Skipping row with no usable project title: {record.get('project')!r}")
            continue
        if not episode:
            episode = record.get("project") or "Untitled episode"

        if not record.get("_complete") or record.get("_validation_warnings"):
            incomplete_or_flagged += 1

        slug = slugify(title)
        if slug not in seen_projects:
            conn.execute(
                """INSERT OR IGNORE INTO production_projects (slug,title,status,featured,blurb,about,form_url)
                   VALUES (?,?,?,?,?,?,?)""",
                (slug, title, "active", 1, "", "", ""),
            )
            seen_projects[slug] = conn.execute(
                "SELECT id FROM production_projects WHERE slug = ?", (slug,)
            ).fetchone()["id"]
        project_id = seen_projects[slug]

        publish_date = first_present(record, PUBLISH_DATE_KEYS)
        finish_date = first_present(record, FINISH_DATE_KEYS)
        if publish_date is None and finish_date is None:
            missing_dates += 1

        conn.execute(
            """INSERT INTO episodes
                 (project_id, title, script_status, recording_status, editing_status,
                  ready_status, publish_status, priority, estimated_finish_date, estimated_publish_date)
               VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(project_id, title) DO UPDATE SET
                 script_status = excluded.script_status,
                 recording_status = excluded.recording_status,
                 editing_status = excluded.editing_status,
                 ready_status = excluded.ready_status,
                 publish_status = excluded.publish_status,
                 priority = excluded.priority,
                 estimated_finish_date = excluded.estimated_finish_date,
                 estimated_publish_date = excluded.estimated_publish_date
            """,
            (
                project_id, episode,
                record.get("script_status", "Not Started"),
                record.get("recording_status", "Not Started"),
                record.get("editing_status", "Not Started"),
                record.get("ready_status", "Not Ready"),
                record.get("publish_status", "Not Published"),
                record.get("priority"),
                finish_date, publish_date,
            ),
        )

    conn.commit()
    print(f"Imported/updated {len(records)} episode row(s) across {len(seen_projects)} project(s).")
    if incomplete_or_flagged:
        print(f"{incomplete_or_flagged} row(s) were incomplete or had validation warnings in the sheet — "
              f"check the parser's own report for details.")
    if missing_dates:
        print(f"{missing_dates} row(s) had no recognizable Publish/Finish date column "
              f"(tried {PUBLISH_DATE_KEYS + FINISH_DATE_KEYS}) — "
              f"if your sheet uses different header text, add the real key to this script.")
    print("member_list was not imported — people stays manual-only, per instruction.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--sample", action="store_true", help="load the built-in placeholder dataset")
    group.add_argument("--from-json", metavar="PATH", help="import podcast_sheet_parser.py's JSON output")
    args = ap.parse_args()

    init_db()
    conn = get_db()
    if args.sample:
        seed_sample(conn)
        print("Seeded sample data.")
    else:
        seed_from_podcast_json(conn, args.from_json)
    conn.close()

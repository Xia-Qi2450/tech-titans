-- Mirrors the shapes already used by the static site's js/data/*.js files,
-- so a future frontend could fetch() this instead of importing hardcoded
-- JS objects with minimal changes.

CREATE TABLE IF NOT EXISTS people (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  role TEXT,
  dept TEXT NOT NULL,
  is_teacher INTEGER NOT NULL DEFAULT 0,
  bio TEXT
  -- Deliberately no link to podcast_sheet_parser.py's Member List: per
  -- instruction, people is manual-only, even for Production members.
);

CREATE TABLE IF NOT EXISTS production_projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'todo',   -- 'active' | 'todo'
  featured INTEGER NOT NULL DEFAULT 0,
  blurb TEXT,
  about TEXT,
  form_url TEXT
  -- blurb/about/form_url/featured/status are manual -- the sheet only ever
  -- gives us a project TITLE (split from the "Project" column), nothing
  -- describing the show itself.
);

-- script_status / recording_status / editing_status / ready_status /
-- publish_status / priority / estimated_finish_date / estimated_publish_date
-- are the REAL fields read from the Podcast Master Sheet on every import
-- and are overwritten by re-import -- don't hand-edit them, they won't
-- stick. idea_approved / finalising_approved / synopsis / drive_id are the
-- opposite: never touched by import, only ever set through the API/GUI.
CREATE TABLE IF NOT EXISTS episodes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES production_projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,

  -- sheet-sourced, refreshed on every --from-json import
  script_status TEXT NOT NULL DEFAULT 'Not Started',
  recording_status TEXT NOT NULL DEFAULT 'Not Started',
  editing_status TEXT NOT NULL DEFAULT 'Not Started',
  ready_status TEXT NOT NULL DEFAULT 'Not Ready',
  publish_status TEXT NOT NULL DEFAULT 'Not Published',
  priority TEXT,
  estimated_finish_date TEXT,    -- sheet's "Finish Date" -- internal target, not shown on the site yet
  estimated_publish_date TEXT,   -- sheet's "Publish Date" -- surfaced as the site's estimatedRelease

  -- manual-only, never touched by import
  idea_approved INTEGER NOT NULL DEFAULT 0,
  finalising_approved INTEGER NOT NULL DEFAULT 0,
  synopsis TEXT,
  drive_id TEXT,

  UNIQUE(project_id, title)   -- lets re-import UPSERT instead of duplicating rows
);

-- No spreadsheet source for Coding yet, so everything here is set directly
-- by whoever edits the project (via the API, eventually the Tkinter GUI).
CREATE TABLE IF NOT EXISTS coding_projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'unfinished',  -- 'finished' | 'unfinished'
  featured INTEGER NOT NULL DEFAULT 0,
  blurb TEXT,
  description TEXT,
  how_to_use TEXT,
  github_url TEXT,
  website_url TEXT,
  stage INTEGER NOT NULL DEFAULT 0,
  estimated_release TEXT
);

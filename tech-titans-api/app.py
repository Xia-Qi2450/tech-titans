import re
import sqlite3
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

from db import get_db, init_db
from derive import derive_stage, derive_state

app = Flask(__name__)
ADMIN_DIR = Path(__file__).parent / "admin"

# Local-dev CORS: allows any http(s)://localhost:<port> or 127.0.0.1:<port>
# origin, since the static site and this API run as separate local servers
# on different ports. NOT scoped for a real deployment -- once hosting is
# decided, replace the regex with the actual site origin(s).
_LOCAL_ORIGIN = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin and _LOCAL_ORIGIN.match(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/api/<path:_ignored>", methods=["OPTIONS"])
def cors_preflight(_ignored):
    return ("", 204)


# ---------- serialization: DB row -> the same JSON shape js/data/*.js uses ----------

def row_to_person(r):
    return {
        "slug": r["slug"],
        "name": r["name"],
        "role": r["role"],
        "dept": r["dept"],
        "teacher": bool(r["is_teacher"]),
        "bio": r["bio"],
    }


def row_to_episode(r):
    state = derive_state(r["publish_status"])
    ep = {"id": r["id"], "title": r["title"], "state": state, "synopsis": r["synopsis"] or ""}
    if state == "production":
        ep["stage"] = derive_stage(
            bool(r["idea_approved"]), r["script_status"], r["recording_status"],
            r["editing_status"], bool(r["finalising_approved"]), r["publish_status"],
        )
    else:
        ep["drive"] = r["drive_id"] or ""
    # Only the sheet's "Publish Date" is surfaced as the site's release
    # estimate -- "Finish Date" is an internal production target, tracked
    # (estimated_finish_date) but not currently shown anywhere.
    if r["estimated_publish_date"]:
        ep["estimatedRelease"] = r["estimated_publish_date"]
    return ep


def row_to_episode_admin(r):
    """Everything row_to_episode has, PLUS the raw sheet-sourced statuses
    and the manual flags -- fields the public site never needs, but the
    admin page needs to show as context (e.g. so 'finalising approved'
    can be disabled until editing_status is actually Completed) and to
    pre-fill its edit form."""
    out = row_to_episode(r)
    out.update({
        "scriptStatus": r["script_status"],
        "recordingStatus": r["recording_status"],
        "editingStatus": r["editing_status"],
        "readyStatus": r["ready_status"],
        "publishStatus": r["publish_status"],
        "priority": r["priority"],
        "estimatedFinishDate": r["estimated_finish_date"],
        "estimatedPublishDate": r["estimated_publish_date"],
        "ideaApproved": bool(r["idea_approved"]),
        "finalisingApproved": bool(r["finalising_approved"]),
        "driveId": r["drive_id"] or "",
    })
    return out


def row_to_production_project(r, episodes):
    return {
        "slug": r["slug"],
        "title": r["title"],
        "status": r["status"],
        "featured": bool(r["featured"]),
        "blurb": r["blurb"] or "",
        "about": r["about"] or "",
        "formUrl": r["form_url"] or "",
        "episodes": episodes,
    }


def row_to_coding_project(r):
    out = {
        "slug": r["slug"],
        "title": r["title"],
        "status": r["status"],
        "featured": bool(r["featured"]),
        "blurb": r["blurb"] or "",
        "description": r["description"] or "",
        "howToUse": r["how_to_use"] or "",
        "githubUrl": r["github_url"] or "",
        "websiteUrl": r["website_url"] or "",
        "stage": r["stage"],
    }
    if r["estimated_release"]:
        out["estimatedRelease"] = r["estimated_release"]
    return out


# ---------- people (fully manual -- create/edit/delete all supported) ----------

@app.get("/api/people")
def list_people():
    conn = get_db()
    rows = conn.execute("SELECT * FROM people").fetchall()
    conn.close()
    return jsonify([row_to_person(r) for r in rows])


@app.get("/api/people/<slug>")
def get_person(slug):
    conn = get_db()
    r = conn.execute("SELECT * FROM people WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    if not r:
        abort(404)
    return jsonify(row_to_person(r))


@app.post("/api/people")
def create_person():
    data = request.get_json(force=True, silent=True) or {}
    missing = [k for k in ("slug", "name", "dept") if not data.get(k)]
    if missing:
        return jsonify({"error": f"missing required field(s): {', '.join(missing)}"}), 400
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO people (slug,name,role,dept,is_teacher,bio) VALUES (?,?,?,?,?,?)",
            (data["slug"], data["name"], data.get("role", ""), data["dept"],
             int(bool(data.get("teacher"))), data.get("bio", "")),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": f"a person with slug '{data['slug']}' already exists"}), 409
    conn.close()
    return jsonify({"created": data["slug"]}), 201


@app.put("/api/people/<slug>")
def update_person(slug):
    data = request.get_json(force=True, silent=True) or {}
    conn = get_db()
    exists = conn.execute("SELECT id FROM people WHERE slug = ?", (slug,)).fetchone()
    if not exists:
        conn.close()
        abort(404)
    colmap = {"name": "name", "role": "role", "dept": "dept", "teacher": "is_teacher", "bio": "bio"}
    sets, values = [], []
    for key, col in colmap.items():
        if key in data:
            values.append(int(bool(data[key])) if key == "teacher" else data[key])
            sets.append(f"{col} = ?")
    if sets:
        values.append(slug)
        conn.execute(f"UPDATE people SET {', '.join(sets)} WHERE slug = ?", values)
        conn.commit()
    conn.close()
    return jsonify({"updated": slug})


@app.delete("/api/people/<slug>")
def delete_person(slug):
    conn = get_db()
    cur = conn.execute("DELETE FROM people WHERE slug = ?", (slug,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        abort(404)
    return jsonify({"deleted": slug})


# ---------- production (projects read-only for now; episodes get a manual-fields PUT) ----------

@app.get("/api/production/projects")
def list_production_projects():
    conn = get_db()
    rows = conn.execute("SELECT * FROM production_projects").fetchall()
    conn.close()
    return jsonify([
        {"slug": r["slug"], "title": r["title"], "status": r["status"],
         "featured": bool(r["featured"]), "blurb": r["blurb"] or ""}
        for r in rows
    ])


@app.get("/api/production/projects/<slug>")
def get_production_project(slug):
    conn = get_db()
    r = conn.execute("SELECT * FROM production_projects WHERE slug = ?", (slug,)).fetchone()
    if not r:
        conn.close()
        abort(404)
    eps = conn.execute("SELECT * FROM episodes WHERE project_id = ?", (r["id"],)).fetchall()
    conn.close()
    return jsonify(row_to_production_project(r, [row_to_episode(e) for e in eps]))


@app.get("/api/admin/production/projects/<slug>")
def get_production_project_admin(slug):
    """Same as above but with row_to_episode_admin -- raw statuses and
    manual flags included, for the admin GUI only."""
    conn = get_db()
    r = conn.execute("SELECT * FROM production_projects WHERE slug = ?", (slug,)).fetchone()
    if not r:
        conn.close()
        abort(404)
    eps = conn.execute("SELECT * FROM episodes WHERE project_id = ?", (r["id"],)).fetchall()
    conn.close()
    return jsonify(row_to_production_project(r, [row_to_episode_admin(e) for e in eps]))


@app.put("/api/production/episodes/<int:episode_id>")
def update_episode(episode_id):
    """Only touches the manual/GUI-only columns: idea_approved,
    finalising_approved, synopsis, drive_id. script_status/recording_status/
    editing_status/publish_status/priority/dates are sheet-owned and come
    back on the next --from-json import regardless of what's sent here."""
    data = request.get_json(force=True, silent=True) or {}
    conn = get_db()
    exists = conn.execute("SELECT id FROM episodes WHERE id = ?", (episode_id,)).fetchone()
    if not exists:
        conn.close()
        abort(404)

    colmap = {
        "ideaApproved": "idea_approved",
        "finalisingApproved": "finalising_approved",
        "synopsis": "synopsis",
        "driveId": "drive_id",
    }
    sets, values = [], []
    for key, col in colmap.items():
        if key in data:
            val = data[key]
            if key in ("ideaApproved", "finalisingApproved"):
                val = int(bool(val))
            sets.append(f"{col} = ?")
            values.append(val)
    if sets:
        values.append(episode_id)
        conn.execute(f"UPDATE episodes SET {', '.join(sets)} WHERE id = ?", values)
        conn.commit()
    conn.close()
    return jsonify({"updated": episode_id})


# ---------- coding (full CRUD -- everything here is manual, no sheet source) ----------

@app.get("/api/coding/projects")
def list_coding_projects():
    conn = get_db()
    rows = conn.execute("SELECT * FROM coding_projects").fetchall()
    conn.close()
    return jsonify([row_to_coding_project(r) for r in rows])


@app.get("/api/coding/projects/<slug>")
def get_coding_project(slug):
    conn = get_db()
    r = conn.execute("SELECT * FROM coding_projects WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    if not r:
        abort(404)
    return jsonify(row_to_coding_project(r))


@app.post("/api/coding/projects")
def create_coding_project():
    data = request.get_json(force=True, silent=True) or {}
    missing = [k for k in ("slug", "title") if not data.get(k)]
    if missing:
        return jsonify({"error": f"missing required field(s): {', '.join(missing)}"}), 400

    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO coding_projects
               (slug, title, status, featured, blurb, description, how_to_use,
                github_url, website_url, stage, estimated_release)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data["slug"], data["title"], data.get("status", "unfinished"),
                int(bool(data.get("featured"))), data.get("blurb", ""), data.get("description", ""),
                data.get("howToUse", ""), data.get("githubUrl", ""), data.get("websiteUrl", ""),
                int(data.get("stage", 0)), data.get("estimatedRelease"),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": f"a project with slug '{data['slug']}' already exists"}), 409
    conn.close()
    return jsonify({"created": data["slug"]}), 201


@app.put("/api/coding/projects/<slug>")
def update_coding_project(slug):
    data = request.get_json(force=True, silent=True) or {}
    conn = get_db()
    exists = conn.execute("SELECT id FROM coding_projects WHERE slug = ?", (slug,)).fetchone()
    if not exists:
        conn.close()
        abort(404)

    colmap = {
        "title": "title", "status": "status", "featured": "featured", "blurb": "blurb",
        "description": "description", "howToUse": "how_to_use", "githubUrl": "github_url",
        "websiteUrl": "website_url", "stage": "stage", "estimatedRelease": "estimated_release",
    }
    sets, values = [], []
    for key, col in colmap.items():
        if key in data:
            values.append(int(bool(data[key])) if key == "featured" else data[key])
            sets.append(f"{col} = ?")

    if sets:
        values.append(slug)
        conn.execute(f"UPDATE coding_projects SET {', '.join(sets)} WHERE slug = ?", values)
        conn.commit()
    conn.close()
    return jsonify({"updated": slug})


@app.delete("/api/coding/projects/<slug>")
def delete_coding_project(slug):
    conn = get_db()
    cur = conn.execute("DELETE FROM coding_projects WHERE slug = ?", (slug,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        abort(404)
    return jsonify({"deleted": slug})


# ---------- admin GUI (static files, same-origin so no CORS needed) ----------

@app.get("/admin/episodes")
def admin_episodes_page():
    return send_from_directory(ADMIN_DIR, "episodes.html")


@app.get("/admin/people")
def admin_people_page():
    return send_from_directory(ADMIN_DIR, "people.html")


@app.get("/admin/<path:filename>")
def admin_assets(filename):
    return send_from_directory(ADMIN_DIR, filename)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)

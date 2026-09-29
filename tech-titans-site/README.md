# tech-titans-site

Vanilla HTML/CSS/JS. No build step, no framework, no npm install - open
`index.html` through a local server and it runs.

Talks to the API for everything except Home and 3D Printing (those are
static copy). If the API's not running, those pages show a plain
"couldn't load" message instead of breaking silently.

## Serve it from its own root

```
cd tech-titans-site
python -m http.server 8080
```

Every page loads CSS/JS with root-relative paths (`/css/styles.css`, not
`css/styles.css`) on purpose - see "Routing", below. Serving this folder
from anywhere other than its own root, or from a parent folder, breaks
those paths.

## Routing: real files, not a JS router

Each page is an actual file at an actual path - `/production/index.html`,
`/production/view/index.html` - not one HTML shell with client-side
routing. That was a deliberate change: an earlier version faked routes
with JS and it broke the moment something tried to link to a page
directly (`Cannot GET /production/heart` from a plain static server with
no fallback configured). Real files don't have that failure mode on any
static host, with zero configuration.

```
/                          Home (static)
/production/               Production department
/production/view/?production=<slug>   one project
/coding/                   Coding department
/coding/view/?coding=<slug>           one project
/printing/                 3D Printing (static, department not formed yet)
/people/view/?person=<slug>           one person
```

The `?production=`/`?coding=`/`?person=` query param is how a "detail"
page knows which record to fetch - there's no per-slug HTML file, one
`view/index.html` handles all of them for that section. Missing the query
param redirects to the section's index; an unknown slug shows a
not-found message without changing the URL.

`404.html` is a plain static page for genuinely bad URLs. It doesn't run
any JS - nothing on it needs the API.

## Where data comes from

```
js/pages/*.js       one file per route above - fetches, then renders
js/api.js           the only file that knows the API's address
js/views/*.js        pure functions: (data) -> HTML string. No fetching.
js/components/*.js   shared pieces views build with (cards, episode
                      tracker, progress bars)
js/data/config.js    NOT API data - local site config: the two progress-
                      bar stage lists (STAGES, CODING_STAGES). Keep these
                      in sync with tech-titans-api/derive.py and
                      tech-titans-api/admin/episodes.js if you change them
```

A page script's job is always: fetch → pass the result straight to a view
function → put the returned string in `#app`. Views never fetch anything
themselves, which is what makes them easy to test - call one with fake
data and check the HTML it returns.

`js/api.js` has one constant, `API_BASE`, currently
`http://localhost:5000`. That's the only line that changes if the API
ever moves.

## Hardcoded vs API-driven

Department names and blurbs ("Production Team", "We make video
podcasts...") are hardcoded in `js/views/production.js` /
`js/views/coding.js` - there's no "departments" table, this is site copy,
not something the club edits week to week. Home's content is hardcoded
the same way. Everything else - projects, episodes, people - comes from
the API.

## Other things worth knowing

- **Episode cards are keyed by database ID**, not their position in the
  list (`data-ep="7"`, not an array index). If you're adding a feature
  that touches episode cards, use the ID.
- **The loading screen is deliberate, not a bug.** `js/loader.js` holds it
  up for at least ~700ms even when the API answers instantly - see the
  comment in that file if it looks like it's stalling on purpose, because
  it is.
- Closing the episode modal wipes its content instead of just hiding it.
  That's required, not decorative - a Drive video embed keeps playing in
  the background otherwise. See the comment above the `close` listener in
  `js/components/episode.js` before changing how the modal closes.
- No CSS framework. Colors/spacing/fonts are CSS custom properties at the
  top of `css/styles.css` (`--accent`, `--bg`, etc.) - change the look by
  changing those, not by hunting through every rule.

import { esc } from '../utils.js';
import { members } from '../components/members.js';

// Department copy stays local rather than API-sourced -- it's site content
// (rarely changes), not operational data the club edits week to week, the
// same way Home's copy and Printing's stub text are hardcoded.
var DEPT_NAME = 'Production Team';
var DEPT_LEAD = 'We make video podcasts and other programmes — discussion-led shows built around the school community, from teacher interviews to student submissions.';

export function vProduction(projects, people) {
  var ps = projects.filter(function (p) { return p.featured; }).slice(0, 5);
  var h = '<a class="back" href="/">&larr; All departments</a><div class="eyebrow">Department</div><h1>' + esc(DEPT_NAME) + '</h1><p class="lead">' + esc(DEPT_LEAD) + '</p>';
  h += '<h2>Featured projects</h2><div class="grid">';
  if (!ps.length) h += '<p>No projects to show yet.</p>';
  ps.forEach(function (p) {
    var ok = p.status === 'active';
    h += '<a class="card" href="/production/view/?production=' + encodeURIComponent(p.slug) + '"><span class="tag ' + (ok ? 't-ok' : 't-warn') + '">' + (ok ? 'Active' : 'Planned') + '</span><h3>' + esc(p.title) + '</h3><p>' + esc(p.blurb) + '</p><span class="arrow">View project &rarr;</span></a>';
  });
  h += '</div>';
  if (projects.length > ps.length) h += '<p style="margin-top:1rem">Showing ' + ps.length + ' of ' + projects.length + ' projects.</p>';
  return h + members(people, 'production');
}

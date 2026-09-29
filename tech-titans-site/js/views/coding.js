import { esc } from '../utils.js';
import { members } from '../components/members.js';
import { estimateLine } from '../estimate.js';

var DEPT_NAME = 'Coding Team';
var DEPT_LEAD = 'We build programs and web pages that benefit teachers and the student body - practical software for the people already in this building.';

export function vCoding(projects, people) {
  var ps = projects.filter(function (p) { return p.featured; }).slice(0, 5);
  var h = '<a class="back" href="/">&larr; All departments</a><div class="eyebrow">Department</div><h1>' + esc(DEPT_NAME) + '</h1><p class="lead">' + esc(DEPT_LEAD) + '</p>';
  h += '<h2>Featured projects</h2><div class="grid">';
  if (!ps.length) h += '<p>No projects to show yet.</p>';
  ps.forEach(function (p) {
    var ok = p.status === 'finished';
    var est = ok ? '' : estimateLine(p.estimatedRelease);
    h += '<a class="card" href="/coding/view/?coding=' + encodeURIComponent(p.slug) + '"><span class="tag ' + (ok ? 't-ok' : 't-warn') + '">' + (ok ? 'Finished' : 'In progress') + '</span><h3>' + esc(p.title) + '</h3><p>' + esc(p.blurb) + '</p>' + (est ? '<p class="estimate">' + esc(est) + '</p>' : '') + '<span class="arrow">View project &rarr;</span></a>';
  });
  h += '</div>';
  if (projects.length > ps.length) h += '<p style="margin-top:1rem">Showing ' + ps.length + ' of ' + projects.length + ' projects.</p>';
  return h + members(people, 'coding');
}

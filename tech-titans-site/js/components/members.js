import { pcard } from './cards.js';

export function members(people, dept) {
  var list = people.filter(function (p) { return p.dept === dept; });
  if (!list.length) return '';
  var t = list.filter(function (p) { return p.teacher; });
  var s = list.filter(function (p) { return !p.teacher; });
  var h = '<h2>Members</h2>';
  if (t.length) h += '<h3 style="margin-bottom:.6rem">Teacher-in-charge</h3><div class="people">' + t.map(pcard).join('') + '</div>';
  if (s.length) h += '<h3 style="margin:1.3rem 0 .6rem">Students</h3><div class="people">' + s.map(pcard).join('') + '</div>';
  return h;
}

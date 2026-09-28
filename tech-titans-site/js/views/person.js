import { esc } from '../utils.js';

export function vPerson(p) {
  return '<a class="back" href="/' + p.dept + '/">&larr; Back to department</a><div class="eyebrow">' + esc(p.role) + '</div><h1>' + esc(p.name) + '</h1>' +
    '<p class="lead">' + esc(p.bio) + '</p><ul class="meta" style="max-width:420px"><li><b>Department</b><span>' + esc(p.dept) + '</span></li><li><b>Role</b><span>' + esc(p.role) + '</span></li></ul>';
}

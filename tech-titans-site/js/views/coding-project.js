import { esc } from '../utils.js';
import { CODING_STAGES } from '../data/config.js';
import { progressBar, progressSteps } from '../components/progress.js';
import { estimateLine } from '../estimate.js';

export function vCodingProject(p) {
  var unfinished = p.status === 'unfinished';

  var h = '<a class="back" href="/coding/">&larr; Coding Team</a><div class="eyebrow">Project</div><h1>' + esc(p.title) + '</h1>';

  if (unfinished) {
    h += '<div class="note bad"><p><b>Still in progress</b> — this project isn&rsquo;t finished yet. Some things may not work as expected.</p></div>';
  }

  h += '<span class="tag ' + (unfinished ? 't-warn' : 't-ok') + '">' + (unfinished ? 'In progress' : 'Finished') + '</span>';
  h += '<h2>About</h2><p class="lead">' + esc(p.description) + '</p>';
  h += '<h2>How to use it</h2><p class="lead">' + esc(p.howToUse) + '</p>';

  h += '<div class="btns">';
  if (p.githubUrl) h += '<a class="btn" href="' + esc(p.githubUrl) + '" target="_blank" rel="noopener">View on GitHub &rarr;</a>';
  if (p.websiteUrl) h += '<a class="btn ghost" href="' + esc(p.websiteUrl) + '" target="_blank" rel="noopener">Open website &rarr;</a>';
  h += '</div>';

  if (unfinished) {
    var stage = p.stage || 0;
    var est = estimateLine(p.estimatedRelease);
    h += '<h2>Progress</h2>' + (est ? '<p class="estimate">' + esc(est) + '</p>' : '') + progressBar(CODING_STAGES, stage) + progressSteps(CODING_STAGES, stage);
  }

  return h;
}

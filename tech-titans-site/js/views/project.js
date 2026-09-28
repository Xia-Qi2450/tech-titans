import { esc } from '../utils.js';
import { group, setEpisodeSource } from '../components/episode.js';

// Takes the already-fetched project object directly -- no lookup here,
// the page script fetched exactly this one project from the API.
export function vProject(p) {
  setEpisodeSource(p.episodes, p.title);

  var ok = p.status === 'active';
  var h = '<a class="back" href="/production/">&larr; Production Team</a><div class="eyebrow">Project</div><h1>' + esc(p.title) + '</h1>' +
    '<span class="tag ' + (ok ? 't-ok' : 't-warn') + '">' + (ok ? 'Active' : 'Planned') + '</span><p class="lead">' + esc(p.about) + '</p>';

  var airing = p.episodes.filter(function (e) { return e.state === 'airing'; });
  var aired = p.episodes.filter(function (e) { return e.state === 'aired'; });
  var production = p.episodes.filter(function (e) { return e.state === 'production'; });

  h += '<h2>Episode tracker</h2>' + group('Currently airing', airing) + group('Already aired', aired) + group('In production', production);

  if (p.formUrl) {
    h += '<div class="note"><p>This show runs on student submissions — send us something and we\'ll queue it for an episode.</p></div>' +
         '<div class="btns"><a class="btn" href="' + esc(p.formUrl) + '" target="_blank" rel="noopener">Submit an idea &rarr;</a></div>';
  }
  return h;
}

import { $, esc } from '../utils.js';
import { vProject } from '../views/project.js';
import { vProjectNotFound } from '../views/notfound.js';
import { openEp } from '../components/episode.js';
import { hideLoader } from '../loader.js';
import { fetchProductionProject } from '../api.js';

var slug = new URLSearchParams(location.search).get('production');

(async function () {
  if (!slug) {
    // No project specified — send them to the department page instead of showing an empty template.
    location.replace('/production/');
    return;
  }
  try {
    var project = await fetchProductionProject(slug);
    $('#app').innerHTML = vProject(project);
    document.title = $('#app h1').textContent + ' — Tech Titans';
  } catch (err) {
    if (err.status === 404) {
      $('#app').innerHTML = vProjectNotFound(slug);
      document.title = 'Project not found — Tech Titans';
    } else {
      $('#app').innerHTML = '<h1>Couldn&rsquo;t load this project</h1><p>' + esc(err.message) + ' &mdash; is the API running?</p>';
    }
  }
  hideLoader();
})();

// Episode cards on this page open the synopsis/video modal.
document.addEventListener('click', function (e) {
  var ep = e.target.closest('[data-ep]');
  if (ep) openEp(ep.getAttribute('data-ep'));
});

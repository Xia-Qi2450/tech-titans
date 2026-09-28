import { $, esc } from '../utils.js';
import { vCodingProject } from '../views/coding-project.js';
import { vCodingProjectNotFound } from '../views/notfound.js';
import { hideLoader } from '../loader.js';
import { fetchCodingProject } from '../api.js';

var slug = new URLSearchParams(location.search).get('coding');

(async function () {
  if (!slug) {
    location.replace('/coding/');
    return;
  }
  try {
    var project = await fetchCodingProject(slug);
    $('#app').innerHTML = vCodingProject(project);
    document.title = $('#app h1').textContent + ' — Tech Titans';
  } catch (err) {
    if (err.status === 404) {
      $('#app').innerHTML = vCodingProjectNotFound(slug);
      document.title = 'Project not found — Tech Titans';
    } else {
      $('#app').innerHTML = '<h1>Couldn&rsquo;t load this project</h1><p>' + esc(err.message) + ' &mdash; is the API running?</p>';
    }
  }
  hideLoader();
})();

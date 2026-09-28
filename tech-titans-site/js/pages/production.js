import { $, esc } from '../utils.js';
import { vProduction } from '../views/production.js';
import { hideLoader } from '../loader.js';
import { fetchProductionProjects, fetchPeople } from '../api.js';

(async function () {
  try {
    var results = await Promise.all([fetchProductionProjects(), fetchPeople()]);
    $('#app').innerHTML = vProduction(results[0], results[1]);
  } catch (err) {
    $('#app').innerHTML = '<h1>Couldn&rsquo;t load this page</h1><p>' + esc(err.message) + ' &mdash; is the API running?</p>';
  }
  hideLoader();
})();

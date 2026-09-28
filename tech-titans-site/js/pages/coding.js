import { $, esc } from '../utils.js';
import { vCoding } from '../views/coding.js';
import { hideLoader } from '../loader.js';
import { fetchCodingProjects, fetchPeople } from '../api.js';

(async function () {
  try {
    var results = await Promise.all([fetchCodingProjects(), fetchPeople()]);
    $('#app').innerHTML = vCoding(results[0], results[1]);
  } catch (err) {
    $('#app').innerHTML = '<h1>Couldn&rsquo;t load this page</h1><p>' + esc(err.message) + ' &mdash; is the API running?</p>';
  }
  hideLoader();
})();

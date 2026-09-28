import { $, esc } from '../utils.js';
import { vPerson } from '../views/person.js';
import { v404 } from '../views/notfound.js';
import { hideLoader } from '../loader.js';
import { fetchPerson } from '../api.js';

var slug = new URLSearchParams(location.search).get('person');

(async function () {
  if (!slug) {
    location.replace('/');
    return;
  }
  try {
    var person = await fetchPerson(slug);
    $('#app').innerHTML = vPerson(person);
    document.title = $('#app h1').textContent + ' — Tech Titans';
  } catch (err) {
    if (err.status === 404) {
      $('#app').innerHTML = v404();
    } else {
      $('#app').innerHTML = '<h1>Couldn&rsquo;t load this person</h1><p>' + esc(err.message) + ' &mdash; is the API running?</p>';
    }
  }
  hideLoader();
})();

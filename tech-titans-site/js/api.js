// Local dev default: the API runs as a separate Flask process on this
// port, the site as a separate static server on its own port. Change this
// one constant once real hosting is decided (same origin, subdomain,
// whatever) -- nothing else in the site should need to change.
var API_BASE = 'http://localhost:5000';

async function apiGet(path) {
  var res = await fetch(API_BASE + path);
  if (!res.ok) {
    var err = new Error('API ' + path + ' returned ' + res.status);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export function fetchPeople() {
  return apiGet('/api/people');
}

export function fetchPerson(slug) {
  return apiGet('/api/people/' + encodeURIComponent(slug));
}

export function fetchProductionProjects() {
  return apiGet('/api/production/projects');
}

export function fetchProductionProject(slug) {
  return apiGet('/api/production/projects/' + encodeURIComponent(slug));
}

export function fetchCodingProjects() {
  return apiGet('/api/coding/projects');
}

export function fetchCodingProject(slug) {
  return apiGet('/api/coding/projects/' + encodeURIComponent(slug));
}

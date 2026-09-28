function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
  });
}

async function loadPeople() {
  var res = await fetch('/api/people');
  if (!res.ok) throw new Error('Server returned ' + res.status);
  return res.json();
}

function personCard(p) {
  return (
    '<div class="card" data-slug="' + esc(p.slug) + '">' +
      '<div class="rowtop"><h3>' + esc(p.name) + '</h3>' +
        (p.teacher ? '<span class="tag t-ok">Teacher</span>' : '<span class="tag t-idle">Student</span>') +
      '</div>' +
      '<p class="ref"><b>Slug</b> ' + esc(p.slug) + ' &middot; not editable here</p>' +
      '<div class="field"><label>Name</label><input type="text" class="f-name" value="' + esc(p.name) + '"></div>' +
      '<div class="field"><label>Role</label><input type="text" class="f-role" value="' + esc(p.role || '') + '"></div>' +
      '<div class="field"><label>Department</label><input type="text" class="f-dept" value="' + esc(p.dept) + '"></div>' +
      '<div class="check">' +
        '<input type="checkbox" class="f-teacher" id="teacher-' + esc(p.slug) + '"' + (p.teacher ? ' checked' : '') + '>' +
        '<div class="checkwrap"><label for="teacher-' + esc(p.slug) + '">Teacher-in-charge</label></div>' +
      '</div>' +
      '<div class="field"><label>Bio</label><textarea class="f-bio">' + esc(p.bio || '') + '</textarea></div>' +
      '<div class="actions">' +
        '<button class="btn" data-save>Save</button>' +
        '<button class="btn ghost" data-delete>Delete</button>' +
        '<span class="status"></span>' +
      '</div>' +
    '</div>'
  );
}

function createFormHtml() {
  return (
    '<div class="card">' +
      '<h3 style="font-family:var(--head);margin:0 0 .8rem">Add a person</h3>' +
      '<div class="field"><label for="new-slug">Slug (unique, e.g. "jamie-tan")</label><input type="text" id="new-slug"></div>' +
      '<div class="field"><label for="new-name">Name</label><input type="text" id="new-name"></div>' +
      '<div class="field"><label for="new-role">Role</label><input type="text" id="new-role"></div>' +
      '<div class="field"><label for="new-dept">Department</label><input type="text" id="new-dept" placeholder="production, coding, ..."></div>' +
      '<div class="check">' +
        '<input type="checkbox" id="new-teacher">' +
        '<div class="checkwrap"><label for="new-teacher">Teacher-in-charge</label></div>' +
      '</div>' +
      '<div class="field"><label for="new-bio">Bio</label><textarea id="new-bio"></textarea></div>' +
      '<div class="actions"><button class="btn" id="createBtn">Add person</button><span class="status" id="createStatus"></span></div>' +
    '</div>'
  );
}

function readCard(card) {
  return {
    name: card.querySelector('.f-name').value,
    role: card.querySelector('.f-role').value,
    dept: card.querySelector('.f-dept').value,
    teacher: card.querySelector('.f-teacher').checked,
    bio: card.querySelector('.f-bio').value,
  };
}

async function saveExisting(card) {
  var slug = card.getAttribute('data-slug');
  var statusEl = card.querySelector('.status');
  var btn = card.querySelector('[data-save]');
  btn.disabled = true;
  statusEl.textContent = 'Saving\u2026';
  statusEl.className = 'status';
  try {
    var res = await fetch('/api/people/' + encodeURIComponent(slug), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(readCard(card)),
    });
    if (!res.ok) throw new Error('Server returned ' + res.status);
    statusEl.textContent = 'Saved';
    statusEl.className = 'status ok';
  } catch (err) {
    statusEl.textContent = 'Couldn\u2019t save \u2014 ' + err.message;
    statusEl.className = 'status err';
  } finally {
    btn.disabled = false;
  }
}

async function deleteExisting(card) {
  var slug = card.getAttribute('data-slug');
  if (!confirm('Delete ' + slug + '? This can\u2019t be undone.')) return;
  var statusEl = card.querySelector('.status');
  try {
    var res = await fetch('/api/people/' + encodeURIComponent(slug), { method: 'DELETE' });
    if (!res.ok) throw new Error('Server returned ' + res.status);
    card.remove();
  } catch (err) {
    statusEl.textContent = 'Couldn\u2019t delete \u2014 ' + err.message;
    statusEl.className = 'status err';
  }
}

async function createPerson() {
  var statusEl = document.getElementById('createStatus');
  var btn = document.getElementById('createBtn');
  var payload = {
    slug: document.getElementById('new-slug').value.trim(),
    name: document.getElementById('new-name').value.trim(),
    role: document.getElementById('new-role').value,
    dept: document.getElementById('new-dept').value.trim(),
    teacher: document.getElementById('new-teacher').checked,
    bio: document.getElementById('new-bio').value,
  };
  if (!payload.slug || !payload.name || !payload.dept) {
    statusEl.textContent = 'Slug, name, and department are required.';
    statusEl.className = 'status err';
    return;
  }
  btn.disabled = true;
  statusEl.textContent = 'Adding\u2026';
  statusEl.className = 'status';
  try {
    var res = await fetch('/api/people', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    var body = await res.json();
    if (!res.ok) throw new Error(body.error || ('Server returned ' + res.status));
    document.getElementById('app').insertAdjacentHTML('beforeend', personCard(payload));
    ['new-slug', 'new-name', 'new-role', 'new-dept', 'new-bio'].forEach(function (id) { document.getElementById(id).value = ''; });
    document.getElementById('new-teacher').checked = false;
    statusEl.textContent = 'Added';
    statusEl.className = 'status ok';
  } catch (err) {
    statusEl.textContent = 'Couldn\u2019t add \u2014 ' + err.message;
    statusEl.className = 'status err';
  } finally {
    btn.disabled = false;
  }
}

async function init() {
  document.getElementById('createWrap').innerHTML = createFormHtml();
  document.getElementById('createBtn').addEventListener('click', createPerson);

  var app = document.getElementById('app');
  var people;
  try {
    people = await loadPeople();
  } catch (err) {
    app.innerHTML = '<p class="empty">Couldn\u2019t load data \u2014 is the Flask server running? (' + esc(err.message) + ')</p>';
    return;
  }
  app.innerHTML = people.length ? people.map(personCard).join('') : '<p class="empty">No one added yet.</p>';

  app.addEventListener('click', function (e) {
    var card = e.target.closest('.card');
    if (!card) return;
    if (e.target.closest('[data-save]')) saveExisting(card);
    if (e.target.closest('[data-delete]')) deleteExisting(card);
  });
}

init();

var STAGE_LABELS = ['Not started', 'Idea thought', 'Writing script', 'Recording footage', 'Editing video', 'Finalising production', 'Finished'];

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
  });
}

async function loadAll() {
  var projects = await fetch('/api/production/projects').then(function (r) { return r.json(); });
  var details = await Promise.all(
    projects.map(function (p) {
      return fetch('/api/admin/production/projects/' + encodeURIComponent(p.slug)).then(function (r) { return r.json(); });
    })
  );
  return details;
}

function stageTag(ep) {
  if (ep.state === 'aired') return '<span class="tag t-ok">Aired</span>';
  var label = STAGE_LABELS[ep.stage] !== undefined ? STAGE_LABELS[ep.stage] : 'Unknown stage';
  var cls = ep.stage >= 5 ? 't-ok' : ep.stage === 0 ? 't-idle' : 't-warn';
  return '<span class="tag ' + cls + '">Stage ' + ep.stage + ': ' + esc(label) + '</span>';
}

function refLine(ep) {
  if (ep.state === 'aired') {
    return '<p class="ref">Published' + (ep.estimatedPublishDate ? ' &middot; target was ' + esc(ep.estimatedPublishDate) : '') + '</p>';
  }
  var parts = [
    '<b>Script</b> ' + esc(ep.scriptStatus),
    '<b>Recording</b> ' + esc(ep.recordingStatus),
    '<b>Editing</b> ' + esc(ep.editingStatus),
    '<b>Ready</b> ' + esc(ep.readyStatus),
  ];
  if (ep.priority) parts.push('<b>Priority</b> ' + esc(ep.priority));
  if (ep.estimatedFinishDate) parts.push('<b>Target finish</b> ' + esc(ep.estimatedFinishDate));
  if (ep.estimatedPublishDate) parts.push('<b>Target publish</b> ' + esc(ep.estimatedPublishDate));
  return '<p class="ref">' + parts.join(' &middot; ') + '</p>';
}

function episodeCard(ep) {
  var canFinalise = ep.editingStatus === 'Completed';
  return (
    '<div class="card" data-episode="' + ep.id + '">' +
      '<div class="rowtop"><h3>' + esc(ep.title) + '</h3>' + stageTag(ep) + '</div>' +
      refLine(ep) +
      '<div class="check">' +
        '<input type="checkbox" id="idea-' + ep.id + '"' + (ep.ideaApproved ? ' checked' : '') + '>' +
        '<div class="checkwrap"><label for="idea-' + ep.id + '">Idea approved by teacher</label></div>' +
      '</div>' +
      '<div class="check">' +
        '<input type="checkbox" id="final-' + ep.id + '"' + (ep.finalisingApproved ? ' checked' : '') + (canFinalise ? '' : ' disabled') + '>' +
        '<div class="checkwrap">' +
          '<label for="final-' + ep.id + '"' + (canFinalise ? '' : ' class="disabled"') + '>Sent for teacher\u2019s final review</label>' +
          (canFinalise ? '' : '<small>Enabled once editing is marked Completed on the sheet.</small>') +
        '</div>' +
      '</div>' +
      '<div class="field">' +
        '<label for="syn-' + ep.id + '">Synopsis</label>' +
        '<textarea id="syn-' + ep.id + '">' + esc(ep.synopsis) + '</textarea>' +
      '</div>' +
      '<div class="field">' +
        '<label for="drive-' + ep.id + '">Google Drive file ID</label>' +
        '<input type="text" id="drive-' + ep.id + '" value="' + esc(ep.driveId) + '" placeholder="the ID from the Drive share link, not the whole URL">' +
      '</div>' +
      '<div class="actions">' +
        '<button class="btn" data-save="' + ep.id + '">Save</button>' +
        '<span class="status" id="status-' + ep.id + '"></span>' +
      '</div>' +
    '</div>'
  );
}

function renderProject(project) {
  var inProd = project.episodes.filter(function (e) { return e.state !== 'aired'; });
  var aired = project.episodes.filter(function (e) { return e.state === 'aired'; });
  var html = '<div class="projgroup"><h2>' + esc(project.title) + '</h2>';
  if (!project.episodes.length) html += '<p class="empty">No episodes yet.</p>';
  html += inProd.map(episodeCard).join('');
  html += aired.map(episodeCard).join('');
  html += '</div>';
  return html;
}

async function saveEpisode(id) {
  var statusEl = document.getElementById('status-' + id);
  var btn = document.querySelector('[data-save="' + id + '"]');
  var payload = {
    ideaApproved: document.getElementById('idea-' + id).checked,
    finalisingApproved: document.getElementById('final-' + id).checked,
    synopsis: document.getElementById('syn-' + id).value,
    driveId: document.getElementById('drive-' + id).value,
  };
  btn.disabled = true;
  statusEl.textContent = 'Saving\u2026';
  statusEl.className = 'status';
  try {
    var res = await fetch('/api/production/episodes/' + id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
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

async function init() {
  var app = document.getElementById('app');
  var projects;
  try {
    projects = await loadAll();
  } catch (err) {
    app.innerHTML = '<p class="empty">Couldn\u2019t load data \u2014 is the Flask server running? (' + esc(err.message) + ')</p>';
    return;
  }
  if (!projects.length) {
    app.innerHTML = '<p class="empty">No production projects yet.</p>';
    return;
  }
  app.innerHTML = projects.map(renderProject).join('');
  app.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-save]');
    if (btn) saveEpisode(btn.getAttribute('data-save'));
  });
}

init();

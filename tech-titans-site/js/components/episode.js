import { $, esc, copyText } from '../utils.js';
import { STAGES } from '../data/config.js';
import { progressBar, progressSteps } from './progress.js';
import { estimateLine } from '../estimate.js';

export function bar(st) {
  return progressBar(STAGES, st);
}

export function steps(st) {
  return progressSteps(STAGES, st);
}

function stateMeta(state) {
  if (state === 'airing') return { cls: 't-ok', label: 'Airing now' };
  if (state === 'aired') return { cls: 't-idle', label: 'Aired' };
  return { cls: 't-warn', label: 'In production' };
}

function estLine(e) {
  var text = estimateLine(e.estimatedRelease);
  return text ? '<p class="estimate">' + esc(text) + '</p>' : '';
}

// The click handler for an episode card fires later, async, well after
// the initial render -- so it can't just close over a local array the way
// a synchronous render could. The page script hands the current project's
// episodes here once, after fetching; openEp() reads from this instead of
// looking anything up globally.
var currentEpisodes = [];
var currentProjectTitle = '';

export function setEpisodeSource(episodes, projectTitle) {
  currentEpisodes = episodes || [];
  currentProjectTitle = projectTitle || '';
}

export function group(label, episodes) {
  if (!episodes.length) return '';
  var h = '<h3 style="margin-top:1.6rem">' + label + '</h3><div class="grid" style="margin-top:.7rem">';
  episodes.forEach(function (e) {
    var m = stateMeta(e.state);
    h += '<button class="card" data-ep="' + e.id + '"><span class="tag ' + m.cls + '">' + m.label + '</span><h3>' + esc(e.title) + '</h3>' +
         (e.state === 'production' ? bar(e.stage || 0) + estLine(e) : '<p>Open for synopsis and video.</p>') + '</button>';
  });
  return h + '</div>';
}

function embed(id) {
  if (!id) return '<div class="embed"><div class="ph">No video linked yet for this episode.</div></div>';
  return '<div class="embed"><iframe src="https://drive.google.com/file/d/' + esc(id) + '/preview" allow="autoplay" allowfullscreen title="Episode video"></iframe></div>';
}

function hasRealDrive(id) {
  return !!id;
}

function driveViewUrl(id) {
  return 'https://drive.google.com/file/d/' + id + '/view';
}

// The dialog element is static and reused for every episode -- openEp()
// only ever rewrites #dlgBody. That means the fix belongs here, once,
// rather than in openEp(): whenever the dialog closes, by ANY method (X
// button, Escape, or a backdrop click), wipe #dlgBody so any embedded
// iframe is actually removed from the DOM, not just hidden.
var dlg = $('#dlg');
if (dlg) {
  dlg.addEventListener('close', function () {
    $('#dlgBody').innerHTML = '';
  });
  dlg.addEventListener('click', function (e) {
    if (e.target === dlg) dlg.close();
  });
}

export function openEp(id) {
  var e = currentEpisodes.filter(function (ep) { return String(ep.id) === String(id); })[0];
  if (!e) return;
  var m = stateMeta(e.state);
  var canCopy = e.state !== 'production' && hasRealDrive(e.drive);

  var h = '<button class="x" id="xBtn" aria-label="Close">&#10005;</button>' +
          '<div class="eyebrow">' + esc(currentProjectTitle) + '</div>' +
          '<span class="tag ' + m.cls + '">' + m.label + '</span>' +
          '<h1 style="font-size:1.45rem">' + esc(e.title) + '</h1><p>' + esc(e.synopsis || 'No synopsis yet.') + '</p>' +
          (e.state === 'production' ? '<h3>Production progress</h3>' + estLine(e) + bar(e.stage || 0) + steps(e.stage || 0) : embed(e.drive)) +
          (canCopy ? '<div class="btns"><button class="btn ghost" id="copyBtn" type="button">Copy Drive link</button></div>' : '');

  $('#dlgBody').innerHTML = h;
  var dialog = $('#dlg');
  dialog.showModal();

  var xBtn = $('#xBtn');
  xBtn.onclick = function () { dialog.close(); };
  xBtn.focus();

  if (canCopy) {
    var cb = $('#copyBtn');
    cb.onclick = function () {
      copyText(driveViewUrl(e.drive)).then(function () {
        cb.textContent = 'Copied!';
      }).catch(function () {
        cb.textContent = "Couldn't copy - copy manually";
      }).then(function () {
        setTimeout(function () { cb.textContent = 'Copy Drive link'; }, 1600);
      });
    };
  }
}

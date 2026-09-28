// Deliberately not a live countdown. A per-second ticker implies a
// precision this team can't actually promise for a volunteer schedule, and
// recomputing once per page load reads exactly the same to a visitor as
// live-ticking would for anything on a weekly-or-slower cadence.
export function estimateLine(iso){
  if(!iso || /REPLACE/.test(iso)) return '';
  var target = new Date(iso).getTime();
  if(isNaN(target)) return '';
  var diff = target - Date.now();
  if(diff <= 0) return 'Expected soon';
  return 'Releases ' + relative(diff) + ' \u00b7 ' + formatDate(target);
}

function relative(diff){
  var hour = 3600000, day = 86400000, week = day * 7;
  if(diff < hour) return 'in under an hour';
  if(diff < day) return plural(Math.round(diff / hour), 'hour');
  if(diff < week * 2) return plural(Math.round(diff / day), 'day');
  return plural(Math.round(diff / week), 'week');
}

function plural(n, unit){
  return 'in about ' + n + ' ' + unit + (n === 1 ? '' : 's');
}

function formatDate(ms){
  return new Date(ms).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
}

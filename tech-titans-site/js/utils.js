export function $(s, r){ return (r || document).querySelector(s); }

export function esc(s){
  return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
  });
}

// Turns a name into up-to-2-letter initials for the avatar circle.
// Strips a leading "REPLACE" placeholder so unfilled data doesn't show "RT".
export function initials(n){
  return n.replace(/REPLACE\s*/, '').trim().split(/\s+/).slice(0, 2)
    .map(function(w){ return w.charAt(0); }).join('').toUpperCase() || '?';
}

// navigator.clipboard needs a secure context (https, or localhost) and isn't
// always present. Falls back to the old execCommand trick so "copy link"
// buttons still work when testing over plain http.
export function copyText(str){
  if(navigator.clipboard && navigator.clipboard.writeText){
    return navigator.clipboard.writeText(str);
  }
  return new Promise(function(resolve, reject){
    try {
      var ta = document.createElement('textarea');
      ta.value = str;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      var ok = document.execCommand('copy');
      document.body.removeChild(ta);
      ok ? resolve() : reject(new Error('execCommand copy failed'));
    } catch(err){ reject(err); }
  });
}

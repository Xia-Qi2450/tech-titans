// All content on this site renders synchronously (no network fetch), so the
// loader would otherwise flash for a few ms and disappear. Forcing it to
// stay up for at least MIN_VISIBLE_MS is a deliberate design choice, not a
// performance workaround.
var MIN_VISIBLE_MS = 700;

export function hideLoader(){
  var loader = document.getElementById('loader');
  if(!loader) return;
  // performance.now() here is already "ms since navigation start" - exactly
  // the elapsed time we need, no separate timer to set up.
  var wait = Math.max(0, MIN_VISIBLE_MS - performance.now());
  setTimeout(function(){
    loader.classList.add('loader-hide');
    // Not relying on transitionend: prefers-reduced-motion strips the CSS
    // transition entirely, which would mean the event never fires and the
    // loader is left sitting in the DOM (invisible but still there).
    setTimeout(function(){ if(loader.parentNode) loader.remove(); }, 260);
  }, wait);
}

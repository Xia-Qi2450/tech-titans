export function vStub(title, lead, tag){
  return '<a class="back" href="/">&larr; All departments</a><div class="eyebrow">Department</div><h1>' + title + '</h1>' +
    (tag ? '<span class="tag t-idle">' + tag + '</span>' : '') + '<p class="lead">' + lead + '</p>' +
    '<div class="note"><p>This department page is next up — project list, detail pages and members work the same way as Production.</p></div>';
}

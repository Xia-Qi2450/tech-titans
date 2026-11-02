import { esc, initials } from '../utils.js';

export function dcard(path, t, tl, h, p, a){
  return '<a class="card" href="' + path + '"><span class="tag ' + t + '">' + tl + '</span><h3>' + h + '</h3><p>' + p + '</p><span class="arrow">' + a + ' &rarr;</span></a>';
}

export function pcard(p){
  return '<a class="person" href="/people/view/?person=' + encodeURIComponent(p.slug) + '"><span class="av">' + esc(initials(p.name)) + '</span><span>' + esc(p.name) + '<small>' + esc(p.role) + '</small></span></a>';
}

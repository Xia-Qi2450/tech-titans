import { esc } from '../utils.js';

export function v404(){
  return '<h1>Page not found</h1><p>That page doesn&rsquo;t exist.</p><div class="btns"><a class="btn" href="/">Go home</a></div>';
}

export function vProjectNotFound(slug){
  return '<a class="back" href="/production/">&larr; Production Team</a><h1>Project not found</h1>' +
    '<p>There&rsquo;s no production project called &ldquo;' + esc(slug) + '&rdquo;.</p>' +
    '<div class="btns"><a class="btn" href="/production/">Back to Production</a></div>';
}

export function vCodingProjectNotFound(slug){
  return '<a class="back" href="/coding/">&larr; Coding Team</a><h1>Project not found</h1>' +
    '<p>There&rsquo;s no coding project called &ldquo;' + esc(slug) + '&rdquo;.</p>' +
    '<div class="btns"><a class="btn" href="/coding/">Back to Coding</a></div>';
}

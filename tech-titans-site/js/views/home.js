import { dcard } from '../components/cards.js';

export function vHome(){
  return '<div class="hero"><div class="eyebrow">Student-led technology group</div><h1>Tech Titans</h1>' +
  '<p class="lead">Three departments, one goal: use technology to make school life better - through programmes students want to watch, tools teachers actually use, and models you can hold in your hand.</p></div>' +
  '<h2>Our departments</h2><div class="grid">' +
  dcard('/production/', 't-ok', 'Active', 'Production Team', 'Video podcasts and original programmes - discussion shows, interviews and student-submitted segments.', 'See projects and episodes') +
  dcard('/coding/', 't-ok', 'Active', 'Coding Team', 'Programs and web pages built for teachers and the student body, solving real problems around school.', 'See projects') +
  dcard('/printing/', 't-idle', 'Forming', '3D Printing Team', 'Printing models for teachers and showing the school what 3D printing can actually do.', 'Not yet officially formed') +
  '</div>';
}

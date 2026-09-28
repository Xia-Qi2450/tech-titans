import { esc } from '../utils.js';

export function progressBar(stages, st){
  var pct = Math.round(st / (stages.length - 1) * 100);
  return '<div class="bar"><i style="width:' + pct + '%"></i></div><p style="font-size:.84rem">' + esc(stages[st]) + '</p>';
}

export function progressSteps(stages, st){
  return '<ul class="steps">' + stages.map(function(s, i){
    return '<li class="' + (i < st ? 'done' : i === st ? 'cur' : '') + '"><span class="dot"></span>' + s + '</li>';
  }).join('') + '</ul>';
}

import { $ } from '../utils.js';
import { vHome } from '../views/home.js';
import { hideLoader } from '../loader.js';

$('#app').innerHTML = vHome();
hideLoader();

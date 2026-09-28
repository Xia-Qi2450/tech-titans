import { $ } from '../utils.js';
import { vStub } from '../views/stub.js';
import { hideLoader } from '../loader.js';

$('#app').innerHTML = vStub('3D Printing Team', 'A planned department focused on printing models for teachers and showcasing the wonders of 3D printing across the school.', 'Not yet officially formed');
hideLoader();

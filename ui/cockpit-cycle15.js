/* Cycle-15 designer goals 2-9. Same /api/fleet/cockpit feed as cockpit.js;
inserts sections after the mode banner of #ckpPanel.
*/
(function () {
  "use strict";
  var API = "/api/fleet/cockpit";
  var RM = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

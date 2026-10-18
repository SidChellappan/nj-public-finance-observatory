"use strict";

const caseStudyMenu = document.querySelector(".case-study-menu");
if (caseStudyMenu) {
  document.addEventListener("click", (event) => {
    if (!caseStudyMenu.contains(event.target)) caseStudyMenu.open = false;
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && caseStudyMenu.open) {
      caseStudyMenu.open = false;
      caseStudyMenu.querySelector("summary").focus();
    }
  });
}

// Keep previously shared home-page section links useful after the page split.
const legacyPages = {
  "#observations": "observations.html",
  "#latest-title": "observations.html",
  "#limits": "limits.html",
  "#gaps": "gaps.html",
  "#downloads": "downloads.html",
  "#corrections": "corrections.html",
};
const filename = window.location.pathname.split("/").pop();
if ((filename === "" || filename === "index.html") && legacyPages[window.location.hash]) {
  window.location.replace(legacyPages[window.location.hash]);
}
if (filename === "methods.html" && window.location.hash === "#corrections") {
  window.location.replace("corrections.html");
}

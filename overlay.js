// overlays.js
//
// Creates overlay layers and exposes a global function to set them:
//
//   window.toeApplyOverlayTypes(bgType, topType)
//
// bgType:  "none" | "snow" | "dust" | "fire"
// topType: "none" | "scanlines" | "grain"
//
(function () {
  function createOverlay(id) {
    let el = document.getElementById(id);
    if (!el) {
      el = document.createElement("div");
      el.id = id;
      el.className = "overlay-layer";
      if (document.body.firstChild) {
        document.body.insertBefore(el, document.body.firstChild);
      } else {
        document.body.appendChild(el);
      }
    }
    return el;
  }

  function ensureFireVideo(parent) {
    if (!parent) return;

    let video = parent.querySelector(".overlay-fire-video");
    if (!video) {
      video = document.createElement("video");
      video.className = "overlay-fire-video";

      // IMPORTANT: root-relative path so it works from / and from /Books/.../
      video.src = "/overlays/fire-loop.mp4";

      video.autoplay = true;
      video.loop = true;
      video.muted = true;
      video.playsInline = true; // mobile-friendly
      parent.appendChild(video);
    }
  }

  function removeFireVideo(parent) {
    if (!parent) return;
    const video = parent.querySelector(".overlay-fire-video");
    if (video) {
      video.remove();
    }
  }

  function setOverlayClasses(bgType, topType) {
    const bgEl  = createOverlay("overlay-bg");
    const topEl = createOverlay("overlay-top");

    const bg  = bgType  || "none";
    const top = topType || "none";

    bgEl.className  = "overlay-layer overlay-bg-"  + bg;
    topEl.className = "overlay-layer overlay-top-" + top;

    if (bg === "fire") {
      ensureFireVideo(bgEl);
    } else {
      removeFireVideo(bgEl);
    }

    // simple debug so you can see it's being called
    if (window.console && console.debug) {
      console.debug("[overlays] apply", { bg, top });
    }
  }

  // Expose globally so reader (and later settings) can control overlays
  window.toeApplyOverlayTypes = function (bgType, topType) {
    setOverlayClasses(bgType, topType);
  };

  function init() {
    // default: no overlays
    setOverlayClasses("none", "none");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

"""Glass-layers hero: the portfolio photograph as a recessed back plane with the
six method steps floating in front as frosted panes.

Pure HTML/CSS 3D plus a few lines of pointer-parallax JavaScript (CCv2 inline
component). No external libraries. Motion is disabled for reduced-motion users
and on narrow screens the panes fall back to a flat stack.
"""

from __future__ import annotations


import streamlit as st


_HTML = """
<div class="stage">
  <div class="rig">
    <div class="photo"><img alt="" /></div>
    <div class="grade"></div>
    <div class="veil"></div>
    <div class="glint"><span></span></div>
    <div class="blocks"><span class="track"></span></div>
    <p class="label" role="heading" aria-level="2"></p>
    <ol class="panes" aria-label="Transformation method, six steps"></ol>
  </div>
</div>
"""

_CSS = """
:host { display: block; }
.stage {
  --rx: 0deg; --ry: 0deg;
  position: relative;
  height: 640px;
  perspective: 1400px;
  perspective-origin: 70% 45%;
  overflow: hidden;
  background: #08171A;
  isolation: isolate;
  font-family: "IBM Plex Sans", system-ui, sans-serif;
}
.rig {
  position: absolute; inset: 0;
  transform-style: preserve-3d;
  transform: rotateX(var(--rx)) rotateY(var(--ry));
  transition: transform 700ms cubic-bezier(0.22, 1, 0.36, 1);
}
/* Full photograph as the back wall: shallow depth so almost the whole frame stays visible. */
.photo, .grade, .veil, .glint { position: absolute; inset: -3%; pointer-events: none; }
.photo { transform: translateZ(-90px) scale(1.07); }
.photo img {
  width: 100%; height: 100%;
  object-fit: cover; object-position: 50% 50%;
  display: block;
  filter: brightness(1.14) contrast(1.04) saturate(1.06);
  animation: dolly 2000ms cubic-bezier(0.22, 1, 0.36, 1) both;
}
/* Gentle green tint (plain overlay: no blend mode, so it costs nothing per frame). */
.grade {
  transform: translateZ(-88px) scale(1.07);
  background: linear-gradient(90deg, rgb(11 58 46 / 16%) 0%, rgb(14 107 82 / 6%) 100%);
}
/* Readability veil for the headline on the left; fades into the ink chapter at the bottom. */
.veil {
  transform: translateZ(-86px) scale(1.07);
  background:
    linear-gradient(90deg, rgb(8 23 26 / 74%) 0%, rgb(8 23 26 / 50%) 26%, rgb(8 23 26 / 12%) 44%, rgb(8 23 26 / 0%) 56%),
    linear-gradient(180deg, rgb(8 23 26 / 18%) 0%, rgb(8 23 26 / 0%) 18%, rgb(8 23 26 / 0%) 72%, rgb(9 26 27 / 100%) 98%);
}
/* Recurring light sweep: a soft bar moved with transform only (GPU-composited). */
.glint { overflow: hidden; transform: translateZ(-84px) scale(1.07); }
.glint span {
  position: absolute; top: -10%; bottom: -10%; left: 0; width: 34%;
  background: linear-gradient(105deg, transparent 0%, rgb(255 255 255 / 10%) 50%, transparent 100%);
  transform: translateX(-120%);
  will-change: transform;
  animation: sweep 7s cubic-bezier(0.45, 0, 0.2, 1) 1600ms infinite;
}
/* Small ledger blocks drifting right to left: one wide tiled strip moved with transform. */
.blocks {
  position: absolute; top: 0; bottom: 0; left: 40%; right: 0;
  overflow: hidden;
  transform: translateZ(-30px);
  pointer-events: none;
  -webkit-mask-image: linear-gradient(90deg, transparent 0%, black 35%);
  mask-image: linear-gradient(90deg, transparent 0%, black 35%);
}
.blocks .track {
  position: absolute; top: 0; bottom: 0; left: 0;
  width: calc(100% + 720px);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cg fill='%2312B886'%3E%3Crect x='18' y='30' width='10' height='10' rx='2' opacity='.6'/%3E%3Crect x='120' y='96' width='14' height='14' rx='3' opacity='.35'/%3E%3Crect x='196' y='168' width='8' height='8' rx='2' opacity='.65'/%3E%3Crect x='70' y='200' width='12' height='12' rx='2' opacity='.3'/%3E%3C/g%3E%3C/svg%3E"), url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cg fill='white'%3E%3Crect x='160' y='40' width='6' height='6' rx='1.5' opacity='.5'/%3E%3Crect x='40' y='130' width='8' height='8' rx='2' opacity='.32'/%3E%3Crect x='210' y='210' width='5' height='5' rx='1' opacity='.45'/%3E%3C/g%3E%3C/svg%3E");
  background-size: 240px 240px, 360px 360px;
  opacity: 0.9;
  will-change: transform;
  animation: drift 56s linear infinite;
}
.panes {
  list-style: none; margin: 0; padding: 0;
  position: absolute; inset: 0;
  transform-style: preserve-3d;
}
.pane {
  --i: 0;
  position: absolute;
  left: calc(51% + var(--i) * 2.2%);
  top: calc(19% + var(--i) * 11.4%);
  width: 28%;
  min-width: 230px;
  height: 62px;
  display: flex; align-items: center; gap: 14px;
  padding: 0 18px;
  box-sizing: border-box;
  border-radius: 14px;
  color: #FFFFFF;
  background:
    linear-gradient(120deg, rgb(255 255 255 / 20%), rgb(255 255 255 / 6%)),
    rgb(10 34 30 / 34%);
  border: 1px solid rgb(255 255 255 / 30%);
  box-shadow: 0 22px 48px rgb(5 10 20 / 42%), inset 0 1px 0 rgb(255 255 255 / 38%);
  transform: translateZ(calc(var(--i) * 30px)) scale(calc(1 - var(--i) * 0.021429));
  transition: transform 420ms cubic-bezier(0.22, 1, 0.36, 1), background 300ms ease,
              border-color 300ms ease, box-shadow 300ms ease;
  animation: pane-in 1000ms cubic-bezier(0.22, 1, 0.36, 1) backwards;
  animation-delay: calc(450ms + var(--i) * 130ms);
  cursor: default;
  outline: none;
}
.pane .n {
  font-variant-numeric: tabular-nums;
  font-size: 12px; font-weight: 600; letter-spacing: 0.14em;
  color: #9FE6C9;
}
.pane .w { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.pane .t {
  font-family: "Bricolage Grotesque", "IBM Plex Sans", sans-serif;
  font-size: 18px; font-weight: 700; letter-spacing: -0.01em; line-height: 1.15;
}
.pane .s {
  font-size: 13px; line-height: 1.25; color: rgb(232 246 240 / 82%);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
/* Section label for the method, floating above the stack. */
.label {
  position: absolute; margin: 0;
  left: 50%; top: 6%;
  transform: translateZ(40px);
  font-family: "Bricolage Grotesque", "IBM Plex Sans", sans-serif;
  font-size: 21px; font-weight: 700; letter-spacing: -0.01em;
  color: #FFFFFF;
  padding: 10px 20px 10px 16px;
  border-radius: 999px;
  background: rgb(8 23 26 / 74%);
  border: 1px solid rgb(95 211 168 / 45%);
  animation: label-in 900ms cubic-bezier(0.22, 1, 0.36, 1) 300ms backwards;
}
.label::before {
  content: ""; display: inline-block; width: 7px; height: 7px; border-radius: 50%;
  background: #12B886; margin-right: 12px; vertical-align: 3px;
  box-shadow: 0 0 0 4px rgb(18 184 134 / 25%);
}
@keyframes label-in { from { opacity: 0; transform: translateZ(40px) translateY(-10px); } to { opacity: 1; transform: translateZ(40px); } }
.pane:hover, .pane:focus-visible {
  transform: translateZ(calc(var(--i) * 30px + 64px)) scale(calc(1 - var(--i) * 0.021429));
  background: linear-gradient(120deg, rgb(255 255 255 / 32%), rgb(255 255 255 / 12%));
  border-color: rgb(95 211 168 / 95%);
  box-shadow: 0 30px 60px rgb(5 10 20 / 50%), 0 0 0 3px rgb(18 184 134 / 50%);
}
@keyframes dolly {
  from { transform: scale(1.08); opacity: 0.4; }
  to { transform: scale(1); opacity: 1; }
}
@keyframes pane-in {
  from { opacity: 0; transform: translateZ(calc(var(--i) * 30px + 360px)) translateY(-20px) scale(calc(1 - var(--i) * 0.021429)); }
  to { opacity: 1; transform: translateZ(calc(var(--i) * 30px)) scale(calc(1 - var(--i) * 0.021429)); }
}
@keyframes sweep {
  0% { transform: translateX(-120%); }
  45%, 100% { transform: translateX(320%); }
}
@keyframes drift {
  from { transform: translateX(0); }
  to { transform: translateX(-720px); }
}
/* Nothing animates while the hero is off screen or the tab is hidden. */
.stage.is-idle .glint span, .stage.is-idle .blocks .track { animation-play-state: paused; }
@media (prefers-reduced-motion: reduce) {
  .photo img, .pane, .glint span, .blocks .track, .label { animation: none; }
  .rig, .pane { transition: none; }
}
@media (max-width: 900px) {
  .stage { height: auto; perspective: none; }
  .rig { position: relative; transform: none; }
  .photo, .grade, .veil, .glint { inset: 0; transform: none; }
  .blocks { transform: none; left: 0; }
  .photo img { object-position: 70% 50%; }
  .veil { background: linear-gradient(180deg, rgb(8 23 26 / 10%) 0%, rgb(8 23 26 / 80%) 100%); }
  .label { position: relative; left: auto; top: auto; transform: none; display: inline-block; margin: 180px 16px 10px; }
  .panes { position: relative; display: grid; gap: 8px; padding: 0 16px 16px; }
  .pane .s { white-space: normal; }
  .pane { position: relative; left: auto; top: auto; bottom: auto; width: auto; min-width: 0; height: auto; padding: 10px 16px; transform: none; animation: none; }
  .pane:hover, .pane:focus-visible { transform: none; }
}
"""

_JS = """
const instances = new WeakMap()

export default function (component) {
  const { data, parentElement } = component
  const stage = parentElement.querySelector(".stage")
  if (!stage) return

  const img = stage.querySelector(".photo img")
  if (data && data.image) {
    const src = new URL(data.image, document.baseURI).href
    if (img.src !== src) {
      img.decoding = "async"
      img.fetchPriority = "high"
      // If a proxy or base path breaks the relative URL, retry from the site root once.
      img.onerror = () => {
        const fallback = new URL(data.image.startsWith("/") ? data.image : "/" + data.image, window.location.origin).href
        if (img.src !== fallback) img.src = fallback
      }
      img.src = src
    }
  }

  const label = stage.querySelector(".label")
  const labelText = (data && data.label) || ""
  if (label.textContent !== labelText) label.textContent = labelText
  label.hidden = !labelText

  const list = stage.querySelector(".panes")
  const steps = (data && data.steps) || []
  if (list.childElementCount !== steps.length) {
    list.textContent = ""
    steps.forEach((step, i) => {
      const li = document.createElement("li")
      li.className = "pane"
      li.tabIndex = 0
      li.style.setProperty("--i", String(i))
      const n = document.createElement("span")
      n.className = "n"
      n.textContent = String(i + 1).padStart(2, "0")
      const verb = Array.isArray(step) ? step[0] : step
      const rest = Array.isArray(step) ? step[1] : ""
      const w = document.createElement("span")
      w.className = "w"
      const t = document.createElement("span")
      t.className = "t"
      t.textContent = verb
      w.append(t)
      if (rest) {
        const s = document.createElement("span")
        s.className = "s"
        s.textContent = rest
        w.append(s)
      }
      li.append(n, w)
      list.append(li)
    })
  }

  if (instances.has(parentElement)) return

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)")
  const narrow = window.matchMedia("(max-width: 900px)")
  let frame = 0
  const onMove = (event) => {
    if (reduce.matches || narrow.matches) return
    const box = stage.getBoundingClientRect()
    const x = (event.clientX - box.left) / box.width - 0.5
    const y = (event.clientY - box.top) / box.height - 0.5
    cancelAnimationFrame(frame)
    frame = requestAnimationFrame(() => {
      stage.style.setProperty("--ry", (x * 9).toFixed(2) + "deg")
      stage.style.setProperty("--rx", (-y * 6).toFixed(2) + "deg")
    })
  }
  const onLeave = () => {
    cancelAnimationFrame(frame)
    stage.style.setProperty("--ry", "0deg")
    stage.style.setProperty("--rx", "0deg")
  }
  stage.addEventListener("pointermove", onMove)
  stage.addEventListener("pointerleave", onLeave)
  let observer = null
  if ("IntersectionObserver" in window) {
    observer = new IntersectionObserver((entries) => {
      for (const entry of entries) stage.classList.toggle("is-idle", !entry.isIntersecting)
    })
    observer.observe(stage)
  }
  const onVisibility = () => stage.classList.toggle("is-idle", document.hidden)
  document.addEventListener("visibilitychange", onVisibility)
  instances.set(parentElement, true)

  return () => {
    stage.removeEventListener("pointermove", onMove)
    stage.removeEventListener("pointerleave", onLeave)
    document.removeEventListener("visibilitychange", onVisibility)
    if (observer) observer.disconnect()
    cancelAnimationFrame(frame)
    instances.delete(parentElement)
  }
}
"""

def _hero_component():
    # Registration is idempotent and cheap for inline strings. Registering on use
    # (not only at import) keeps the component available in every Streamlit
    # runtime, including the fresh runtimes created by AppTest.
    return st.components.v2.component("glass_layers_hero", html=_HTML, css=_CSS, js=_JS)


# Served by Streamlit static file serving, so the browser downloads and caches it once
# instead of receiving ~160 KB of base64 with every rerun of the Overview page.
_IMAGE_URL = "app/static/portfolio_hero.webp"


def glass_hero(steps: list[tuple[str, str]], *, label: str = "", key: str = "glass_hero") -> None:
    """Render the photograph with the method steps as floating glass panes under a label."""
    _hero_component()(
        data={"image": _IMAGE_URL, "steps": [list(step) for step in steps], "label": label},
        height="content",
        key=key,
    )

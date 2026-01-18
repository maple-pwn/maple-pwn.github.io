(() => {
  const MIN_WIDTH = 200;
  const MAX_WIDTH = 480;

  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

  const setWidth = (sidebar, width) => {
    const next = clamp(width, MIN_WIDTH, MAX_WIDTH);
    sidebar.style.width = `${next}px`;
    sidebar.style.flexBasis = `${next}px`;
  };

  const setupHandle = (sidebar, side) => {
    const handle = document.createElement("div");
    handle.className = "sidebar-resize-handle";
    sidebar.appendChild(handle);

    let startX = 0;
    let startWidth = 0;

    const onMove = (event) => {
      const dx = event.clientX - startX;
      const width = side === "primary" ? startWidth + dx : startWidth - dx;
      setWidth(sidebar, width);
    };

    const onUp = () => {
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerup", onUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    handle.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      handle.setPointerCapture(event.pointerId);
      startX = event.clientX;
      startWidth = sidebar.getBoundingClientRect().width;
      document.body.style.cursor = "ew-resize";
      document.body.style.userSelect = "none";
      document.addEventListener("pointermove", onMove);
      document.addEventListener("pointerup", onUp);
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    const primary = document.querySelector(".md-sidebar--primary");
    const secondary = document.querySelector(".md-sidebar--secondary");

    if (primary) setupHandle(primary, "primary");
    if (secondary) setupHandle(secondary, "secondary");
  });
})();

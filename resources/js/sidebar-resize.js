(() => {
  const MIN_WIDTH = 240;
  const MAX_WIDTH = 480;

  const getMaxWidth = () => Math.min(MAX_WIDTH, window.innerWidth - 200);
  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

  const setWidth = (sidebar, width) => {
    const next = clamp(width, MIN_WIDTH, getMaxWidth());
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

  const isDesktop = () =>
    window.matchMedia("(pointer: fine)").matches &&
    window.matchMedia("(min-width: 60em)").matches;

  document.addEventListener("DOMContentLoaded", () => {
    if (!isDesktop()) return;

    const primary = document.querySelector(".md-sidebar--primary");
    const secondary = document.querySelector(".md-sidebar--secondary");

    if (primary) setupHandle(primary, "primary");
    if (secondary) setupHandle(secondary, "secondary");

    const onResize = () => {
      [primary, secondary].forEach((sidebar) => {
        if (!sidebar) return;
        const width = sidebar.getBoundingClientRect().width;
        setWidth(sidebar, width);
      });
    };

    window.addEventListener("resize", onResize);
  });
})();

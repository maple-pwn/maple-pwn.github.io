(() => {
  const WORDS_PER_MINUTE = 300;

  const countWords = (text) => {
    const cjk = (text.match(/[\u4e00-\u9fff]/g) || []).length;
    const latin = (text.match(/[A-Za-z0-9]+/g) || []).length;
    return { total: cjk + latin };
  };

  const buildMetrics = () => {
    const article = document.querySelector("article.md-content__inner");
    if (!article) return;

    const existing = article.querySelector(".reading-metrics");
    if (existing) existing.remove();

    const text = article.innerText || "";
    const counts = countWords(text);
    if (!counts.total) return;

    const minutes = Math.max(1, Math.ceil(counts.total / WORDS_PER_MINUTE));
    const info = document.createElement("div");
    info.className = "reading-metrics";
    info.innerHTML = `<span>阅读时长 ${minutes} 分钟</span><span>字数 ${counts.total}</span>`;

    const h1 = article.querySelector("h1");
    if (h1 && h1.nextSibling) {
      h1.parentNode.insertBefore(info, h1.nextSibling);
    } else {
      article.insertBefore(info, article.firstChild);
    }
  };

  const hookMaterial = () => {
    if (window.document$ && window.document$.subscribe) {
      window.document$.subscribe(buildMetrics);
    } else {
      document.addEventListener("DOMContentLoaded", buildMetrics);
    }
  };

  hookMaterial();
})();

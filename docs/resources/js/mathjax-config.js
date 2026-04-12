window.MathJax = {
  tex: {
    packages: {'[+]': ['ams']},   // 启用 AMS，支持 align 环境
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']]
  },
  options: {
    skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
  }
};

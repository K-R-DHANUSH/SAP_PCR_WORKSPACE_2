// scripts/ai-validator.js
(function () {
  "use strict";

  function normalize(text) {
    return text
      .replace(/\r/g, "")
      .split("\n")
      .map(l => l.trim())
      .filter(Boolean);
  }

  function validate(lines) {
    const issues = [];

    lines.forEach((line, i) => {

      if (/\bTHEN\b/i.test(line))
        issues.push(`Line ${i + 1}: Remove THEN keyword`);

      if (/(AMT|RTE|NUM)\(\d+\)/i.test(line))
        issues.push(`Line ${i + 1}: Indexed AMT/RTE/NUM not allowed`);

      if (/[+\-*/]/.test(line) && !/MULTI|DIVI/i.test(line))
        issues.push(`Line ${i + 1}: Inline math not allowed`);
    });

    return issues;
  }

  window.PCRAIValidator = {
    normalize,
    validate
  };

})();
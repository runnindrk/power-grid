const svgNS = 'http://www.w3.org/2000/svg';

export function el(tag, attrs) {
  const e = document.createElementNS(svgNS, tag);
  for (const [name, value] of Object.entries(attrs)) e.setAttribute(name, value);
  return e;
}

export function htmlElement(tag, { className, textContent, ...attributes } = {}) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (textContent !== undefined) element.textContent = textContent;
  for (const [name, value] of Object.entries(attributes)) element.setAttribute(name, value);
  return element;
}

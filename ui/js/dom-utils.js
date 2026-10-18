const SVG_NAMESPACE = 'http://www.w3.org/2000/svg';

// Creates an SVG element with the given attributes.
export function el(tag, attributes) {
  const element = document.createElementNS(SVG_NAMESPACE, tag);

  for (const name in attributes) {
    element.setAttribute(name, attributes[name]);
  }

  return element;
}

// Creates an HTML element; className can be a text or a list of class names.
export function htmlElement(tag, options) {
  const element = document.createElement(tag);

  for (const name in options) {
    const value = options[name];

    if (name === 'className') {
      element.className = Array.isArray(value) ? value.join(' ') : value;
    } else if (name === 'textContent') {
      element.textContent = value;
    } else {
      element.setAttribute(name, value);
    }
  }

  return element;
}

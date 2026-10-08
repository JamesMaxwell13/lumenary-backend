(() => {
  const scriptSrc = document.currentScript?.src ?? "";
  const iconHref = scriptSrc.replace(/branding\.js(?:\?.*)?$/, "icon.png");
  const selectors = ['link[rel="shortcut icon"]', 'link[rel="icon"]'];
  const existingIcon = document.querySelector(selectors.join(", "));

  if (existingIcon) {
    existingIcon.href = iconHref;
    return;
  }

  const icon = document.createElement("link");
  icon.rel = "icon";
  icon.href = iconHref;
  document.head.appendChild(icon);
})();

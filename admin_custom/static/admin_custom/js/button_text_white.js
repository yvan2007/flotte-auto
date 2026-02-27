/**
 * Force le texte des boutons à fond coloré en blanc.
 * S'exécute au chargement et applique des styles inline pour garantir la visibilité.
 */
(function() {
  function applyWhiteText() {
    var selectors = '.btn-primary, .btn-success, .btn-danger, .btn-warning, .btn-info, input[type="submit"].btn-primary, input[type="submit"][name="_save"]';
    var els = document.querySelectorAll(selectors);
    els.forEach(function(el) {
      el.style.setProperty('color', 'white', 'important');
      el.style.setProperty('font-size', 'inherit', 'important');
      el.style.setProperty('opacity', '1', 'important');
      el.style.setProperty('visibility', 'visible', 'important');
      var children = el.querySelectorAll('*');
      children.forEach(function(child) {
        child.style.setProperty('color', 'white', 'important');
      });
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyWhiteText);
  } else {
    applyWhiteText();
  }
  // Réappliquer après un court délai (contenu dynamique)
  setTimeout(applyWhiteText, 100);
  setTimeout(applyWhiteText, 500);
})();

/*!
 * Dynamic Favicon Theme Switcher
 * Автоматически меняет favicon в зависимости от темы (светлая/тёмная)
 */

(function() {
  'use strict';

  function updateFavicon(theme) {
    const favicon = document.querySelector('link[rel="icon"]');
    const appleTouchIcon = document.querySelector('link[rel="apple-touch-icon"]');

    // Для тёмной темы используем светлую иконку (чтобы была видна на тёмном фоне)
    // Для светлой темы используем тёмную иконку (чтобы была видна на светлом фоне)
    const iconPath = theme === 'dark'
      ? '/static/images/vum-icon-light.svg'
      : '/static/images/vum-icon-dark.svg';

    if (favicon) favicon.href = iconPath;
    if (appleTouchIcon) appleTouchIcon.href = iconPath;
  }

  function getBrowserTheme() {
    // Определяем тему браузера/системы, НЕ тему сайта
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  function initFavicon() {
    // Устанавливаем начальную иконку на основе БРАУЗЕРНОЙ темы
    const browserTheme = getBrowserTheme();
    updateFavicon(browserTheme);

    // Следим ТОЛЬКО за изменениями системной/браузерной темы
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        const newTheme = e.matches ? 'dark' : 'light';
        updateFavicon(newTheme);
      });
    }
  }

  // Инициализация при загрузке DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFavicon);
  } else {
    initFavicon();
  }
})();

/* DR Liquidity - i18n (English / Hindi) */
(function() {
  const STORAGE = 'drl-lang';
  const translations = {
    en: {
      home: 'Home', firms: 'Firms', tools: 'Tools', education: 'Education',
      community: 'Community', journal: 'Journal', dashboard: 'Dashboard',
      login: 'Sign In', signup: 'Sign Up', logout: 'Logout',
      trade: 'Trade', win: 'Win', loss: 'Loss', save: 'Save', cancel: 'Cancel',
    },
    hi: {
      home: 'होम', firms: 'फर्म', tools: 'टूल्स', education: 'शिक्षा',
      community: 'समुदाय', journal: 'जर्नल', dashboard: 'डैशबोर्ड',
      login: 'साइन इन', signup: 'साइन अप', logout: 'लॉग आउट',
      trade: 'ट्रेड', win: 'जीत', loss: 'हार', save: 'सेव', cancel: 'रद्द',
    }
  };
  function getLang() { return localStorage.getItem(STORAGE) || 'en'; }
  function setLang(lang) {
    localStorage.setItem(STORAGE, lang);
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const k = el.getAttribute('data-i18n');
      if (translations[lang] && translations[lang][k]) el.textContent = translations[lang][k];
    });
  }
  setLang(getLang());
  window.DRLSetLang = setLang;
  window.DRLGetLang = getLang;
})();

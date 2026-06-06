/* Currency Formatting Logic for Teebusiness */

const CurrencyManager = {
  currentCurrency: 'GNF', // Default
  rates: {
    GNF: 1,
    USD: 0.00011,
    EUR: 0.00010869565217391304
  },
  
  formatters: {
    GNF: new Intl.NumberFormat('fr-GN', { style: 'currency', currency: 'GNF', maximumFractionDigits: 0 }),
    USD: new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }),
    EUR: new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 })
  },
  
  init() {
    const savedCurrency = localStorage.getItem('teebusiness_currency');
    if (savedCurrency && this.rates[savedCurrency]) {
      this.currentCurrency = savedCurrency;
    }
    
    // Bind currency selectors
    const selectors = document.querySelectorAll('.currency-select');
    selectors.forEach(selector => {
      selector.value = this.currentCurrency;
      selector.addEventListener('change', (e) => {
        this.setCurrency(e.target.value);
        // Sync all selectors
        selectors.forEach(s => { if(s !== e.target) s.value = e.target.value; });
      });
    });
    
    this.updatePricesOnPage();
  },
  
  setCurrency(currency) {
    if (this.rates[currency]) {
      this.currentCurrency = currency;
      localStorage.setItem('teebusiness_currency', currency);
      this.updatePricesOnPage();
    }
  },
  
  convertAndFormat(basePriceGnf) {
    const converted = basePriceGnf * this.rates[this.currentCurrency];
    return this.formatters[this.currentCurrency].format(converted);
  },
  
  updatePricesOnPage() {
    const priceElements = document.querySelectorAll('[data-price-gnf]');
    priceElements.forEach(el => {
      const basePrice = parseFloat(el.getAttribute('data-price-gnf'));
      el.textContent = this.convertAndFormat(basePrice);
      
      // Simple fade-in animation for price update
      el.style.opacity = '0.5';
      setTimeout(() => {
        el.style.opacity = '1';
      }, 150);
    });
  }
};

document.addEventListener('DOMContentLoaded', () => {
  CurrencyManager.init();
});

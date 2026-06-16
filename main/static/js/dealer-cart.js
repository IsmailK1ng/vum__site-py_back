/* Дилерская корзина — клиентское хранилище в localStorage.
 * Singleton: window.DealerCart
 *
 * Структура: [{ id: <part_id>, qty: <int> }, ...]
 * При любом изменении бросаем window event 'dealer-cart-change' —
 * хедер/бейджи подписываются на него и обновляют счётчик.
 */
(function(){
  if (window.DealerCart) return;

  var KEY = 'dealer_cart_v1';
  var EVENT = 'dealer-cart-change';

  function readRaw(){
    try {
      var raw = localStorage.getItem(KEY);
      var arr = raw ? JSON.parse(raw) : [];
      if (!Array.isArray(arr)) return [];
      // Чистим мусор: только корректные объекты с положительным qty
      return arr.filter(function(i){
        return i && Number.isInteger(i.id) && Number.isInteger(i.qty) && i.qty > 0;
      });
    } catch (e) {
      return [];
    }
  }

  function writeRaw(items){
    try {
      localStorage.setItem(KEY, JSON.stringify(items));
    } catch (e) {
      // QuotaExceeded или приватный режим — игнор, корзина не сохранится
    }
    window.dispatchEvent(new Event(EVENT));
  }

  function getItems(){ return readRaw(); }

  function findIndex(items, partId){
    for (var i = 0; i < items.length; i++) {
      if (items[i].id === partId) return i;
    }
    return -1;
  }

  function add(partId, qty){
    partId = parseInt(partId, 10);
    qty = parseInt(qty, 10) || 0;
    if (!partId || qty < 1) return;
    var items = readRaw();
    var idx = findIndex(items, partId);
    if (idx >= 0) items[idx].qty += qty;
    else items.push({ id: partId, qty: qty });
    writeRaw(items);
  }

  function setQuantity(partId, qty){
    partId = parseInt(partId, 10);
    qty = parseInt(qty, 10) || 0;
    if (!partId) return;
    var items = readRaw();
    if (qty < 1) {
      items = items.filter(function(i){ return i.id !== partId; });
    } else {
      var idx = findIndex(items, partId);
      if (idx >= 0) items[idx].qty = qty;
      else items.push({ id: partId, qty: qty });
    }
    writeRaw(items);
  }

  function remove(partId){ setQuantity(partId, 0); }
  function clear(){ writeRaw([]); }
  function count(){
    return readRaw().reduce(function(s, i){ return s + i.qty; }, 0);
  }
  function distinctCount(){ return readRaw().length; }

  /**
   * Привязка бейджа-счётчика к DOM-элементу.
   * targetEl — span/div куда будет рисоваться число (или пустота при 0).
   */
  function bindBadge(targetEl){
    if (!targetEl) return;
    function render(){
      var n = count();
      if (n > 0) {
        targetEl.textContent = n > 99 ? '99+' : String(n);
        targetEl.style.display = '';
      } else {
        targetEl.textContent = '';
        targetEl.style.display = 'none';
      }
    }
    render();
    window.addEventListener(EVENT, render);
    // Синхронизация между вкладками
    window.addEventListener('storage', function(e){
      if (e.key === KEY) render();
    });
  }

  window.DealerCart = {
    KEY: KEY,
    EVENT: EVENT,
    getItems: getItems,
    add: add,
    setQuantity: setQuantity,
    remove: remove,
    clear: clear,
    count: count,
    distinctCount: distinctCount,
    bindBadge: bindBadge
  };
})();

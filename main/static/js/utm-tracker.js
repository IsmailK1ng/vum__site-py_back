// main/static/js/utm-tracker.js
// Production version - UTM tracking for FAW Trucks

(function () {
    'use strict';

    // Cookie read function
    window.getCookie = function (name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return decodeURIComponent(parts.pop().split(';').shift());
        }
        return null;
    };

    // Cookie write function
    function setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
        const isSecure = location.protocol === 'https:' ? ';Secure' : '';
        document.cookie = `${name}=${encodeURIComponent(value)};expires=${expires.toUTCString()};path=/;SameSite=Lax${isSecure}`;
    }

    // Extract UTM from URL
    const params = new URLSearchParams(window.location.search);
    const utm = {};
    const utmKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'];
    
    utmKeys.forEach(key => {
        if (params.has(key)) {
            utm[key] = params.get(key);
        }
    });

    // Save UTM
    if (Object.keys(utm).length > 0) {
        const utmString = JSON.stringify(utm);
        sessionStorage.setItem('utm_data', utmString);
        setCookie('utm_data', utmString, 30);
    }

    // Get UTM function
    window.getUTMData = function() {
        // 1. Check URL
        const currentParams = new URLSearchParams(window.location.search);
        const currentUTM = {};
        utmKeys.forEach(key => {
            if (currentParams.has(key)) currentUTM[key] = currentParams.get(key);
        });
        if (Object.keys(currentUTM).length > 0) {
            return JSON.stringify(currentUTM);
        }
        
        // 2. Check sessionStorage
        const saved = sessionStorage.getItem('utm_data');
        if (saved) return saved;
        
        // 3. Check cookie
        const cookie = window.getCookie('utm_data');
        if (cookie) return cookie;
        
        return null;
    };
})();
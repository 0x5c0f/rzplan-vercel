// ==UserScript==
// @name         显示网站ip和ISP信息
// @namespace    https://{{ DOMAIN }}/
// @version      1.3
// @description  在一个浮动的可拖动面板中显示当前网站的解析IP地址和ISP信息，并提供DNS输入框。
// @description  当前脚本由 ChatGpt 生成
// @match        *://*/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @connect      {{ DOMAIN }}
// ==/UserScript==

(function() {
    'use strict';

    let dnsServer = GM_getValue('dnsServer', '8.8.8.8');
    const apiURL = '//{{ DOMAIN }}{{ API_V1_STR }}/utils/resolve';

    function createPanel() {
        const panel = document.createElement('div');
        panel.id = 'ip-info-panel';
        panel.style.position = 'fixed';
        panel.style.left = GM_getValue('panelLeft', 'auto');
        panel.style.top = GM_getValue('panelTop', 'auto');
        panel.style.right = GM_getValue('panelRight', '10px');
        panel.style.bottom = GM_getValue('panelBottom', '10px');
        panel.style.background = 'rgba(0, 0, 0, 0.5)';
        panel.style.color = 'white';
        panel.style.padding = '10px';
        panel.style.borderRadius = '8px';
        panel.style.zIndex = '99999';
        panel.style.fontSize = '14px';
        panel.style.maxWidth = '300px';
        panel.style.cursor = 'move';
        panel.innerHTML = '正在获取 IP 信息...';
        document.body.appendChild(panel);

        addDnsInput(panel);

        // 拖动功能
        let isDragging = false, offsetX, offsetY;

        panel.addEventListener('mousedown', function(e) {
            if (e.target.tagName.toLowerCase() === 'input') return; // 输入框不拖动
            isDragging = true;
            offsetX = e.clientX - panel.offsetLeft;
            offsetY = e.clientY - panel.offsetTop;
            e.preventDefault();
        });

        document.addEventListener('mousemove', function(e) {
            if (isDragging) {
                panel.style.left = (e.clientX - offsetX) + 'px';
                panel.style.top = (e.clientY - offsetY) + 'px';
                panel.style.right = 'auto';
                panel.style.bottom = 'auto';
            }
        });

        document.addEventListener('mouseup', function() {
            if (isDragging) {
                GM_setValue('panelLeft', panel.style.left);
                GM_setValue('panelTop', panel.style.top);
                GM_setValue('panelRight', 'auto');
                GM_setValue('panelBottom', 'auto');
            }
            isDragging = false;
        });

        // 点击展开/收起
        panel.addEventListener('click', (e) => {
    if (e.target.tagName.toLowerCase() === 'input') return; // 输入框不触发展开
    const detail = document.getElementById('ip-info-detail');
    const toggleText = panel.querySelector('em');
    if (detail) {
        if (detail.style.display === 'none') {
            detail.style.display = 'block';
            if (toggleText) toggleText.textContent = '(点击关闭详情)';
        } else {
            detail.style.display = 'none';
            if (toggleText) toggleText.textContent = '(点击展开详情)';
        }
    }
});
    }

    function addDnsInput(panel) {
        const dnsInput = document.createElement('input');
        dnsInput.type = 'text';
        dnsInput.placeholder = 'DNS 服务器 (默认8.8.8.8)';
        dnsInput.style.width = '100%';
        dnsInput.style.marginTop = '8px';
        dnsInput.style.padding = '4px 0';
        dnsInput.style.border = 'none';
        dnsInput.style.borderBottom = '1px solid white';
        dnsInput.style.background = 'transparent';
        dnsInput.style.color = 'white';
        dnsInput.style.outline = 'none';
        dnsInput.style.boxSizing = 'border-box';
        dnsInput.value = dnsServer;
        panel.appendChild(dnsInput);

        dnsInput.addEventListener('change', () => {
            dnsServer = dnsInput.value || '8.8.8.8';
            GM_setValue('dnsServer', dnsServer);
            fetchIPInfo();
        });
    }

    function updatePanel(data) {
        const panel = document.getElementById('ip-info-panel');
        if (!panel) return;

        let content = `<strong>${data.domain}</strong><br>`;
        content += `DNS: ${data.dns_server}<br>`;
        content += `IPv4: ${data.ipv4_addresses.length} | IPv6: ${data.ipv6_addresses.length}<br>`;
        content += `<em>(点击展开详情)</em>`;

        let detailHTML = '<div id="ip-info-detail" style="display:none; margin-top:8px;">';
        data.ipinfo.forEach(info => {
            detailHTML += `<div style="margin-bottom:5px;">`;
            detailHTML += `<div>IP: ${info.ip}</div>`;
            if (info.org) detailHTML += `<div>ISP: ${info.org}</div>`;
            if (info.country) detailHTML += `<div>国家: ${info.country}</div>`;
            detailHTML += `</div>`;
        });
        detailHTML += '</div>';

        panel.innerHTML = content + detailHTML;

        addDnsInput(panel);
    }

    function fetchIPInfo() {
        const hostname = window.location.hostname;
        GM_xmlhttpRequest({
            method: "GET",
            url: `${apiURL}?domain=${hostname}&dns_server=${dnsServer}&show_ipinfo=false`,
            onload: function(response) {
                try {
                    const data = JSON.parse(response.responseText);
                    updatePanel(data);
                } catch (e) {
                    console.error('解析IP信息失败:', e);
                }
            },
            onerror: function() {
                console.error('请求IP信息失败');
            }
        });
    }

    // 执行
    createPanel();
    fetchIPInfo();

})();

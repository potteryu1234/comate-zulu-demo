// 全局状态
let selectedProducts = [];
let allProducts = [];
let currentScenario = 'balanced';
let scenarios = {};
let currentSessionId = null;

// 初始化Session ID
function initSession() {
    currentSessionId = localStorage.getItem('wristband_session_id');
    if (!currentSessionId) {
        currentSessionId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('wristband_session_id', currentSessionId);
    }
    return currentSessionId;
}

// 记录用户行为（用于协同过滤）
async function recordBehavior(productId, behaviorType = 'view', score = 1) {
    const sessionId = initSession();
    try {
        await fetch('/api/behavior', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': sessionId
            },
            body: JSON.stringify({
                wristband_id: productId,
                behavior_type: behaviorType,
                score: score
            })
        });
    } catch (err) {
        console.log('行为记录失败:', err);
    }
}

// 初始化
window.onload = function() {
    initSession();
    loadScenarios();
    loadProducts();
    loadMarketData();
};

// 切换标签页
function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
    
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
    
    if (tabName === 'market') {
        setTimeout(() => initMarketCharts(), 100);
    }
}

// 加载场景配置
function loadScenarios() {
    fetch('/api/scenarios')
        .then(res => res.json())
        .then(data => {
            scenarios = data;
        });
}

// 设置场景 - 增强版（带场景描述和推荐说明）
function setScenario(scenarioKey) {
    currentScenario = scenarioKey;
    
    // 更新按钮状态
    document.querySelectorAll('.scenario-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // 更新权重滑块
    if (scenarios[scenarioKey]) {
        const scenario = scenarios[scenarioKey];
        const weights = scenario.weights;
        
        for (let key in weights) {
            const slider = document.getElementById(key);
            if (slider) {
                slider.value = weights[key];
                updateWeight(key);
            }
        }
        
        // 显示场景说明
        showScenarioDescription(scenario);
    }
}

// 显示场景描述
function showScenarioDescription(scenario) {
    // 移除旧的描述
    const oldDesc = document.getElementById('scenario-description');
    if (oldDesc) {
        oldDesc.remove();
    }
    
    // 创建场景描述元素
    const descDiv = document.createElement('div');
    descDiv.id = 'scenario-description';
    descDiv.style.cssText = `
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        animation: fadeIn 0.3s ease;
    `;
    
    // 场景详细说明
    const descriptions = {
        'health_focus': {
            title: '🏥 健康预警关注',
            desc: '重点关注健康监测功能的完整性和数据精准度，适合关注身体状况、需要健康预警的用户。',
            highlights: ['心率、血氧、睡眠等健康功能', '数据测量精准度', '健康预警提醒']
        },
        'battery_focus': {
            title: '🔋 长续航刚需',
            desc: '优先考虑续航能力，减少充电频率，适合户外运动、差旅频繁的用户。',
            highlights: ['超长续航时间', 'GPS模式续航', '快速充电']
        },
        'balanced': {
            title: '⚖️ 均衡之选',
            desc: '在健康功能、续航、舒适度等方面取得平衡，适合大多数用户的日常使用。',
            highlights: ['功能全面均衡', '性价比合理', '佩戴舒适']
        },
        'budget': {
            title: '💰 性价比优先',
            desc: '在有限预算内获取最大功能价值，适合学生党、初次尝试智能手环的用户。',
            highlights: ['价格实惠', '核心功能齐全', '高性价比']
        }
    };
    
    const desc = descriptions[currentScenario] || { title: scenario.name, desc: '', highlights: [] };
    
    descDiv.innerHTML = `
        <h3 style="margin: 0 0 10px 0; font-size: 18px;">${desc.title}</h3>
        <p style="margin: 0 0 10px 0; opacity: 0.95; line-height: 1.5;">${desc.desc}</p>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            ${desc.highlights.map(h => `<span style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 15px; font-size: 12px;">${h}</span>`).join('')}
        </div>
    `;
    
    // 插入到场景按钮后面
    const scenarioPanel = document.querySelector('.scenario-buttons').parentElement;
    scenarioPanel.insertBefore(descDiv, scenarioPanel.children[1]);
    
    // 3秒后自动淡出
    setTimeout(() => {
        if (descDiv.parentElement) {
            descDiv.style.opacity = '0.7';
        }
    }, 3000);
}

// 更新权重显示 - 增强版（带总权重校验和自动归一化）
function updateWeight(id, autoNormalize = false) {
    const slider = document.getElementById(id);
    const value = parseInt(slider.value);
    document.getElementById('val-' + id).textContent = value + '%';
    
    // 计算总权重
    const weightIds = ['health_breadth', 'data_accuracy', 'battery_life', 'comfort', 'brand_reputation', 'price_performance'];
    let total = 0;
    const currentValues = {};
    
    weightIds.forEach(w => {
        const val = parseInt(document.getElementById(w).value);
        currentValues[w] = val;
        total += val;
    });
    
    // 更新总权重显示
    const totalElement = document.getElementById('total-weight');
    totalElement.textContent = `总权重: ${total}%`;
    
    // 根据总权重设置颜色
    if (total === 100) {
        totalElement.style.color = '#28a745'; // 绿色
        totalElement.innerHTML = `总权重: ${total}% ✓`;
    } else if (total > 100) {
        totalElement.style.color = '#dc3545'; // 红色
        totalElement.innerHTML = `总权重: ${total}% ⚠ 超出${total - 100}%`;
    } else {
        totalElement.style.color = '#ffc107'; // 黄色
        totalElement.innerHTML = `总权重: ${total}% ⚠ 还差${100 - total}%`;
    }
    
    // 自动归一化
    if (autoNormalize && total > 0 && total !== 100) {
        const factor = 100 / total;
        weightIds.forEach(w => {
            const newValue = Math.round(currentValues[w] * factor);
            document.getElementById(w).value = newValue;
            document.getElementById('val-' + w).textContent = newValue + '%';
        });
        totalElement.style.color = '#28a745';
        totalElement.innerHTML = `总权重: 100% ✓ (已自动归一化)`;
    }
}

// 权重归一化按钮功能
function normalizeWeights() {
    updateWeight('health_breadth', true);
}

// 获取推荐
function getRecommendations() {
    const weights = {
        health_breadth: parseInt(document.getElementById('health_breadth').value),
        data_accuracy: parseInt(document.getElementById('data_accuracy').value),
        battery_life: parseInt(document.getElementById('battery_life').value),
        comfort: parseInt(document.getElementById('comfort').value),
        brand_reputation: parseInt(document.getElementById('brand_reputation').value),
        price_performance: parseInt(document.getElementById('price_performance').value)
    };
    
    const resultsDiv = document.getElementById('recommend-results');
    resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在分析用户偏好...</p></div>';
    
    fetch('/api/recommend', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-Session-ID': initSession()
        },
        body: JSON.stringify({ scenario: currentScenario, weights: weights })
    })
    .then(res => res.json())
    .then(data => {
        displayRecommendations(data.recommendations, data.meta);
    })
    .catch(err => {
        resultsDiv.innerHTML = '<p style="color: #e74c3c;">获取推荐失败，请重试</p>';
    });
}

// 显示推荐结果
function displayRecommendations(products, meta) {
    const container = document.getElementById('recommend-results');
    
    if (!products || products.length === 0) {
        container.innerHTML = '<p>暂无推荐数据</p>';
        return;
    }
    
    // 显示推荐方式提示
    let tipHtml = '';
    if (meta && meta.cf_used) {
        tipHtml = '<p style="margin-bottom:15px;color:#667eea;font-size:14px;">🤖 混合推荐：协同过滤(40%) + 加权评分(60%)</p>';
    } else {
        tipHtml = '<p style="margin-bottom:15px;color:#999;font-size:14px;">📊 加权评分推荐（行为数据积累后将启用协同过滤）</p>';
    }
    
    container.innerHTML = tipHtml + products.map((p, index) => `
        <div class="product-card" onclick="toggleProductSelection(${p.id})" data-id="${p.id}">
            <div class="product-rank">${index + 1}</div>
            ${p.image_url ? `<img src="${p.image_url.split(',')[0]}" alt="${p.name}" class="product-image" onerror="this.style.display='none'">` : ''}
            <div class="product-brand">${p.brand || '未知品牌'}</div>
            <div class="product-name">${p.name}</div>
            <div class="product-price">¥${p.price || '价格未知'}</div>
            <div class="product-score">
                <span>综合</span>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${(p.hybrid_score || p.score) * 10}%"></div>
                </div>
                <span class="score-value">${(p.hybrid_score || p.score).toFixed(1)}分</span>
            </div>
            ${p.cf_score !== null && p.cf_score !== undefined ? `
            <div class="product-score" style="margin-top:5px;">
                <span>CF</span>
                <div class="score-bar">
                    <div class="score-fill" style="width:${p.cf_score * 10}%;background:#e67e22"></div>
                </div>
                <span class="score-value" style="color:#e67e22">${p.cf_score.toFixed(1)}</span>
            </div>
            ` : ''}
            <div class="feature-tags">
                ${Object.entries(p.features || {}).filter(([k, v]) => v).slice(0, 4).map(([k]) => `
                    <span class="feature-tag">${getFeatureName(k)}</span>
                `).join('')}
            </div>
        </div>
    `).join('');
    
    // 恢复选中状态
    selectedProducts.forEach(id => {
        const card = document.querySelector(`.product-card[data-id="${id}"]`);
        if (card) card.classList.add('selected');
    });
}

// 功能名称映射
function getFeatureName(key) {
    const names = {
        heart_rate: '心率',
        sleep: '睡眠',
        blood_oxygen: '血氧',
        stress: '压力',
        body_temp: '体温',
        ecg: '心电图',
        blood_pressure: '血压',
        blood_sugar: '血糖',
        gps: 'GPS',
        nfc: 'NFC',
        water_resist: '防水',
        bluetooth_call: '蓝牙通话'
    };
    return names[key] || key;
}

// 切换产品选择
function toggleProductSelection(productId) {
    const index = selectedProducts.indexOf(productId);
    const card = document.querySelector(`.product-card[data-id="${productId}"]`);
    
    if (index > -1) {
        selectedProducts.splice(index, 1);
        if (card) card.classList.remove('selected');
    } else {
        if (selectedProducts.length < 4) {
            selectedProducts.push(productId);
            if (card) card.classList.add('selected');
        } else {
            alert('最多只能选择4个产品进行对比');
            return;
        }
    }
    
    updateComparePanel();
}

// 更新对比面板
function updateComparePanel() {
    const panel = document.getElementById('compare-panel');
    const count = document.getElementById('compare-count');
    
    count.textContent = selectedProducts.length;
    panel.style.display = selectedProducts.length > 0 ? 'block' : 'none';
}

// 显示对比
function showCompare() {
    if (selectedProducts.length < 2) {
        alert('请至少选择2个产品进行对比');
        return;
    }
    
    showTab('compare');
    document.querySelectorAll('.nav-tab')[3].classList.add('active');
    
    const resultsDiv = document.getElementById('compare-results');
    resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在生成对比...</p></div>';
    
    fetch('/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_ids: selectedProducts })
    })
    .then(res => res.json())
    .then(data => {
        displayComparison(data);
    });
}

// 显示对比结果 - 增强版（带雷达图）
function displayComparison(products) {
    const container = document.getElementById('compare-results');
    
    if (!products || products.length === 0) {
        container.innerHTML = '<p>暂无对比数据</p>';
        return;
    }
    
    const features = ['heart_rate', 'sleep', 'blood_oxygen', 'stress', 'body_temp', 'ecg', 'gps', 'nfc', 'water_resist'];
    
    // 创建雷达图容器
    let html = '<div style="margin-bottom: 30px;">';
    html += '<h3 style="margin-bottom: 15px;">综合对比雷达图</h3>';
    html += '<div id="compare-radar-chart" style="width: 100%; height: 400px;"></div>';
    html += '</div>';
    
    // 详细对比表格
    html += '<h3 style="margin-bottom: 15px;">详细参数对比</h3>';
    html += '<table style="width: 100%; border-collapse: collapse;">';
    
    // 表头
    html += '<tr><th style="padding: 15px; border: 1px solid #ddd; background: #f8f9fa;">对比项</th>';
    products.forEach(p => {
        html += `<th style="padding: 15px; border: 1px solid #ddd; background: #f8f9fa; text-align: center;">${p.name}</th>`;
    });
    html += '</tr>';
    
    // 价格
    html += '<tr><td style="padding: 15px; border: 1px solid #ddd; font-weight: bold;">价格</td>';
    products.forEach(p => {
        html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center; color: #e74c3c; font-weight: bold;">¥${p.price || '未知'}</td>`;
    });
    html += '</tr>';
    
    // 满意度
    html += '<tr><td style="padding: 15px; border: 1px solid #ddd; font-weight: bold;">用户满意度</td>';
    products.forEach(p => {
        html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center;">${p.satisfaction}%</td>`;
    });
    html += '</tr>';
    
    // 续航指数
    html += '<tr><td style="padding: 15px; border: 1px solid #ddd; font-weight: bold;">续航指数</td>';
    products.forEach(p => {
        html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center;">${p.battery_score}/10</td>`;
    });
    html += '</tr>';
    
    // 健康功能
    features.forEach(f => {
        html += `<tr><td style="padding: 15px; border: 1px solid #ddd; font-weight: bold;">${getFeatureName(f)}</td>`;
        products.forEach(p => {
            const hasFeature = p.features && p.features[f];
            html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center;">${hasFeature ? '✅' : '❌'}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</table>';
    
    // 添加清空按钮和生成报告按钮
    html += `<div style="margin-top: 20px; text-align: center; display: flex; justify-content: center; gap: 10px;">
        <button class="scenario-btn" onclick="clearSelection()">清空选择</button>
        <button class="btn-primary" onclick="generateComparisonReport()">📊 生成对比报告</button>
    </div>`;
    
    container.innerHTML = html;
    
    // 渲染雷达图
    setTimeout(() => renderCompareRadarChart(products), 100);
}

// 渲染对比雷达图
function renderCompareRadarChart(products) {
    const chartDom = document.getElementById('compare-radar-chart');
    if (!chartDom) return;
    
    const chart = echarts.init(chartDom);
    
    // 准备雷达图数据
    const indicators = [
        { name: '健康功能', max: 10 },
        { name: '数据精准', max: 10 },
        { name: '续航能力', max: 10 },
        { name: '舒适度', max: 10 },
        { name: '品牌口碑', max: 10 },
        { name: '性价比', max: 10 }
    ];
    
    const colors = ['#667eea', '#e74c3c', '#27ae60', '#f39c12'];
    
    const seriesData = products.map((p, index) => ({
        value: [
            p.score_details?.health_breadth || 5,
            p.score_details?.data_accuracy || 5,
            p.score_details?.battery_life || 5,
            p.score_details?.comfort || 5,
            p.score_details?.brand_reputation || 5,
            p.score_details?.price_performance || 5
        ],
        name: p.name,
        lineStyle: { color: colors[index % colors.length] },
        areaStyle: { 
            color: colors[index % colors.length],
            opacity: 0.1
        },
        itemStyle: { color: colors[index % colors.length] }
    }));
    
    chart.setOption({
        tooltip: { trigger: 'item' },
        legend: {
            data: products.map(p => p.name),
            bottom: 0
        },
        radar: {
            indicator: indicators,
            center: ['50%', '45%'],
            radius: '65%'
        },
        series: [{
            type: 'radar',
            data: seriesData
        }]
    });
}

// 生成对比报告
function generateComparisonReport() {
    if (selectedProducts.length < 2) {
        alert('请至少选择2个产品进行对比');
        return;
    }
    
    // 获取当前对比的产品数据
    fetch('/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_ids: selectedProducts })
    })
    .then(res => res.json())
    .then(products => {
        // 生成报告HTML
        const reportHtml = createComparisonReportHtml(products);
        
        // 在新窗口打开报告
        const reportWindow = window.open('', '_blank');
        reportWindow.document.write(reportHtml);
        reportWindow.document.close();
    });
}

// 创建对比报告HTML
function createComparisonReportHtml(products) {
    const now = new Date().toLocaleString('zh-CN');
    
    let html = `
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>智能手环选购对比报告</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; background: #f5f7fa; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #667eea; text-align: center; margin-bottom: 10px; }
            .subtitle { text-align: center; color: #999; margin-bottom: 30px; }
            .product-grid { display: grid; grid-template-columns: repeat(${products.length}, 1fr); gap: 20px; margin-bottom: 30px; }
            .product-card { background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; }
            .product-name { font-weight: bold; margin-bottom: 10px; }
            .product-price { color: #e74c3c; font-size: 20px; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px; border: 1px solid #ddd; text-align: center; }
            th { background: #667eea; color: white; }
            .recommendation { background: #e8f5e9; padding: 20px; border-radius: 10px; margin-top: 30px; }
            .winner { background: #fff3e0; padding: 15px; border-radius: 8px; margin-top: 20px; }
            @media print { body { background: white; } .container { box-shadow: none; } }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 智能手环选购对比报告</h1>
            <p class="subtitle">生成时间：${now}</p>
            
            <h2>对比产品</h2>
            <div class="product-grid">
                ${products.map(p => `
                    <div class="product-card">
                        <div class="product-name">${p.name}</div>
                        <div class="product-price">¥${p.price || '未知'}</div>
                        <div style="margin-top: 10px; color: #666;">${p.brand || '未知品牌'}</div>
                    </div>
                `).join('')}
            </div>
            
            <h2>详细对比</h2>
            <table>
                <tr>
                    <th>对比项</th>
                    ${products.map(p => `<th>${p.name}</th>`).join('')}
                </tr>
                <tr>
                    <td>价格</td>
                    ${products.map(p => `<td>¥${p.price || '未知'}</td>`).join('')}
                </tr>
                <tr>
                    <td>综合评分</td>
                    ${products.map(p => `<td>${p.satisfaction || '-'}</td>`).join('')}
                </tr>
                <tr>
                    <td>续航指数</td>
                    ${products.map(p => `<td>${p.battery_score || '-'}/10</td>`).join('')}
                </tr>
            </table>
            
            <div class="recommendation">
                <h3>💡 选购建议</h3>
                <p>根据您的需求偏好，我们为您分析以上产品的优劣势。建议您根据实际使用场景和预算进行选择。</p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
                <p>本报告由智能手环选购分析平台自动生成，仅供参考</p>
            </div>
        </div>
    </body>
    </html>`;
    
    return html;
}

// 清空选择
function clearSelection() {
    selectedProducts = [];
    document.querySelectorAll('.product-card.selected').forEach(card => {
        card.classList.remove('selected');
    });
    updateComparePanel();
    document.getElementById('compare-results').innerHTML = '<p style="color: #666;">请在"智能推荐"或"产品库"中选择2-4个产品进行对比</p>';
}

// 加载产品列表
function loadProducts() {
    fetch('/api/products')
        .then(res => res.json())
        .then(data => {
            allProducts = data;
            if (data.length === 0) {
                document.getElementById('product-list').style.display = 'none';
                document.getElementById('no-data-tip').style.display = 'block';
            } else {
                document.getElementById('product-list').style.display = 'grid';
                document.getElementById('no-data-tip').style.display = 'none';
                displayProductList(data);
            }
        })
        .catch(err => {
            document.getElementById('product-list').style.display = 'none';
            document.getElementById('no-data-tip').style.display = 'block';
        });
}

// 加载演示数据
function loadDemoData() {
    const demoProducts = [
        {id: 1, brand: '苹果', name: 'Apple Watch Series 9', price: '2999', intro: '全新S9 SiP芯片，双指互点两下，精准查找iPhone'},
        {id: 2, brand: '华为', name: '华为 Watch GT 4', price: '1488', intro: '14天超长续航，科学减脂管理，心律失常提示'},
        {id: 3, brand: '小米', name: '小米手环8 Pro', price: '399', intro: '1.74英寸AMOLED大屏，150+运动模式，独立GPS'},
        {id: 4, brand: '华为', name: '华为手环8', price: '269', intro: '14天续航，100种运动模式，血氧自动检测'},
        {id: 5, brand: '苹果', name: 'Apple Watch SE', price: '1999', intro: 'S8 SiP芯片，车祸检测，50米防水'},
        {id: 6, brand: '三星', name: 'Galaxy Watch6', price: '1799', intro: '身体成分分析，睡眠追踪，Exynos W930芯片'}
    ];
    
    document.getElementById('product-list').style.display = 'grid';
    document.getElementById('no-data-tip').style.display = 'none';
    displayProductList(demoProducts);
    
    // 显示提示
    alert('已加载演示数据，仅供功能展示使用');
}

// 显示产品列表
function displayProductList(products) {
    const container = document.getElementById('product-list');
    
    if (!products || products.length === 0) {
        container.innerHTML = '<p>暂无产品数据，请先运行爬虫</p>';
        return;
    }
    
    container.innerHTML = products.map(p => `
        <div class="product-card" onclick="showProductDetail(${p.id})" data-id="${p.id}">
            ${p.image_url ? `<img src="${p.image_url.split(',')[0]}" alt="${p.name}" class="product-image" onerror="this.style.display='none'">` : ''}
            <div class="product-brand">${p.brand || '未知品牌'}</div>
            <div class="product-name">${p.name}</div>
            <div class="product-price">¥${p.price || '价格未知'}</div>
            <p style="color: #666; font-size: 14px; margin-top: 10px; line-height: 1.5;">${p.intro ? p.intro.substring(0, 80) + '...' : '暂无简介'}</p>
        </div>
    `).join('');
}

// 显示产品详情
function showProductDetail(productId) {
    const modal = document.getElementById('detail-modal');
    const body = document.getElementById('detail-body');
    const title = document.getElementById('detail-title');
    
    modal.style.display = 'flex';
    body.innerHTML = '<div class="loading"><div class="spinner"></div><p>加载中...</p></div>';
    
    fetch(`/api/product/${productId}`)
        .then(res => res.json())
        .then(data => {
            title.textContent = data.product.name;
            
            let html = `
                ${data.product.image_url ? `
                <div style="margin-bottom: 20px; text-align: center;">
                    <img src="${data.product.image_url.split(',')[0]}" alt="${data.product.name}" style="max-width: 100%; max-height: 300px; object-fit: contain; border-radius: 10px;" onerror="this.style.display='none'">
                </div>
                ` : ''}
                <div style="margin-bottom: 20px;">
                    <span style="color: #e74c3c; font-size: 24px; font-weight: bold;">¥${data.product.price || '价格未知'}</span>
                    <span style="color: #666; margin-left: 20px;">${data.product.brand || '未知品牌'}</span>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="margin-bottom: 10px;">健康功能</h3>
                    <div class="feature-tags">
                        ${Object.entries(data.features || {}).map(([k, v]) => `
                            <span class="feature-tag ${v ? '' : 'missing'}">${getFeatureName(k)} ${v ? '✓' : '✗'}</span>
                        `).join('')}
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="margin-bottom: 10px;">续航指数: ${data.battery_score}/10</h3>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${data.battery_score * 10}%"></div>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="margin-bottom: 10px;">维度情感分析</h3>
                    ${Object.entries(data.dimension_analysis || {}).map(([k, v]) => `
                        <div style="margin: 10px 0;">
                            <span>${getDimensionName(k)}: </span>
                            <span style="color: ${v.sentiment > 0.6 ? '#27ae60' : v.sentiment > 0.4 ? '#f39c12' : '#e74c3c'}">
                                ${(v.sentiment * 100).toFixed(1)}% (${v.count}条)
                            </span>
                        </div>
                    `).join('')}
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h3 style="margin-bottom: 10px;">高频关键词</h3>
                    <div class="feature-tags">
                        ${(data.keywords || []).map(k => `
                            <span class="feature-tag">${k.word} (${k.weight})</span>
                        `).join('')}
                    </div>
                </div>
                
                <div>
                    <h3 style="margin-bottom: 10px;">用户反馈</h3>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                        <h4 style="color: #27ae60; margin-bottom: 10px;">优点</h4>
                        ${(data.pros_cons?.pros || []).map(p => `<p style="margin: 5px 0;">✓ ${p.text}</p>`).join('') || '<p style="color: #999;">暂无数据</p>'}
                    </div>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px;">
                        <h4 style="color: #e74c3c; margin-bottom: 10px;">缺点</h4>
                        ${(data.pros_cons?.cons || []).map(c => `<p style="margin: 5px 0;">✗ ${c.text}</p>`).join('') || '<p style="color: #999;">暂无数据</p>'}
                    </div>
                </div>
            `;
            
            body.innerHTML = html;
        });
}

// 维度名称映射
function getDimensionName(key) {
    const names = {
        battery: '续航表现',
        comfort: '佩戴舒适度',
        accuracy: '数据准确度',
        appearance: '外观设计'
    };
    return names[key] || key;
}

// 关闭详情弹窗
function closeDetail(event) {
    if (!event || event.target.id === 'detail-modal') {
        document.getElementById('detail-modal').style.display = 'none';
    }
}

// 加载市场数据
function loadMarketData() {
    fetch('/api/market/overview')
        .then(res => res.json())
        .then(data => {
            window.marketData = data;
        });
}

// 初始化市场图表 - 增强版
function initMarketCharts() {
    if (!window.marketData) {
        console.log('市场数据尚未加载');
        return;
    }
    
    const data = window.marketData;
    
    // 品牌价格分布箱线图
    const priceChart = echarts.init(document.getElementById('price-chart'));
    
    if (data.brand_boxplot && data.brand_boxplot.brands.length > 0) {
        const brands = data.brand_boxplot.brands;
        const boxData = data.brand_boxplot.data.map(d => d.box_data);
        
        priceChart.setOption({
            title: { 
                text: '主流品牌价格分布（箱线图）',
                left: 'center'
            },
            tooltip: { 
                trigger: 'item',
                formatter: function(params) {
                    const d = data.brand_boxplot.data[params.dataIndex];
                    return `${d.brand}<br/>` +
                           `最小值: ¥${params.value[0]}]}<br/>` +
                           `Q1: ¥${params.value[1]}]}<br/>` +
                           `中位数: ¥${params.value[2]}]}<br/>` +
                           `Q3: ¥${params.value[3]}]}<br/>` +
                           `最大值: ¥${params.value[4]}]}<br/>` +
                           `平均: ¥${d.avg}<br/>` +
                           `产品数: ${d.count}`;
                }
            },
            xAxis: { 
                type: 'category', 
                data: brands,
                axisLabel: { rotate: 30 }
            },
            yAxis: { 
                type: 'value', 
                name: '价格(元)',
                axisLabel: {
                    formatter: function(value) {
                        return '¥' + value;
                    }
                }
            },
            series: [{
                type: 'boxplot',
                data: boxData,
                itemStyle: { 
                    color: '#667eea',
                    borderColor: '#764ba2',
                    borderWidth: 2
                }
            }]
        });
    } else {
        priceChart.setOption({
            title: { text: '暂无品牌价格数据', left: 'center' }
        });
    }
    
    // 健康功能渗透率堆叠柱状图
    const featureChart = echarts.init(document.getElementById('feature-chart'));
    
    if (data.feature_penetration && data.feature_penetration.features.length > 0) {
        const priceRanges = data.feature_penetration.price_ranges;
        const features = data.feature_penetration.features;
        
        // 选择前8个重要功能展示
        const topFeatures = features.slice(0, 8);
        
        featureChart.setOption({
            title: { 
                text: '健康功能在不同价格段位的渗透率',
                left: 'center'
            },
            tooltip: { 
                trigger: 'axis',
                axisPointer: { type: 'shadow' }
            },
            legend: {
                data: topFeatures.map(f => f.feature_name),
                bottom: 0,
                type: 'scroll'
            },
            xAxis: {
                type: 'category',
                data: priceRanges
            },
            yAxis: { 
                type: 'value', 
                name: '渗透率(%)',
                max: 100,
                axisLabel: {
                    formatter: '{value}%'
                }
            },
            series: topFeatures.map((f, index) => ({
                name: f.feature_name,
                type: 'bar',
                stack: 'total',
                data: f.penetration_rates,
                emphasis: { focus: 'series' }
            }))
        });
    } else {
        featureChart.setOption({
            title: { text: '暂无功能渗透率数据', left: 'center' }
        });
    }
}

// ==================== 用户系统模块 ====================

let currentUser = null;

// 检查登录状态
function checkLoginStatus() {
    fetch('/api/user/current')
        .then(res => res.json())
        .then(data => {
            if (data.logged_in) {
                currentUser = data.user;
                updateUserPanel();
            }
        });
}

// 更新用户面板
function updateUserPanel() {
    const panel = document.getElementById('user-panel');
    if (currentUser) {
        panel.innerHTML = `
            <span style="color: white;">欢迎, ${currentUser.username}</span>
            <button class="btn-primary" onclick="logout()" style="margin-left: 10px; padding: 8px 20px; font-size: 14px;">退出</button>
        `;
    } else {
        panel.innerHTML = `
            <span id="user-status" style="color: white;">未登录</span>
            <button class="btn-primary" onclick="showLoginModal()" style="margin-left: 10px; padding: 8px 20px; font-size: 14px;">登录</button>
            <button class="btn-primary" onclick="showRegisterModal()" style="margin-left: 10px; padding: 8px 20px; font-size: 14px; background: transparent; border: 2px solid white;">注册</button>
        `;
    }
}

// 显示登录弹窗
function showLoginModal() {
    showLoginForm();
    document.getElementById('login-modal').style.display = 'flex';
}

// 显示注册弹窗
function showRegisterModal() {
    showRegisterForm();
    document.getElementById('login-modal').style.display = 'flex';
}

// 关闭登录弹窗
function closeLoginModal(event) {
    if (!event || event.target.id === 'login-modal') {
        document.getElementById('login-modal').style.display = 'none';
    }
}

// 显示登录表单
function showLoginForm() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('auth-title').textContent = '用户登录';
}

// 显示注册表单
function showRegisterForm() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
    document.getElementById('auth-title').textContent = '用户注册';
}

// 弹窗登录
function modalLogin() {
    const username = document.getElementById('modal-login-username').value;
    const password = document.getElementById('modal-login-password').value;
    
    if (!username || !password) {
        alert('请输入用户名和密码');
        return;
    }
    
    fetch('/api/user/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            currentUser = data.user;
            updateUserPanel();
            closeLoginModal();
            loadUserData();
            alert('登录成功！');
        } else {
            alert(data.error || '登录失败');
        }
    })
    .catch(err => {
        alert('登录请求失败，请检查网络连接');
    });
}

// 弹窗注册
function modalRegister() {
    const username = document.getElementById('modal-register-username').value.trim();
    const password = document.getElementById('modal-register-password').value;
    const password2 = document.getElementById('modal-register-password2').value;
    const email = document.getElementById('modal-register-email').value.trim();
    const nickname = document.getElementById('modal-register-nickname').value.trim();
    
    // 验证输入
    if (!username || !password) {
        alert('用户名和密码不能为空');
        return;
    }
    
    if (password !== password2) {
        alert('两次输入的密码不一致');
        return;
    }
    
    if (password.length < 6) {
        alert('密码长度至少为6位');
        return;
    }
    
    fetch('/api/user/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            username, 
            password, 
            email: email || null, 
            nickname: nickname || username 
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert('注册成功！请登录');
            showLoginForm();
            // 清空注册表单
            document.getElementById('modal-register-username').value = '';
            document.getElementById('modal-register-password').value = '';
            document.getElementById('modal-register-password2').value = '';
            document.getElementById('modal-register-email').value = '';
            document.getElementById('modal-register-nickname').value = '';
            // 填充登录表单
            document.getElementById('modal-login-username').value = username;
        } else {
            alert(data.error || '注册失败');
        }
    })
    .catch(err => {
        alert('注册请求失败，请检查网络连接');
    });
}

// 页面内登录
function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    if (!username || !password) {
        alert('请输入用户名和密码');
        return;
    }
    
    fetch('/api/user/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            currentUser = data.user;
            updateUserPanel();
            showUserDashboard();
            loadUserData();
        } else {
            alert(data.error || '登录失败');
        }
    });
}

// 退出登录
function logout() {
    fetch('/api/user/logout', { method: 'POST' })
        .then(() => {
            currentUser = null;
            location.reload();
        });
}

// 显示用户仪表盘
function showUserDashboard() {
    document.getElementById('login-panel').style.display = 'none';
    document.getElementById('user-dashboard').style.display = 'block';
}

// 加载用户数据
function loadUserData() {
    loadUserFavorites();
    loadUserHistory();
}

// 加载用户收藏
function loadUserFavorites() {
    fetch('/api/user/favorites')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('user-favorites');
            if (data.error) {
                container.innerHTML = '<p>请先登录</p>';
                return;
            }
            if (data.length === 0) {
                container.innerHTML = '<p style="color: #999;">暂无收藏</p>';
                return;
            }
            container.innerHTML = data.map(p => `
                <div class="product-card" onclick="showProductDetail(${p.id})" style="cursor: pointer;">
                    <div class="product-brand">${p.brand || '未知品牌'}</div>
                    <div class="product-name">${p.name}</div>
                    <div class="product-price">¥${p.price || '价格未知'}</div>
                </div>
            `).join('');
        });
}

// 加载用户历史
function loadUserHistory() {
    fetch('/api/user/history')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('user-history');
            if (data.error) {
                container.innerHTML = '<p>请先登录</p>';
                return;
            }
            if (data.length === 0) {
                container.innerHTML = '<p style="color: #999;">暂无浏览记录</p>';
                return;
            }
            container.innerHTML = data.slice(0, 10).map(p => `
                <div class="product-card" onclick="showProductDetail(${p.id})" style="cursor: pointer;">
                    <div class="product-brand">${p.brand || '未知品牌'}</div>
                    <div class="product-name">${p.name}</div>
                    <div style="font-size: 12px; color: #999; margin-top: 5px;">
                        ${p.behavior_type === 'favorite' ? '⭐ 收藏' : p.behavior_type === 'compare' ? '📊 对比' : '👁 浏览'}
                    </div>
                </div>
            `).join('');
        });
}

// 获取协同过滤推荐
function getCFRecommendations() {
    const container = document.getElementById('personal-recommend-results');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在分析相似用户...</p></div>';
    
    fetch('/api/recommend/collaborative')
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                container.innerHTML = '<p style="color: #e74c3c;">' + data.error + '</p>';
                return;
            }
            if (data.fallback || data.recommendations.length === 0) {
                container.innerHTML = '<p style="color: #999;">' + data.message + '</p>';
                return;
            }
            displayPersonalRecommendations(data.recommendations);
        });
}

// 获取混合推荐
function getHybridRecommendations() {
    const container = document.getElementById('personal-recommend-results');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在生成个性化推荐...</p></div>';
    
    fetch('/api/recommend/hybrid')
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                container.innerHTML = '<p style="color: #e74c3c;">' + data.error + '</p>';
                return;
            }
            displayPersonalRecommendations(data.recommendations, true);
        });
}

// 显示个性化推荐
function displayPersonalRecommendations(products, showCFBadge = false) {
    const container = document.getElementById('personal-recommend-results');
    
    if (!products || products.length === 0) {
        container.innerHTML = '<p>暂无推荐</p>';
        return;
    }
    
    container.innerHTML = products.map((p, index) => `
        <div class="product-card" onclick="showProductDetail(${p.id})" style="cursor: pointer;">
            ${showCFBadge && p.cf_recommended ? '<div style="background: #27ae60; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px; display: inline-block; margin-bottom: 5px;">协同推荐</div>' : ''}
            ${p.image_url ? `<img src="${p.image_url.split(',')[0]}" alt="${p.name}" class="product-image" onerror="this.style.display='none'">` : ''}
            <div class="product-rank">${index + 1}</div>
            <div class="product-brand">${p.brand || '未知品牌'}</div>
            <div class="product-name">${p.name}</div>
            <div class="product-price">¥${p.price || '价格未知'}</div>
            <div class="product-score">
                <div class="score-bar">
                    <div class="score-fill" style="width: ${p.score * 10}%"></div>
                </div>
                <span class="score-value">${p.score}分</span>
            </div>
        </div>
    `).join('');
}

// 保存用户偏好
function savePreference() {
    if (!currentUser) {
        alert('请先登录');
        return;
    }
    
    const prefName = document.getElementById('pref-name').value || '我的偏好';
    
    const weights = {
        health_breadth: parseInt(document.getElementById('health_breadth').value),
        data_accuracy: parseInt(document.getElementById('data_accuracy').value),
        battery_life: parseInt(document.getElementById('battery_life').value),
        comfort: parseInt(document.getElementById('comfort').value),
        brand_reputation: parseInt(document.getElementById('brand_reputation').value),
        price_performance: parseInt(document.getElementById('price_performance').value),
        name: prefName,
        is_default: true
    };
    
    fetch('/api/user/preference', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(weights)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert('偏好设置已保存');
        } else {
            alert(data.error || '保存失败');
        }
    });
}

// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    loadBrands();
});

// ==================== 产品搜索功能 ====================

function loadBrands() {
    fetch('/api/brands')
        .then(res => res.json())
        .then(brands => {
            const select = document.getElementById('search-brand');
            if (select) {
                brands.forEach(brand => {
                    const option = document.createElement('option');
                    option.value = brand;
                    option.textContent = brand;
                    select.appendChild(option);
                });
            }
        })
        .catch(err => console.log('加载品牌列表失败'));
}

function searchProducts() {
    const keyword = document.getElementById('search-keyword').value;
    const brand = document.getElementById('search-brand').value;
    const minPrice = document.getElementById('search-min-price').value;
    const maxPrice = document.getElementById('search-max-price').value;
    const sort = document.getElementById('search-sort').value;
    
    // 获取选中的功能筛选
    const features = [];
    document.querySelectorAll('.search-feature:checked').forEach(cb => {
        features.push(cb.value);
    });
    
    // 构建查询参数
    const params = new URLSearchParams();
    if (keyword) params.append('keyword', keyword);
    if (brand) params.append('brand', brand);
    if (minPrice) params.append('min_price', minPrice);
    if (maxPrice) params.append('max_price', maxPrice);
    if (sort) params.append('sort', sort);
    features.forEach(f => params.append('features', f));
    
    const container = document.getElementById('search-results');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>搜索中...</p></div>';
    
    fetch(`/api/search?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('search-count').textContent = `(${data.total}个结果)`;
            displaySearchResults(data.products);
        })
        .catch(err => {
            container.innerHTML = '<p style="color: #e74c3c; text-align: center;">搜索失败，请重试</p>';
        });
}

function displaySearchResults(products) {
    const container = document.getElementById('search-results');
    
    if (!products || products.length === 0) {
        container.innerHTML = '<p style="color: #999; text-align: center;">没有找到符合条件的产品</p>';
        return;
    }
    
    container.innerHTML = products.map(p => `
        <div class="product-card" onclick="showProductDetail(${p.id})" style="cursor: pointer;">
            ${p.image_url ? `<img src="${p.image_url.split(',')[0]}" alt="${p.name}" class="product-image" onerror="this.style.display='none'">` : ''}
            <div class="product-brand">${p.brand || '未知品牌'}</div>
            <div class="product-name">${p.name}</div>
            <div class="product-price">¥${p.price || '价格未知'}</div>
            <p style="color: #666; font-size: 14px; margin-top: 10px; line-height: 1.5;">${p.intro ? p.intro.substring(0, 80) + '...' : '暂无简介'}</p>
            <div style="margin-top: 10px;">
                <button class="scenario-btn" onclick="event.stopPropagation(); addToCompare(${p.id})" style="font-size: 12px; padding: 5px 10px;">+ 对比</button>
            </div>
        </div>
    `).join('');
}

function resetSearch() {
    document.getElementById('search-keyword').value = '';
    document.getElementById('search-brand').value = '';
    document.getElementById('search-min-price').value = '';
    document.getElementById('search-max-price').value = '';
    document.getElementById('search-sort').value = 'relevance';
    document.querySelectorAll('.search-feature:checked').forEach(cb => cb.checked = false);
    document.getElementById('search-results').innerHTML = '<p style="color: #999; text-align: center;">请输入搜索条件</p>';
    document.getElementById('search-count').textContent = '';
}

// ==================== 高级对比功能 ====================

function addToCompare(productId) {
    if (selectedProducts.includes(productId)) {
        alert('该产品已在对比列表中');
        return;
    }
    if (selectedProducts.length >= 6) {
        alert('最多只能对比6个产品');
        return;
    }
    selectedProducts.push(productId);
    updateComparePreview();
    alert('已添加到对比列表');
}

function loadProductsForCompare() {
    const input = document.getElementById('compare-product-ids').value;
    if (!input) {
        alert('请输入产品ID');
        return;
    }
    
    const ids = input.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
    if (ids.length < 2) {
        alert('至少需要输入2个产品ID');
        return;
    }
    
    selectedProducts = ids.slice(0, 6);
    updateComparePreview();
}

function updateComparePreview() {
    const container = document.getElementById('selected-products-preview');
    if (selectedProducts.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = `
        <p style="margin-bottom: 10px;">已选择 ${selectedProducts.length} 个产品：</p>
        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
            ${selectedProducts.map(id => `
                <span style="background: #667eea; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px;">
                    产品ID: ${id}
                    <span onclick="removeFromCompare(${id})" style="cursor: pointer; margin-left: 5px;">×</span>
                </span>
            `).join('')}
        </div>
    `;
}

function removeFromCompare(productId) {
    const index = selectedProducts.indexOf(productId);
    if (index > -1) {
        selectedProducts.splice(index, 1);
        updateComparePreview();
    }
}

function startAdvancedCompare() {
    if (selectedProducts.length < 2) {
        alert('请至少选择2个产品进行对比');
        return;
    }
    
    // 获取选中的对比维度
    const dimensions = [];
    document.querySelectorAll('.compare-dimension:checked').forEach(cb => {
        dimensions.push(cb.value);
    });
    
    if (dimensions.length === 0) {
        alert('请至少选择一个对比维度');
        return;
    }
    
    const resultsDiv = document.getElementById('compare-results');
    const analysisDiv = document.getElementById('compare-analysis');
    resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在生成对比...</p></div>';
    analysisDiv.innerHTML = '';
    
    fetch('/api/compare/advanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            product_ids: selectedProducts,
            dimensions: dimensions
        })
    })
    .then(res => res.json())
    .then(data => {
        displayAdvancedComparison(data);
    })
    .catch(err => {
        resultsDiv.innerHTML = '<p style="color: #e74c3c;">对比失败，请重试</p>';
    });
}

function displayAdvancedComparison(data) {
    const container = document.getElementById('compare-results');
    const analysisDiv = document.getElementById('compare-analysis');
    
    if (!data.products || data.products.length === 0) {
        container.innerHTML = '<p>暂无对比数据</p>';
        return;
    }
    
    const products = data.products;
    const dimensions = data.dimensions;
    
    // 构建对比表格
    let html = '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse; min-width: 600px;">';
    
    // 表头 - 产品名称
    html += '<tr><th style="padding: 15px; border: 1px solid #ddd; background: #f8f9fa; width: 150px;">对比项</th>';
    products.forEach(p => {
        html += `<th style="padding: 15px; border: 1px solid #ddd; background: #f8f9fa; text-align: center; min-width: 150px;">
            <div>${p.name}</div>
            <div style="font-size: 12px; color: #666; margin-top: 5px;">${p.brand || '未知品牌'}</div>
        </th>`;
    });
    html += '</tr>';
    
    // 价格
    if (dimensions.includes('price')) {
        html += '<tr><td style="padding: 15px; border: 1px solid #ddd; font-weight: bold;">价格</td>';
        products.forEach(p => {
            const isBest = p.id === data.analysis.best_value;
            html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center; color: #e74c3c; font-weight: bold; ${isBest ? 'background: #fff3cd;' : ''}">
                ¥${p.price || '未知'}
                ${isBest ? '<div style="font-size: 12px; color: #27ae60;">⭐性价比最高</div>' : ''}
            </td>`;
        });
        html += '</tr>';
    }
    
    // 健康功能
    if (dimensions.includes('features')) {
        const features = ['heart_rate', 'sleep', 'blood_oxygen', 'stress', 'body_temp', 'ecg', 'gps', 'nfc', 'water_resist'];
        features.forEach(f => {
            html += `<tr><td style="padding: 15px; border: 1px solid #ddd; font-weight: bold;">${getFeatureName(f)}</td>`;
            products.forEach(p => {
                const hasFeature = p.features && p.features[f];
                html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center;">${hasFeature ? '✅' : '❌'}</td>`;
            });
            html += '</tr>';
        });
        
        // 功能数量统计
        html += '<tr><td style="padding: 15px; border: 1px solid #ddd; font-weight: bold;">功能数量</td>';
        products.forEach(p => {
            const count = p.features ? Object.values(p.features).filter(v => v).length : 0;
            const isMost = p.id === data.analysis.most_features;
            html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center; ${isMost ? 'background: #d4edda; font-weight: bold;' : ''}">
                ${count}项
                ${isMost ? '<div style="font-size: 12px; color: #27ae60;">⭐功能最全</div>' : ''}
            </td>`;
        });
        html += '</tr>';
    }
    
    // 续航能力
    if (dimensions.includes('battery')) {
        html += '<tr><td style="padding: 15px; border: 1px solid #ddd; font-weight: bold;">续航指数</td>';
        products.forEach(p => {
            const isBest = p.id === data.analysis.best_battery;
            html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center; ${isBest ? 'background: #d1ecf1; font-weight: bold;' : ''}">
                ${p.battery_score || '-'}/10
                ${isBest ? '<div style="font-size: 12px; color: #17a2b8;">⭐续航最强</div>' : ''}
            </td>`;
        });
        html += '</tr>';
    }
    
    // 用户评分
    if (dimensions.includes('rating')) {
        html += '<tr><td style="padding: 15px; border: 1px solid #ddd; font-weight: bold;">用户满意度</td>';
        products.forEach(p => {
            const isBest = p.id === data.analysis.best_rating;
            html += `<td style="padding: 15px; border: 1px solid #ddd; text-align: center; ${isBest ? 'background: #f8d7da; font-weight: bold;' : ''}">
                ${p.satisfaction || '-'}%
                <div style="font-size: 12px; color: #666;">(${p.reviews_count || 0}条评价)</div>
                ${isBest ? '<div style="font-size: 12px; color: #dc3545;">⭐口碑最好</div>' : ''}
            </td>`;
        });
        html += '</tr>';
    }
    
    html += '</table></div>';
    container.innerHTML = html;
    
    // 显示智能分析
    if (data.analysis.recommendations.length > 0) {
        analysisDiv.innerHTML = `
            <div class="panel" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <div class="panel-title" style="color: white; border-left-color: white;">🤖 智能对比分析</div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                    ${data.analysis.recommendations.map(r => `
                        <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px;">
                            <div style="font-weight: bold; margin-bottom: 10px;">${r.product_name}</div>
                            <div style="font-size: 14px;">
                                ${r.reasons.map(reason => `<span style="display: inline-block; background: rgba(255,255,255,0.3); padding: 3px 10px; border-radius: 15px; margin: 2px;">${reason}</span>`).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
}

function clearCompareSelection() {
    selectedProducts = [];
    document.getElementById('compare-product-ids').value = '';
    updateComparePreview();
    document.getElementById('compare-results').innerHTML = '';
    document.getElementById('compare-analysis').innerHTML = '';
}

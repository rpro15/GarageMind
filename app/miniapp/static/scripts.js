[23 06 2026 19:12] Ruslan: const API_BASE = window.location.origin;

const brandSelect = document.getElementById('brand');
const modelSelect = document.getElementById('model');
const yearInput = document.getElementById('year');
const budgetInput = document.getElementById('budget');
const form = document.getElementById('tireForm');
const resultsDiv = document.getElementById('results');
const adviceDiv = document.getElementById('advice');
const productListDiv = document.getElementById('product-list');
const loadingDiv = document.getElementById('loading');
const submitBtn = document.getElementById('submitBtn');

let tg = window.Telegram?.WebApp;
if (tg) {
    tg.expand();
    tg.ready();
}

async function loadBrands() {
    try {
        const response = await fetch(`${API_BASE}/api/brands`);
        if (!response.ok) throw new Error('Ошибка загрузки марок');
        const brands = await response.json();
        brandSelect.innerHTML = '<option value="">Выберите марку</option>';
        brands.forEach(brand => {
            const option = document.createElement('option');
            option.value = brand;
            option.textContent = brand;
            brandSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading brands:', error);
        brandSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
    }
}

brandSelect.addEventListener('change', async () => {
    const brand = brandSelect.value;
    if (!brand) {
        modelSelect.innerHTML = '<option value="">Сначала выберите марку</option>';
        modelSelect.disabled = true;
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/api/models?brand=${encodeURIComponent(brand)}`);
        if (!response.ok) throw new Error('Ошибка загрузки моделей');
        const models = await response.json();
        modelSelect.innerHTML = '<option value="">Выберите модель</option>';
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            modelSelect.appendChild(option);
        });
        modelSelect.disabled = false;
    } catch (error) {
        console.error('Error loading models:', error);
        modelSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
        modelSelect.disabled = true;
    }
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const brand = brandSelect.value;
    const model = modelSelect.value;
    const year = yearInput.value;
    const drivingStyle = document.querySelector('input[name="driving_style"]:checked')?.value;
    const budget = budgetInput.value;
    const season = document.querySelector('input[name="season"]:checked')?.value;
    
    if (!brand  !model  !year || !drivingStyle) {
        alert('Пожалуйста, заполните все обязательные поля.');
        return;
    }
    
    loadingDiv.style.display = 'block';
    resultsDiv.style.display = 'none';
    submitBtn.disabled = true;
    
    const payload = {
        brand,
        model,
        year: parseInt(year),
        driving_style: drivingStyle,
        budget: budget ? parseInt(budget) : null,
        season: season || null
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/recommend_tires`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Ошибка сервера');
        }
        
        const data = await response.json();
        displayResults(data);
        
        if (tg) {
            tg.sendData(JSON.stringify({ action: 'recommendation', ...data }));
        }
        
    } catch (error) {
        alert(`Произошла ошибка: ${error.message}`);
        console.error(error);
    } finally {
        loadingDiv.style.display = 'none';
        submitBtn.disabled = false;
    }
});

function displayResults(data) {
[23 06 2026 19:12] Ruslan: resultsDiv.style.display = 'block';
    adviceDiv.innerHTML = <p>${data.advice}</p>;
    productListDiv.innerHTML = '';
    if (data.products && data.products.length > 0) {
        data.products.forEach(product => {
            const card = document.createElement('div');
            card.className = 'product-card';
            
            const img = document.createElement('img');
            img.src = product.image_url || 'https://via.placeholder.com/64?text=No+Image';
            img.alt = product.name;
            
            const info = document.createElement('div');
            info.className = 'product-info';
            info.innerHTML = `
                <div class="name">${product.name}</div>
                <div class="price">${product.price} ₽</div>
                <div class="source">${product.source || 'Партнёр'}</div>
            `;
            
            const link = document.createElement('a');
            link.href = product.partner_link || '#';
            link.target = '_blank';
            link.className = 'product-link';
            link.textContent = 'Купить';
            
            card.appendChild(img);
            card.appendChild(info);
            card.appendChild(link);
            productListDiv.appendChild(card);
        });
    } else {
        productListDiv.innerHTML = '<p>К сожалению, товаров по вашему запросу не найдено. Попробуйте изменить параметры.</p>';
    }
}

loadBrands();
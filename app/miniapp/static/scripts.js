// ============================================
// Авто Эксперт AI — Чат-консультант
// ============================================

const API_BASE = window.location.origin;
const $ = id => document.getElementById(id);

// ===== DOM =====
const messagesEl = $('messages');
const chatInput = $('chatInput');
const sendBtn = $('sendBtn');
const micBtn = $('micBtn');
const speechIndicator = $('speechIndicator');
const resultsOverlay = $('resultsOverlay');
const resultsPanel = $('resultsPanel');
const adviceDiv = $('advice');
const productListDiv = $('product-list');
const closeResultsBtn = $('closeResults');
const loadingResults = $('loading-results');
const modeToggle = $('modeToggle');
const chatMode = $('chatMode');
const formMode = $('formMode');
const headerSub = $('headerSub');
const tireForm = $('tireForm');
const brandSelect = $('brand');
const modelSelect = $('model');
const yearInput = $('year');
const budgetInput = $('budget');

let tg = window.Telegram?.WebApp;
if (tg) { tg.expand(); tg.ready(); }

// ===== Состояние =====
let currentMode = 'chat'; // 'chat' | 'form'
const userData = {
    brand: null,
    model: null,
    year: null,
    driving_style: null,
    season: null,
    budget: null
};
let currentStep = 0;
let isProcessing = false;

// ===== Справочники =====
const MODELS_RU = {
    "Lada": ["Granta", "Vesta", "Niva Legend", "Niva Travel", "Largus", "Kalina", "Priora", "XRAY"],
    "Kia": ["Rio", "Sportage", "Cerato", "Stinger", "Soul", "Seltos", "Sorento", "Picanto"],
    "Hyundai": ["Solaris", "Creta", "Tucson", "Elantra", "Santa Fe", "Sonata", "Palisade"],
    "Toyota": ["Camry", "Corolla", "RAV4", "Land Cruiser 300", "Yaris", "Highlander", "C-HR", "Hilux"],
    "Volkswagen": ["Polo", "Golf", "Passat", "Tiguan", "Jetta", "Teramont", "Taos", "ID.4"],
    "Skoda": ["Octavia", "Rapid", "Kodiaq", "Karoq", "Superb", "Fabia", "Yeti"],
    "Nissan": ["Qashqai", "X-Trail", "Terrano", "Almera", "Juke", "Murano", "Pathfinder"],
    "Mitsubishi": ["Outlander", "Pajero Sport", "L200", "ASX", "Eclipse Cross", "Lancer"],
    "BMW": ["X5", "X3", "3 Series", "5 Series", "X1", "X7", "iX", "M5"],
    "Mercedes-Benz": ["GLC", "GLE", "E-Class", "C-Class", "GLA", "GLB", "S-Class", "G-Class"],
    "Audi": ["Q5", "Q7", "A6", "A4", "Q3", "A8", "e-tron", "RS6"],
    "Ford": ["Focus", "Kuga", "Explorer", "Transit", "Ranger", "Mustang", "Puma"],
    "Renault": ["Logan", "Duster", "Kaptur", "Arkana", "Sandero", "Megane", "Koleos"],
    "Chevrolet": ["Niva", "Tahoe", "Camaro", "Cruze", "Traverse", "Suburban"],
    "Mazda": ["CX-5", "Mazda 6", "CX-9", "MX-5", "CX-30", "Mazda 3"],
};

const BRANDS = Object.keys(MODELS_RU).sort();

const DRIVING_STYLES = {
    "комфорт": "comfort",
    "комфортный": "comfort",
    "спорт": "sport",
    "спортивный": "sport",
    "экономия": "economy",
    "эконом": "economy",
    "экономичный": "economy",
};
const SEASONS = {
    "лето": "summer",
    "летний": "summer",
    "летняя": "summer",
    "зима": "winter",
    "зимний": "winter",
    "зимняя": "winter",
    "всесезон": "all_season",
    "всесезонный": "all_season",
    "всесезонная": "all_season",
};
const MONTHS_SEASON = {
    "лето": "summer",
    "весна": "summer",
    "осень": "all_season",
    "зима": "winter",
};

// ===== Шаги диалога (чат) =====
const DIALOG = [
    {
        question: "Привет! Я AI-консультант по подбору шин 🚗\n\nС какой маркой автомобиля?",
        parse: (text) => {
            const found = BRANDS.find(b => text.toLowerCase().includes(b.toLowerCase()));
            if (found) return { valid: true, value: found };
            for (const b of BRANDS) {
                if (text.length >= 3 && b.toLowerCase().startsWith(text.toLowerCase().slice(0, 3))) {
                    return { valid: true, value: b };
                }
            }
            return { valid: false, hint: `Я не узнал марку. Напишите одну из: ${BRANDS.slice(0, 8).join(', ')}...` };
        }
    },
    {
        question: (data) => `Отлично, ${data.brand}! Какая модель?`,
        parse: (text, data) => {
            const models = MODELS_RU[data.brand] || [];
            const found = models.find(m => text.toLowerCase().includes(m.toLowerCase()));
            if (found) return { valid: true, value: found };
            for (const m of models) {
                if (text.length >= 2 && m.toLowerCase().startsWith(text.toLowerCase().slice(0, 2))) {
                    return { valid: true, value: m };
                }
            }
            return { valid: false, hint: `Модели ${data.brand}: ${models.join(', ')}` };
        }
    },
    {
        question: "Какой год выпуска?",
        parse: (text) => {
            const nums = text.match(/\d{4}/);
            if (nums) {
                const y = parseInt(nums[0]);
                if (y >= 1980 && y <= 2026) return { valid: true, value: y };
            }
            return { valid: false, hint: "Напишите год цифрами (например, 2020)" };
        }
    },
    {
        question: "Стиль вождения?\n\n🚗 Комфорт — плавная езда\n🏎️ Спорт — динамика\n⛽ Эконом — экономия",
        parse: (text) => {
            const t = text.toLowerCase();
            for (const [key, val] of Object.entries(DRIVING_STYLES)) {
                if (t.includes(key)) return { valid: true, value: val };
            }
            if (t.includes("ком")) return { valid: true, value: "comfort" };
            if (t.includes("спорт")) return { valid: true, value: "sport" };
            if (t.includes("эко")) return { valid: true, value: "economy" };
            return { valid: false, hint: "Выберите: Комфорт, Спорт или Эконом" };
        }
    },
    {
        question: "Какой сезон?\n\n☀️ Лето\n❄️ Зима\n🌦️ Всесезон",
        parse: (text) => {
            const t = text.toLowerCase();
            for (const [key, val] of Object.entries(SEASONS)) {
                if (t.includes(key)) return { valid: true, value: val };
            }
            for (const [key, val] of Object.entries(MONTHS_SEASON)) {
                if (t.includes(key)) return { valid: true, value: val };
            }
            if (t.includes("лет")) return { valid: true, value: "summer" };
            if (t.includes("зим")) return { valid: true, value: "winter" };
            if (t.includes("все")) return { valid: true, value: "all_season" };
            return { valid: false, hint: "Выберите: Лето, Зима или Всесезон" };
        }
    },
    {
        question: "Какой бюджет? (₽)\n\nМожно пропустить — скажите 'любой'",
        parse: (text) => {
            const t = text.toLowerCase();
            if (t.includes("нет") || t.includes("любой") || t.includes("не") || t.includes("пропустить") || t.includes("без")) {
                return { valid: true, value: null };
            }
            const nums = text.match(/\d+/);
            if (nums) return { valid: true, value: parseInt(nums[0]) };
            return { valid: false, hint: "Напишите сумму цифрами (например, 40000) или 'любой'" };
        }
    },
];

// ===== Переключение режимов =====
function switchMode(mode) {
    currentMode = mode;
    if (mode === 'chat') {
        chatMode.classList.remove('hidden');
        formMode.classList.add('hidden');
        modeToggle.classList.remove('form-active');
        modeToggle.innerHTML = '<i class="fas fa-list"></i>';
        headerSub.innerHTML = '<i class="fas fa-robot"></i> <span>AI-консультант по подбору шин</span>';
        // Если чат пустой — начать диалог
        if (messagesEl.children.length === 0) {
            setTimeout(() => askQuestion(0), 300);
        }
    } else {
        chatMode.classList.add('hidden');
        formMode.classList.remove('hidden');
        modeToggle.classList.add('form-active');
        modeToggle.innerHTML = '<i class="fas fa-comment-dots"></i>';
        headerSub.innerHTML = '<i class="fas fa-sliders-h"></i> <span>Быстрый подбор шин</span>';
        loadFormBrands();
    }
    document.getElementById('app').classList.remove('step-0', 'step-1', 'step-2', 'step-3', 'step-4', 'step-5');
}

modeToggle.addEventListener('click', () => {
    switchMode(currentMode === 'chat' ? 'form' : 'chat');
});

// ===== Чат: сообщения =====
function addMessage(text, type = 'bot') {
    const div = document.createElement('div');
    div.className = `msg ${type}`;
    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.innerHTML = type === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = text;
    div.appendChild(avatar);
    div.appendChild(bubble);
    messagesEl.appendChild(div);
    scrollChat();
    return div;
}

function addTyping() {
    const div = document.createElement('div');
    div.className = 'msg bot';
    div.id = 'typingIndicator';
    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
    div.appendChild(avatar);
    div.appendChild(bubble);
    messagesEl.appendChild(div);
    scrollChat();
}

function removeTyping() {
    const el = $('typingIndicator');
    if (el) el.remove();
}

function scrollChat() {
    const chat = $('chat');
    chat.scrollTop = chat.scrollHeight;
}

function setStepClass(step) {
    const app = document.getElementById('app');
    for (let i = 0; i <= 6; i++) app.classList.remove(`step-${i}`);
    if (step >= 0 && step <= 5) app.classList.add(`step-${step}`);
}

// ===== Чат: вопросы =====
function askQuestion(step) {
    const dialog = DIALOG[step];
    if (!dialog) return;
    const q = typeof dialog.question === 'function' ? dialog.question(userData) : dialog.question;
    addMessage(q);
    setStepClass(step);
}

function handleUserInput(text) {
    if (isProcessing) return;
    text = text.trim();
    if (!text) return;

    addMessage(text, 'user');
    chatInput.value = '';

    const dialog = DIALOG[currentStep];
    if (!dialog) return;

    const result = dialog.parse(text, userData);

    if (!result.valid) {
        addTyping();
        setTimeout(() => { removeTyping(); addMessage(result.hint); }, 600);
        return;
    }

    const keys = ['brand', 'model', 'year', 'driving_style', 'season', 'budget'];
    userData[keys[currentStep]] = result.value;
    currentStep++;

    if (currentStep >= DIALOG.length) {
        addTyping();
        setTimeout(() => { removeTyping(); sendRecommendation(); }, 800);
    } else {
        setTimeout(() => askQuestion(currentStep), 400);
    }
}

// ===== Общий запрос к API =====
async function sendRecommendation(payloadOverride) {
    const payload = payloadOverride || {
        brand: userData.brand,
        model: userData.model,
        year: userData.year,
        driving_style: userData.driving_style,
        season: userData.season,
        budget: userData.budget
    };

    if (currentMode === 'chat') {
        addMessage("Спасибо! Анализирую ваш авто... 🤖");
        addTyping();
    }
    loadingResults.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/recommend_tires`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (currentMode === 'chat') removeTyping();

        if (!response.ok) {
            const err = await response.json();
            if (currentMode === 'chat') addMessage(`Ошибка: ${err.error || 'Что-то пошло не так'}`);
            return;
        }

        const data = await response.json();
        loadingResults.classList.add('hidden');
        showResults(data);

        if (currentMode === 'chat') {
            addMessage("Готово! Смотрите рекомендации ниже 👇");
        }

        if (tg) {
            tg.sendData(JSON.stringify({ action: 'recommendation', ...data }));
        }

    } catch (err) {
        if (currentMode === 'chat') removeTyping();
        loadingResults.classList.add('hidden');
        if (currentMode === 'chat') addMessage(`Ошибка соединения: ${err.message}`);
        console.error(err);
    }
}

// ===== Результаты =====
function showResults(data) {
    adviceDiv.innerHTML = `<p>${data.advice}</p>`;
    productListDiv.innerHTML = '';

    if (data.products && data.products.length > 0) {
        data.products.forEach(product => {
            const card = document.createElement('div');
            card.className = 'product-card';
            const img = document.createElement('img');
            img.src = product.image_url || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 56 56"%3E%3Crect width="56" height="56" fill="%230a0d14" rx="8"/%3E%3Ccircle cx="28" cy="28" r="12" fill="none" stroke="%2300d4ff" stroke-width="1.5"/%3E%3C/svg%3E';
            img.alt = product.name;
            const info = document.createElement('div');
            info.className = 'product-info';
            info.innerHTML = `
                <div class="name">${product.name}</div>
                <div class="price">${product.price.toLocaleString('ru-RU')} ₽</div>
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
        productListDiv.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">Товаров не найдено.</p>';
    }

    resultsOverlay.classList.remove('hidden');
}

// ===== Форма =====
async function loadFormBrands() {
    try {
        const response = await fetch(`${API_BASE}/api/brands`);
        const brands = await response.json();
        brandSelect.innerHTML = '<option value="">Выберите марку</option>';
        brands.forEach(b => {
            const opt = document.createElement('option');
            opt.value = b;
            opt.textContent = b;
            brandSelect.appendChild(opt);
        });
    } catch (e) {
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
    // Локальные модели
    const localModels = MODELS_RU[brand] || ['Другая'];
    modelSelect.innerHTML = '<option value="">Выберите модель</option>';
    localModels.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m;
        modelSelect.appendChild(opt);
    });
    modelSelect.disabled = false;
});

tireForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        brand: brandSelect.value,
        model: modelSelect.value,
        year: parseInt(yearInput.value),
        driving_style: document.querySelector('input[name="driving_style"]:checked')?.value || 'comfort',
        season: document.querySelector('input[name="season"]:checked')?.value || 'summer',
        budget: budgetInput.value ? parseInt(budgetInput.value) : null,
    };
    if (!payload.brand || !payload.model || !payload.year) {
        alert('Заполните все обязательные поля');
        return;
    }
    loadingResults.classList.remove('hidden');
    await sendRecommendation(payload);
});

// ===== Голосовой ввод =====
let recognition = null;
let isListening = false;

function initSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        micBtn.style.opacity = '0.4';
        micBtn.title = 'Голосовой ввод не поддерживается';
        return;
    }
    recognition = new SpeechRecognition();
    recognition.lang = 'ru-RU';
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        stopListening();
        chatInput.value = transcript;
        handleUserInput(transcript);
    };
    recognition.onerror = (event) => {
        stopListening();
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
            addMessage(`Ошибка: ${event.error}`, 'bot');
        }
    };
    recognition.onend = () => stopListening();
}

function toggleListening() {
    if (!recognition) {
        addMessage("Голосовой ввод не поддерживается в вашем браузере", 'bot');
        return;
    }
    if (isListening) stopListening();
    else startListening();
}

function startListening() {
    try {
        recognition.start();
        isListening = true;
        micBtn.classList.add('listening');
        speechIndicator.classList.remove('hidden');
        micBtn.innerHTML = '<i class="fas fa-stop"></i>';
    } catch (e) {}
}

function stopListening() {
    try { recognition.stop(); } catch(e) {}
    isListening = false;
    micBtn.classList.remove('listening');
    speechIndicator.classList.add('hidden');
    micBtn.innerHTML = '<i class="fas fa-microphone"></i>';
}

// ===== События =====
sendBtn.addEventListener('click', () => handleUserInput(chatInput.value));
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleUserInput(chatInput.value);
});
micBtn.addEventListener('click', toggleListening);
closeResultsBtn.addEventListener('click', () => resultsOverlay.classList.add('hidden'));
resultsOverlay.addEventListener('click', (e) => {
    if (e.target === resultsOverlay) resultsOverlay.classList.add('hidden');
});

// ===== Старт =====
function init() {
    initSpeech();
    switchMode('chat'); // по умолчанию чат
}

init();

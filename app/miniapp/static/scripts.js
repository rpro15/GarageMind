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
const popularPickDiv = $('popularPick');
const popularContentDiv = $('popularContent');
const shareBtn = $('shareBtn');
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
let lastRecommendationData = null;

// ===== I18N =====
let currentLang = localStorage.getItem('lang') || 'ru';
let translations = {};

async function loadLang(lang) {
    try {
        const resp = await fetch(API_BASE + '/api/lang/' + lang);
        if (!resp.ok) throw new Error('Not found');
        translations = await resp.json();
        currentLang = lang;
        localStorage.setItem('lang', lang);
        document.documentElement.lang = lang;
        translateUI();
        var lbl = document.getElementById('langLabel');
        if (lbl) lbl.textContent = lang.toUpperCase();
        document.querySelectorAll('.lang-option').forEach(function(opt) {
            opt.classList.toggle('active', opt.dataset.lang === lang);
        });
        return true;
    } catch(e) {
        console.warn('Lang load failed:', lang, e);
        if (lang !== 'ru') return await loadLang('ru');
        return false;
    }
}

function __(key) {
    return translations[key] || key;
}

function translateUI() {
    document.querySelectorAll('[data-i18n]').forEach(function(el) {
        el.textContent = __(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function(el) {
        el.placeholder = __(el.dataset.i18nPlaceholder);
    });
    document.querySelectorAll('[data-i18n-title]').forEach(function(el) {
        el.title = __(el.dataset.i18nTitle);
    });
    var hs = document.getElementById('headerSub');
    if (hs) hs.innerHTML = '<i class="fas fa-robot"></i> <span>' + __('header.chat_subtitle') + '</span>';
}

document.addEventListener('click', function(e) {
    var btn = document.getElementById('langBtn');
    var menu = document.getElementById('langMenu');
    if (btn && menu) {
        if (btn.contains(e.target)) {
            menu.classList.toggle('hidden');
        } else if (!menu.contains(e.target)) {
            menu.classList.add('hidden');
        }
    }
});

document.querySelectorAll('.lang-option').forEach(function(opt) {
    opt.addEventListener('click', function() {
        loadLang(opt.dataset.lang);
        document.getElementById('langMenu').classList.add('hidden');
    });
});

// ===== ПОЛНАЯ БАЗА МАРОК И МОДЕЛЕЙ (РФ рынок) =====
const MODELS_RU = {
    // === Россия ===
    "Lada": ["Granta", "Vesta", "Niva Legend", "Niva Travel", "Largus", "Kalina", "Priora", "XRAY", "Vesta Cross", "Largus Cross"],
    "Москвич": ["Москвич 3", "Москвич 3e", "Москвич 6", "Москвич 8"],
    "Evolute": ["Evolute i-PRO", "Evolute i-JOY", "Evolute i-SKY", "Evolute i-VAN"],
    "Aurus": ["Aurus Senat", "Aurus Komendant", "Aurus Arsenal"],
    "УАЗ": ["Патриот", "Хантер", "Буханка (2206)", "Профи", "Pickup", "Симбир"],
    "ГАЗ": ["ГАЗель Next", "ГАЗель NN", "ГАЗель Бизнес", "Соболь NN", "Валдай 8"],
    "КАМАЗ": ["Камаз 54901", "Камаз 43118", "Камаз 65115"],
    "Daewoo": ["Nexia", "Matiz", "Lanos", "Gentra", "Lacetti"],
    "ЗАЗ": ["ЗАЗ Sens", "ЗАЗ Vida", "ЗАЗ Chance"],

    // === Германия/Европа ===
    "Volkswagen": ["Polo", "Golf", "Passat", "Tiguan", "Touareg", "Jetta", "Teramont", "Taos", "ID.4", "ID.6", "Caddy", "Caravelle", "Multivan", "Amarok"],
    "Skoda": ["Octavia", "Rapid", "Kodiaq", "Karoq", "Superb", "Fabia", "Yeti", "Scala", "Enyaq iV"],
    "BMW": ["X3", "X5", "X1", "X7", "3 Series", "5 Series", "7 Series", "X4", "X6", "iX", "i5", "i4", "M3", "M5"],
    "Mercedes-Benz": ["GLC", "GLE", "E-Class", "C-Class", "GLA", "GLB", "S-Class", "G-Class", "GLS", "V-Class", "A-Class", "EQC", "EQS", "AMG GT"],
    "Audi": ["Q5", "Q7", "A6", "A4", "Q3", "A8", "e-tron", "RS6", "Q8", "A5", "A7", "Q2", "Q4 e-tron"],
    "Porsche": ["Cayenne", "Macan", "Panamera", "911", "Taycan", "Cayenne Coupe"],
    "Opel": ["Astra", "Mokka", "Crossland", "Grandland", "Insignia", "Combo", "Zafira", "Vivaro"],
    "Renault": ["Logan", "Duster", "Kaptur", "Arkana", "Sandero", "Megane", "Koleos", "Talisman", "Master"],
    "Peugeot": ["3008", "5008", "208", "2008", "508", "408", "Partner", "Boxer", "Landtrek"],
    "Citroen": ["C3", "C4", "C5 Aircross", "C4 Picasso", "Berlingo", "Jumper", "C4 Cactus"],
    "Fiat": ["Panda", "500", "Doblo", "Ducato", "Tipo", "500X", "Fullback"],
    "Volvo": ["XC60", "XC90", "XC40", "S90", "V60", "V90 Cross Country", "S60", "EX30", "EX90"],
    "Jaguar": ["F-Pace", "E-Pace", "I-Pace", "XF", "XE", "F-Type", "XJ"],
    "Land Rover": ["Range Rover", "Range Rover Sport", "Discovery", "Discovery Sport", "Velar", "Evoque", "Defender"],
    "Alfa Romeo": ["Giulia", "Stelvio", "Tonale", "Junior", "33 Stradale"],
    "Maserati": ["Grecale", "Levante", "MC20", "Quattroporte", "Ghibli", "GranTurismo", "GranCabrio"],
    "Ferrari": ["Purosangue", "SF90 Stradale", "296 GTB", "Roma", "F8 Tributo", "812 Superfast", "Monza SP2"],
    "Lamborghini": ["Urus", "Huracán", "Revuelto", "Temerario", "Countach LPI 800-4"],
    "Bentley": ["Bentayga", "Flying Spur", "Continental GT", "Mulsanne", "Batur"],
    "Rolls-Royce": ["Cullinan", "Ghost", "Phantom", "Spectre", "Dawn", "Wraith"],
    "Aston Martin": ["DBX", "DB12", "Vantage", "DBS", "Valhalla", "DBX707"],
    "Mini": ["Cooper", "Cooper S", "Countryman", "Clubman", "Aceman", "Electric", "JCW GP", "Cabrio"],
    "Smart": ["Fortwo", "Forfour", "#1", "#3", "#5", "Crossblade"],

    // === Корея ===
    "Kia": ["Rio", "Sportage", "Cerato", "Stinger", "Soul", "Seltos", "Sorento", "Picanto", "Mohave", "Carnival", "K5", "K9", "EV6", "EV9", "Niro"],
    "Hyundai": ["Solaris", "Creta", "Tucson", "Elantra", "Santa Fe", "Sonata", "Palisade", "Staria", "IONIQ 5", "IONIQ 6", "Kona", "Bayon", "Grandeur", "Nexo"],
    "Genesis": ["G80", "G90", "GV70", "GV80", "GV60"],
    "SsangYong": ["Korando", "Kyron", "Rexton", "Tivoli", "Musso", "Torres", "Actyon", "Stavic", "Chairman"],
    "KGM (KG Mobility)": ["Tivoli", "Korando", "Torres", "Musso", "Rexton", "Actyon", "Korando Emoción"],

    // === Япония ===
    "Toyota": ["Camry", "Corolla", "RAV4", "Land Cruiser 300", "Yaris", "Highlander", "C-HR", "Hilux", "Fortuner", "Corolla Cross", "Land Cruiser Prado", "Hiace", "Alphard", "Supra", "GR86", "bZ4x"],
    "Nissan": ["Qashqai", "X-Trail", "Terrano", "Almera", "Juke", "Murano", "Pathfinder", "Navara", "Note", "Leaf", "Ariya", "Sylphy", "Sentra", "Z"],
    "Mitsubishi": ["Outlander", "Pajero Sport", "L200", "ASX", "Eclipse Cross", "Lancer", "Delica", "Pajero", "Xpander"],
    "Mazda": ["CX-5", "CX-9", "CX-30", "CX-50", "CX-60", "Mazda 6", "MX-5", "Mazda 3", "CX-90", "MX-30"],
    "Suzuki": ["Vitara", "S-Cross", "Jimny", "Swift", "Ignis", "Baleno", "Across"],
    "Subaru": ["Forester", "Outback", "XV", "Impreza", "WRX", "Levorg", "Solterra"],
    "Honda": ["CR-V", "Civic", "Accord", "HR-V", "Pilot", "Jazz", "ZR-V"],
    "Lexus": ["RX", "NX", "LX", "ES", "UX", "GX", "LC", "LS", "TX", "RZ", "LM"],
    "Infiniti": ["QX50", "QX55", "QX60", "QX80", "Q50", "Q60"],

    // === США ===
    "Ford": ["Focus", "Kuga", "Explorer", "Transit", "Ranger", "Mustang", "Puma", "Bronco", "Bronco Sport", "Maverick", "Escape", "Edge", "F-150", "Mustang Mach-E", "Everest"],
    "Chevrolet": ["Niva", "Tahoe", "Camaro", "Cruze", "Traverse", "Suburban", "Trailblazer", "Captiva", "Blazer", "Malibu", "Silverado", "Equinox", "Tracker"],
    "Dodge": ["Durango", "Ram 1500", "Charger", "Challenger", "Grand Caravan"],
    "Jeep": ["Cherokee", "Grand Cherokee", "Wrangler", "Renegade", "Compass", "Gladiator", "Avenger"],
    "Cadillac": ["Escalade", "XT5", "XT4", "XT6", "CT5", "Lyriq"],
    "Lincoln": ["Navigator", "Aviator", "Corsair", "Nautilus"],
    "GMC": ["Yukon", "Acadia", "Terrain", "Sierra", "Canyon", "Hummer EV"],
    "Tesla": ["Model 3", "Model Y", "Model S", "Model X", "Cybertruck"],

    // === КИТАЙ (все бренды на рынке РФ) ===
    "Chery": ["Tiggo 4", "Tiggo 7 Pro", "Tiggo 8 Pro", "Tiggo 9", "Tiggo 8 Pro Max", "Arrizo 8", "Tiggo 4 Pro"],
    "Changan": ["CS35 Plus", "CS55 Plus", "CS75 Plus", "UNI-K", "UNI-T", "UNI-V", "Eado", "Lamore", "Raeton Plus", "Hunter Plus"],
    "Geely": ["Monjaro", "Atlas Pro", "Coolray", "Tugella", "Emgrand X7", "Okavango", "Geometry C", "Preface", "Boyue", "Xingyue L"],
    "Haval": ["Jolion", "F7", "F7x", "Dargo", "H6", "H9", "M6 Plus", "H3", "Big Dog", "Raptor", "Xiaolong Max"],
    "Great Wall": ["Poer Cannon (пикап)", "Wingle 7", "Wingle 5"],
    "Tank (GWM)": ["Tank 300", "Tank 500", "Tank 400", "Tank 700"],
    "Omoda": ["Omoda C5", "Omoda S5 GT", "Omoda C7"],
    "Jaecoo": ["Jaecoo J7", "Jaecoo J8", "Jaecoo J6"],
    "Exeed": ["Exeed LX", "Exeed TXL", "Exeed VX", "Exeed RX", "Exeed Sterra ES"],
    "BYD": ["BYD Atto 3 (Yuan Plus)", "BYD Song Plus", "BYD Qin Plus", "BYD Han", "BYD Tang", "BYD Dolphin", "BYD Seagull", "BYD Frigate 07", "BYD Yangwang U8"],
    "Zeekr": ["Zeekr 001", "Zeekr 007", "Zeekr 009", "Zeekr X", "Zeekr Mix"],
    "Li Auto": ["Li L7", "Li L8", "Li L9", "Li Mega", "Li L6"],
    "Neta": ["Neta U", "Neta V", "Neta S", "Neta GT", "Neta L"],
    "NIO": ["NIO ES6", "NIO ES8", "NIO ET5", "NIO ET7", "NIO EC6", "NIO EL6"],
    "Voyah": ["Voyah Free", "Voyah Dream", "Voyah Passion", "Voyah Courage"],
    "Dongfeng": ["Shine Max", "Aeolus Yixuan", "Aeolus Haohan", "Rich 6"],
    "GAC": ["GAC GS3", "GAC GS4", "GAC GS8", "GAC GN6", "GAC Empow", "GAC Aion Y", "GAC Aion S", "GAC Aion V"],
    "Hongqi": ["H5", "H9", "HS5", "HS7", "EHS9", "S9"],
    "FAW": ["Bestune B70", "Bestune T77", "Bestune T99", "Bestune T90"],
    "DFSK": ["DFSK 500", "DFSK 580", "DFSK 600", "DFSK ix5", "DFSK Mini EV"],
    "BAIC": ["BJ40", "BJ80", "X5", "X7", "EU5", "U5 Plus"],
    "Baojun": ["Baojun 510", "Baojun 530", "Baojun KiWi EV", "Baojun Yep", "Baojun Cloud"],
    "Wuling": ["Wuling Mini EV", "Wuling Bingo", "Wuling Xingchi", "Wuling Air EV", "Wuling Victory"],
    "Foton": ["Foton Tunland", "Foton Sauvana", "Foton Midi"],
    "HiPhi": ["HiPhi Y", "HiPhi Z", "HiPhi X", "HiPhi A"],
    "Xpeng": ["Xpeng G6", "Xpeng G9", "Xpeng P5", "Xpeng P7", "Xpeng X9"],
    "Lantu": ["Lantu Dreamer", "Lantu Free", "Lantu Passion"],
    "SWM": ["SWM G01", "SWM G05", "SWM X3", "SWM X7"],
    "MVM": ["MVM 110", "MVM 310", "MVM 530", "MVM X55 Pro"],
    "Avatr": ["Avatr 11", "Avatr 12"],
    "IM Motors": ["IM L6", "IM LS6", "IM LS7"],
    "AITO": ["AITO M5", "AITO M7", "AITO M9"],
    "Wey (GWM)": ["Wey Coffee 01", "Wey Coffee 02", "Wey Mocha", "Wey Latte"],
    "Ora": ["Ora Good Cat", "Ora Ballet Cat", "Ora Lightning Cat"],
    "Kaiyi": ["Kaiyi X3", "Kaiyi X5", "Kaiyi E5"],
    "Fengon": ["Fengon 500", "Fengon 580", "Fengon S560", "Fengon ix7"],
    "Skywell": ["Skywell HT-i", "Skywell ET5"],
    "Soueast": ["Soueast DX7", "Soueast DX5", "Soueast A5"],
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

// ===== Результаты (премиум) =====
function showResults(data) {
    lastRecommendationData = data;
    adviceDiv.innerHTML = `<p>${data.advice}</p>`;

    // ═══ Народный выбор ═══
    if (data.popular_pick) {
        popularPickDiv.classList.remove('hidden');
        popularContentDiv.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="flex:1;">
                    <div style="font-weight:600; font-size:14px; color:var(--text-primary);">${data.popular_pick.name}</div>
                    <div style="display:flex; gap:8px; align-items:center; margin-top:4px;">
                        <span style="font-size:15px; font-weight:700; color:var(--gold);">${data.popular_pick.price.toLocaleString('ru-RU')} ₽</span>
                        <span style="font-size:11px; color:var(--text-muted);">★ ${data.popular_pick.rating || 4.5}</span>
                    </div>
                </div>
                <a href="${data.popular_pick.link || '#'}" target="_blank" style="background:linear-gradient(135deg,var(--gold),#e6c200); color:#000; border:none; padding:8px 16px; border-radius:30px; font-weight:700; font-size:12px; cursor:pointer; text-decoration:none; white-space:nowrap;">Выбрать</a>
            </div>
        `;
    } else {
        popularPickDiv.classList.add('hidden');
    }

    // ═══ Товары с ценами ═══
    productListDiv.innerHTML = '';
    if (data.products && data.products.length > 0) {
        const sorted = [...data.products].sort((a, b) => a.price - b.price);
        sorted.forEach((product, idx) => {
            const card = document.createElement('div');
            card.className = 'product-card' + (idx === 0 ? ' best-price' : '');
            const starsHtml = product.rating ? '★'.repeat(Math.round(product.rating)) + '☆'.repeat(5 - Math.round(product.rating)) : '';
            card.innerHTML = `
                ${idx === 0 ? '<div class="best-price-badge"><i class="fas fa-crown"></i> Лучшая цена</div>' : ''}
                <img src="${product.image_url || 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2256%22 height=%2256%22 viewBox=%220 0 56 56%22%3E%3Crect width=%2256%22 height=%2256%22 fill=%22%230a0d14%22 rx=%228%22/%3E%3Ccircle cx=%2228%22 cy=%2228%22 r=%2212%22 fill=%22none%22 stroke=%22%2300d4ff%22 stroke-width=%221.5%22/%3E%3C/svg%3E'}" alt="${product.name}">
                <div class="product-info">
                    <div class="name">${product.name}</div>
                    <div class="rating-row">${starsHtml ? `<span class="stars">${starsHtml}</span>` : ''}<span class="rating-text">${product.rating ? product.rating.toFixed(1) : ''}</span></div>
                    <div class="${idx === 0 ? 'best-price-label' : 'price'}">${product.price.toLocaleString('ru-RU')} ₽</div>
                    <div class="source">${product.source || 'Партнёр'}</div>
                </div>
                <a href="${product.partner_link || '#'}" target="_blank" class="product-link">Купить</a>
            `;
            productListDiv.appendChild(card);
        });
    } else {
        productListDiv.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:20px;">Товаров не найдено.</p>';
    }

    // ═══ Кнопка поделиться ═══
    if (navigator.share) {
        shareBtn.classList.remove('hidden');
    } else {
        shareBtn.classList.add('hidden');
    }

    resultsOverlay.classList.remove('hidden');
}

// ===== Поделиться =====
shareBtn.addEventListener('click', () => {
    if (!lastRecommendationData) return;
    const text = `🚗 Авто Эксперт AI рекомендует:\n\n${lastRecommendationData.advice}`;
    if (navigator.share) {
        navigator.share({ title: 'Подбор шин AI', text });
    }
});

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
    loadLang('ru');
    switchMode('chat'); // по умолчанию чат
}

init();

// PWA — регистрация Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js')
            .then(registration => {
                console.log('[PWA] Service Worker зарегистрирован:', registration.scope);
            })
            .catch(error => {
                console.log('[PWA] Регистрация SW не удалась:', error);
            });
    });
}

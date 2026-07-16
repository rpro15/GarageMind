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
let currentMode = 'chat';
let userData = {
    brand: null,
    model: null,
    year: null,
    driving_style: null,
    season: null,
    budget: null
};
let isProcessing = false;
let lastRecommendationData = null;
// История сообщений для AI-чата
let chatHistory = [];

// ===== Сброс состояния чата =====
function resetUserData() {
    userData = {
        brand: null,
        model: null,
        year: null,
        driving_style: null,
        season: null,
        budget: null
    };
}

function resetChat() {
    resetUserData();
    isProcessing = false;
    chatHistory = [];
    messagesEl.innerHTML = '';
    lastRecommendationData = null;
    enableInput();
    startChat();
}

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

// ===== Русские названия брендов → латинские =====
const BRAND_RU_MAP = {
    "лада": "Lada", "лда": "Lada", "ваз": "Lada", "вз": "Lada",
    "тойота": "Toyota", "тота": "Toyota",
    "бмв": "BMW",
    "мерседес": "Mercedes-Benz", "мерс": "Mercedes-Benz",
    "ауди": "Audi",
    "киа": "Kia", "kіа": "Kia",
    "хёндэ": "Hyundai", "хендай": "Hyundai", "хендэ": "Hyundai", "хюндай": "Hyundai", "хундай": "Hyundai",
    "ниссан": "Nissan",
    "мазда": "Mazda",
    "форд": "Ford",
    "шкода": "Skoda", "skoda": "Skoda",
    "фольксваген": "Volkswagen", "фв": "Volkswagen", "vw": "Volkswagen", "фольц": "Volkswagen",
    "рено": "Renault",
    "митсубиси": "Mitsubishi", "мицубиси": "Mitsubishi", "митсу": "Mitsubishi",
    "лексус": "Lexus",
    "хонда": "Honda",
    "субару": "Subaru",
    "шевроле": "Chevrolet",
    "опель": "Opel",
    "пежо": "Peugeot",
    "ситроен": "Citroen",
    "вольво": "Volvo",
    "фиат": "Fiat",
    "порше": "Porsche", "porsche": "Porsche",
    "ягуар": "Jaguar",
    "ленд ровер": "Land Rover", "лендровер": "Land Rover",
    "мини": "Mini",
    "смарт": "Smart",
    "джили": "Geely", "geely": "Geely",
    "черри": "Chery", "cherу": "Chery",
    "хавал": "Haval", "haval": "Haval",
    "омода": "Omoda",
    "джейко": "Jaecoo",
    "уаз": "UAZ", "uaz": "UAZ",
    "газ": "GAZ",
    "москвич": "Moskvich", "москвич": "Moskvich",
    "киа": "Kia",
    "хендэ": "Hyundai",
    "тесла": "Tesla", "tesla": "Tesla",
    "китай": "Chery",
    "великий стіна": "Great Wall", "грейт вол": "Great Wall",
    "танк": "Tank (GWM)",
    "байк": "BYD", "byd": "BYD", "бивайди": "BYD",
    "зикр": "Zeekr", "zeekr": "Zeekr",
    "ли": "Li Auto",
    "нио": "NIO",
    "воя": "Voyah",
    "донфен": "Dongfeng",
    "джи ес": "GAC",
    "хончи": "Hongqi",
    "эксид": "Exeed",
    "чанъань": "Changan",
    "changan": "Changan",
    "овал": "Haval",
    "сузуки": "Suzuki",
    "субару": "Subaru",
    "инфинити": "Infiniti",
    "кадилак": "Cadillac",
    "линколн": "Lincoln",
    "додж": "Dodge",
    "джип": "Jeep",
    "крайслер": "Chrysler",
    "альфа ромео": "Alfa Romeo",
    "мазерат": "Maserati",
    "феррари": "Ferrari",
    "ламборгини": "Lamborghini",
    "бентли": "Bentley",
    "роллс ройс": "Rolls-Royce", "роллс": "Rolls-Royce",
    "астон мартин": "Aston Martin",
    "генсис": "Genesis", "генезис": "Genesis",
    "ссангионг": "SsangYong", "ссан йонг": "SsangYong",
    "рено": "Renault",
    "датсун": "Datsun",
    "ситроен": "Citroen",
    "хенде": "Hyundai",
    "шкода": "Skoda",
};

// ===== Транслит букв =====
const CYR_TO_LAT = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i',
    'й':'i','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t',
    'у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ъ':'','ы':'y','ь':'',
    'э':'e','ю':'iu','я':'ia',
};

function translit(text) {
    let r = '';
    for (const ch of text.toLowerCase()) {
        r += CYR_TO_LAT[ch] || ch;
    }
    return r;
}

function findBrand(text) {
    const t = text.toLowerCase().trim();
    // 1. Точное совпадение по BRAND_RU_MAP
    if (BRAND_RU_MAP[t]) return BRAND_RU_MAP[t];
    // 2. Поиск по ключам (первые слова)
    for (const [ru, en] of Object.entries(BRAND_RU_MAP)) {
        if (t.startsWith(ru) || t.includes(' ' + ru)) return en;
    }
    // 3. Прямое совпадение по латинским названиям
    for (const b of BRANDS) {
        if (t.includes(b.toLowerCase())) return b;
    }
    // 4. Транслитерируем и ищем
    const translitText = translit(text);
    for (const b of BRANDS) {
        if (translitText.includes(b.toLowerCase())) return b;
        if (b.toLowerCase().startsWith(translitText.slice(0, 3))) return b;
    }
    return null;
}

function findModel(text, brand) {
    const models = MODELS_RU[brand] || [];
    const t = text.toLowerCase();
    // Точное совпадение
    for (const m of models) {
        if (t.includes(m.toLowerCase())) return m;
    }
    // Транслит
    const tt = translit(text);
    for (const m of models) {
        if (tt.includes(m.toLowerCase())) return m;
    }
    // Префикс 3+ символа
    for (const m of models) {
        const prefix = m.toLowerCase().slice(0, Math.min(3, m.length));
        if (prefix.length >= 2 && tt.includes(prefix)) return m;
    }
    return null;
}

function findYear(text) {
    const nums = text.match(/\d{4}/);
    if (nums) {
        const y = parseInt(nums[0]);
        if (y >= 1980 && y <= 2030) return y;
    }
    return null;
}

function findDrivingStyle(text) {
    const t = text.toLowerCase();
    for (const [key, val] of Object.entries(DRIVING_STYLES)) {
        if (t.includes(key)) return val;
    }
    if (t.includes("ком")) return "comfort";
    if (t.includes("спорт")) return "sport";
    if (t.includes("динамик")) return "sport";
    if (t.includes("эко")) return "economy";
    return null;
}

function findSeason(text) {
    const t = text.toLowerCase();
    for (const [key, val] of Object.entries(SEASONS)) {
        if (t.includes(key)) return val;
    }
    for (const [key, val] of Object.entries(MONTHS_SEASON)) {
        if (t.includes(key)) return val;
    }
    if (t.includes("лет")) return "summer";
    if (t.includes("зим")) return "winter";
    if (t.includes("все")) return "all_season";
    if (t.includes("круглогодич")) return "all_season";
    return null;
}

function findBudget(text) {
    const t = text.toLowerCase();
    if (t.includes("нет") || t.includes("любой") || t.includes("не") || t.includes("пропустить") || t.includes("без")) return 0;
    const nums = text.match(/\d+/);
    if (nums) return parseInt(nums[0]);
    return null;
}

// ===== Умный парсер: вытаскивает всё что можно из одного сообщения =====
function smartParse(text) {
    const result = {};
    const brand = findBrand(text);
    if (brand) result.brand = brand;

    // Если знаем бренд — ищем модель среди известных для этого бренда
    if (brand) {
        const model = findModel(text, brand);
        if (model) result.model = model;
    }

    const year = findYear(text);
    if (year) result.year = year;

    const style = findDrivingStyle(text);
    if (style) result.driving_style = style;

    const season = findSeason(text);
    if (season) result.season = season;

    const budget = findBudget(text);
    if (budget) result.budget = budget;

    return result;
}

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

// ===== Умный диалог через AI =====
// AI-чат: отправляем историю и получаем умный ответ
async function askAI(text) {
    if (isProcessing) return;
    isProcessing = true;

    chatHistory.push({ role: 'user', content: text });
    addTyping();

    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000);

        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: chatHistory,
                user_data: { ...userData },
                user_id: tg?.initDataUnsafe?.user?.id?.toString() || 'anonymous'
            }),
            signal: controller.signal
        });

        clearTimeout(timeout);
        removeTyping();

        if (!response.ok) {
            // Если 404 — значит нет AI чата, парсим данные локально
            if (response.status === 404) {
                handleLocalParse(text);
                return;
            }
            addMessage('Извините, AI временно недоступен. Попробуйте ещё раз.');
            isProcessing = false;
            return;
        }

        const data = await response.json();

        // Обновляем данные, если AI что-то распарсил
        if (data.user_data) {
            for (const [key, val] of Object.entries(data.user_data)) {
                if (val !== null && val !== undefined && val !== '') {
                    if (userData[key] === null || userData[key] === undefined || userData[key] === '') {
                        userData[key] = val;
                    }
                }
            }
        }

        // Добавляем ответ AI в историю
        chatHistory.push({ role: 'assistant', content: data.reply });
        addMessage(data.reply);

        // Если AI считает что данных достаточно — делаем подбор
        if (data.ready) {
            const allFilled = userData.brand && userData.model && userData.year &&
                userData.driving_style && userData.season;
            if (allFilled) {
                await new Promise(resolve => setTimeout(resolve, 600));
                await sendRecommendation();
            }
        }

        } catch (err) {
        removeTyping();
        if (err.name === 'AbortError') {
            addMessage('⏱️ Превышено время ожидания. Попробуйте ещё раз.');
            handleLocalParse(text);
        } else {
            addMessage(`⚠️ Ошибка: ${err.message}. Использую локальный парсинг...`);
            handleLocalParse(text);
        }
        console.error(err);
    } finally {
        isProcessing = false;
        enableInput();
    }
}

// ===== Локальный парсинг (резервный, если AI недоступен) =====
function handleLocalParse(text) {
    const parsed = smartParse(text);

    // Обновляем userData из распарсенных данных
    let updated = false;
    for (const [key, val] of Object.entries(parsed)) {
        if (val !== null && val !== undefined && val !== '') {
            if (!userData[key]) {
                userData[key] = val;
                updated = true;
            }
        }
    }

    // Формируем ответ
    const missing = [];
    if (!userData.brand) missing.push('марку авто');
    if (!userData.model && userData.brand) missing.push('модель');
    if (!userData.year) missing.push('год выпуска');
    if (!userData.driving_style) missing.push('стиль вождения (комфорт/спорт/эконом)');
    if (!userData.season) missing.push('сезон (лето/зима/всесезон)');

    if (missing.length > 0) {
        const brandDisplay = userData.brand ? `\n\n🚗 **Сейчас выбрано**: ${userData.brand} ${userData.model || ''} ${userData.year || ''}`.trim() : '';
        addMessage(`✅ Принято!${brandDisplay}\n\n📋 Укажите, пожалуйста: ${missing.join(', ')}.`);
    } else {
        // Все данные есть — делаем подбор
        addTyping();
        setTimeout(() => {
            removeTyping();
            addMessage('✅ Все данные собраны! Делаю подбор...');
            sendRecommendation();
        }, 500);
    }
}

function handleUserInput(text) {
    if (isProcessing) {
        addMessage('⏳ Подождите, предыдущий запрос ещё обрабатывается...');
        return;
    }
    text = text.trim();
    if (!text) return;

    addMessage(text, 'user');
    chatInput.value = '';
    chatInput.disabled = true;

    // Пробуем AI-чат, если упадёт — парсим локально
    askAI(text);
}

// Разблокировка поля ввода после обработки
function enableInput() {
    chatInput.disabled = false;
    chatInput.focus();
}

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
            startChat();
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

// ===== Старт чата с приветствием =====
async function startChat() {
    addTyping();
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 10000);

        const resp = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: [{ role: 'user', content: 'Привет! Нужна помощь с выбором шин.' }],
                user_data: { ...userData },
                user_id: 'new_user'
            }),
            signal: controller.signal
        });

        clearTimeout(timeout);
        removeTyping();

        if (resp.ok) {
            const data = await resp.json();
            if (data.reply) {
                chatHistory.push({ role: 'assistant', content: data.reply });
                addMessage(data.reply);
                return;
            }
        }
    } catch(e) {
        // fallback
    }

    removeTyping();
    // Приветствие в любом случае (даже если AI недоступен)
    addMessage("Привет! Я AI-консультант по подбору шин 🚗\n\nНапишите марку авто (можно на русском), например:\n«Тойота Камри 2020, комфорт, лето»\n\nЯ помогу подобрать лучшие шины! 😊");
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
    checkShowResetButton();
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

// Показываем кнопку "Начать заново" после 4+ сообщений
function checkShowResetButton() {
    const msgCount = messagesEl.querySelectorAll('.msg').length;
    const existingBtn = document.getElementById('resetChatBtn');
    if (msgCount >= 4 && !existingBtn) {
        addResetButton();
    } else if (msgCount < 4 && existingBtn) {
        existingBtn.remove();
    }
}

// ===== Общий запрос к API =====
async function sendRecommendation(payloadOverride) {
    if (isProcessing) return;
    isProcessing = true;

    const payload = payloadOverride || {
        brand: userData.brand,
        model: userData.model,
        year: userData.year,
        driving_style: userData.driving_style,
        season: userData.season,
        budget: userData.budget,
        user_id: tg?.initDataUnsafe?.user?.id?.toString() || 'anonymous'
    };

    // Проверка обязательных полей
    if (!payload.brand || !payload.model || !payload.year || !payload.driving_style) {
        addMessage('⚠️ Не хватает данных. Укажите марку, модель, год и стиль вождения.');
        isProcessing = false;
        return;
    }

    if (currentMode === 'chat') {
        addMessage("🔍 Анализирую ваш авто, подбираю лучшие шины...");
    }
    addTyping();
    loadingResults.classList.remove('hidden');

    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 45000);

        const response = await fetch(`${API_BASE}/api/recommend_tires`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            signal: controller.signal
        });

        clearTimeout(timeout);
        removeTyping();

        if (!response.ok) {
            loadingResults.classList.add('hidden');
            let errMsg = 'Что-то пошло не так';
            try {
                const err = await response.json();
                errMsg = err.error || err.message || errMsg;
                if (typeof errMsg === 'object') errMsg = errMsg.message || JSON.stringify(errMsg);
            } catch(e) {}
            if (currentMode === 'chat') addMessage(`❌ Ошибка: ${errMsg}`);
            isProcessing = false;
            return;
        }

        const data = await response.json();
        loadingResults.classList.add('hidden');
        showResults(data);

        if (currentMode === 'chat') {
            addMessage("✅ Готово! Смотрите рекомендации ниже 👇");
            // Не сбрасываем userData, чтобы пользователь мог продолжить
        }

        if (tg) {
            try { tg.sendData(JSON.stringify({ action: 'recommendation', ...data })); } catch(e) {}
        }

    } catch (err) {
        removeTyping();
        loadingResults.classList.add('hidden');
        let errMsg = err.message;
        if (err.name === 'AbortError') errMsg = 'Превышено время ожидания';
        if (currentMode === 'chat') addMessage(`⚠️ ${errMsg}. Попробуйте ещё раз позже.`);
        console.error(err);
    } finally {
        isProcessing = false;
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

// ===== Камера / фото =====
const attachBtn = $('attachBtn');
let fileInput = null;

function initCamera() {
    // Создаём скрытый input для выбора файла
    fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput);

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Показываем что обрабатываем
        addMessage("📸 Анализирую фото...", 'bot');
        addTyping();

        try {
            const formData = new FormData();
            formData.append('image', file);

            const response = await fetch(`${API_BASE}/api/recognize-part`, {
                method: 'POST',
                body: formData
            });

            removeTyping();

            if (!response.ok) {
                addMessage("Не удалось распознать фото. Попробуйте другой ракурс.");
                return;
            }

            const data = await response.json();

            // Показываем результат
            let resultText = "🔍 Результат распознавания:\n";
            if (data.brand) resultText += `Марка: ${data.brand}\n`;
            if (data.model) resultText += `Модель: ${data.model}\n`;
            if (data.year) resultText += `Год: ${data.year}\n`;
            if (data.tire_size) resultText += `Размер шин: ${data.tire_size}\n`;
            if (data.vin) resultText += `VIN: ${data.vin}\n`;
            if (data.description) resultText += `Описание: ${data.description}\n`;

            addMessage(resultText);

            // Обновляем userData из распознанного
            if (data.brand) userData.brand = data.brand;
            if (data.model) userData.model = data.model;
            if (data.year) userData.year = parseInt(data.year);

            // Продолжаем диалог с AI
            const missingData = [];
            if (!userData.brand) missingData.push('марка');
            if (!userData.model) missingData.push('модель');
            if (!userData.year) missingData.push('год');
            if (!userData.driving_style) missingData.push('стиль вождения');
            if (!userData.season) missingData.push('сезон');

            if (missingData.length > 0) {
                // Добавляем в историю AI то что распознали
                let aiContext = `Я загрузил фото. Распознано: `;
                if (data.brand) aiContext += `${data.brand} `;
                if (data.model) aiContext += `${data.model} `;
                if (data.year) aiContext += `${data.year}`;
                chatHistory.push({ role: 'user', content: aiContext.trim() });

                // Спрашиваем AI что дальше
                const aiResp = await fetch(`${API_BASE}/api/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        messages: chatHistory,
                        user_data: { ...userData },
                        user_id: tg?.initDataUnsafe?.user?.id?.toString() || 'anonymous'
                    })
                });
                if (aiResp.ok) {
                    const aiData = await aiResp.json();
                    chatHistory.push({ role: 'assistant', content: aiData.reply });
                    addMessage(aiData.reply);
                }
            }

        } catch (err) {
            removeTyping();
            addMessage(`Ошибка: ${err.message}`);
        }

        // Очищаем input для повторного выбора
        fileInput.value = '';
    });
}

attachBtn.addEventListener('click', () => {
    if (fileInput) {
        fileInput.click(); // Открывает галерею/камеру
    }
});

closeResultsBtn.addEventListener('click', () => resultsOverlay.classList.add('hidden'));
resultsOverlay.addEventListener('click', (e) => {
    if (e.target === resultsOverlay) resultsOverlay.classList.add('hidden');
});

// ===== Кнопка "Новый поиск" в чате =====
function addResetButton() {
    const existingBtn = document.getElementById('resetChatBtn');
    if (existingBtn) return;
    
    const btn = document.createElement('button');
    btn.id = 'resetChatBtn';
    btn.className = 'reset-chat-btn';
    btn.innerHTML = '<i class="fas fa-redo"></i> Начать заново';
    btn.addEventListener('click', () => {
        resetChat();
        btn.remove();
    });
    messagesEl.appendChild(btn);
}

// ===== Старт =====
function init() {
    initSpeech();
    initCamera();
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

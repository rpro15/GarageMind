import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'services/api_service.dart';
import 'screens/home_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/form_screen.dart';
import 'screens/result_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AppState()),
      ],
      child: const AvtoExpertApp(),
    ),
  );
}

class AvtoExpertApp extends StatelessWidget {
  const AvtoExpertApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Авто Эксперт AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF080B14),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00D4FF),
          secondary: Color(0xFFFF6B35),
          surface: Color(0xFF0E1422),
          error: Color(0xFFFF1744),
        ),
        textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0E1422),
          elevation: 0,
          centerTitle: true,
        ),
        cardTheme: CardTheme(
          color: const Color(0xFF131B2C),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: Color(0xFF1B2740), width: 1),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF0A0F1C),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: Color(0xFF1B2740)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: Color(0xFF00D4FF), width: 2),
          ),
          labelStyle: const TextStyle(color: Color(0xFF6B80A0)),
        ),
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const HomeScreen(),
        '/chat': (context) => const ChatScreen(),
        '/form': (context) => const FormScreen(),
        '/result': (context) => const ResultScreen(),
      },
    );
  }
}

// ====== Глобальное состояние приложения ======
class AppState extends ChangeNotifier {
  final ApiService _api = ApiService();

  // Режим
  bool isChatMode = true;

  // Данные чата
  final List<ChatMessage> messages = [];
  bool isLoading = false;

  // Данные формы
  String? selectedBrand;
  String? selectedModel;
  int? selectedYear;
  String drivingStyle = 'comfort';
  String season = 'summer';
  int? budget;

  // Результаты
  String? advice;
  List<ProductItem> products = [];
  Map<String, List<String>> brandsCache = {};

  void switchMode(bool chat) {
    isChatMode = chat;
    notifyListeners();
  }

  Future<List<String>> getBrands() async {
    if (brandsCache.containsKey('_brands')) {
      return brandsCache['_brands']!;
    }
    final brands = await _api.fetchBrands();
    brandsCache['_brands'] = brands;
    return brands;
  }

  Future<List<String>> getModels(String brand) async {
    if (brandsCache.containsKey(brand)) {
      return brandsCache[brand]!;
    }
    final models = await _api.fetchModels(brand);
    brandsCache[brand] = models;
    return models;
  }

  // Чат — отправка сообщения
  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;
    messages.add(ChatMessage(text: text, isUser: true));
    isLoading = true;
    notifyListeners();

    // Имитация ответа AI заглушкой (пока нет DeepSeek)
    await Future.delayed(const Duration(milliseconds: 800));

    final response = _generateMockResponse(text);
    messages.add(ChatMessage(text: response, isUser: false));
    isLoading = false;
    notifyListeners();
  }

  String _generateMockResponse(String userText) {
    final t = userText.toLowerCase();
    if (t.contains('lada') || t.contains('лада') || t.contains('vesta') || t.contains('granta')) {
      return 'Отличный выбор! Для Lada Vesta рекомендую:\n\n'
          '🔹 Лето: Michelin X-Ice 185/65R15 — 8 900 ₽\n'
          '🔹 Зима: Nokian Hakka 7 185/65R15 — 11 200 ₽\n'
          '🔹 Бюджет: Triangle TR928 185/65R15 — 4 500 ₽\n\n'
          'Какой сезон вас интересует?';
    }
    if (t.contains('toyota') || t.contains('тойота') || t.contains('camry') || t.contains('камри')) {
      return 'Toyota Camry — надёжный выбор! Рекомендую шины:\n\n'
          '🔹 Лето: Continental PremiumContact 6 215/60R16 — 12 500 ₽\n'
          '🔹 Зима: Bridgestone Blizzak VRX 215/60R16 — 15 800 ₽\n'
          '🔹 Всесезон: Michelin CrossClimate+ 215/60R16 — 14 200 ₽\n\n'
          'Хотите сравнить цены на Ozon и Wildberries?';
    }
    if (t.contains('bmw') || t.contains('x5') || t.contains('mercedes') || t.contains('audi')) {
      return 'Премиум-авто — премиум-шины! Рекомендую:\n\n'
          '🔹 Лето: Pirelli P Zero 255/50R19 — 22 400 ₽\n'
          '🔹 Зима: Continental IceContact 3 255/50R19 — 26 500 ₽\n'
          '🔹 Спорт: Michelin Pilot Sport 4S 255/50R19 — 28 900 ₽\n\n'
          'Какой бюджет рассматриваете?';
    }
    return 'Здравствуйте! Я AI-консультант по подбору шин 🚗\n\n'
        'Расскажите о вашем автомобиле. Напишите марку и модель.\n'
        'Например: "Toyota Camry 2020" или "Lada Vesta"';
  }

  // Отправка формы
  Future<void> submitForm() async {
    if (selectedBrand == null || selectedModel == null || selectedYear == null) return;
    isLoading = true;
    notifyListeners();

    await Future.delayed(const Duration(milliseconds: 1200));

    advice = 'Рекомендуем шины для $selectedBrand $selectedModel ($selectedYear):\n\n'
        'Оптимальный размер: 205/55R16\n'
        'Индекс нагрузки: 91\n'
        'Индекс скорости: H (до 210 км/ч)';
    products = [
      ProductItem(name: 'Michelin X-Ice 205/55R16', price: 12400, source: 'Ozon'),
      ProductItem(name: 'Nokian Hakka 7 205/55R16', price: 11800, source: 'Wildberries'),
      ProductItem(name: 'Continental WinterContact 205/55R16', price: 13500, source: 'Яндекс.Маркет'),
    ];

    isLoading = false;
    notifyListeners();
  }
}

// Модели
class ChatMessage {
  final String text;
  final bool isUser;
  ChatMessage({required this.text, required this.isUser});
}

class ProductItem {
  final String name;
  final int price;
  final String source;
  ProductItem({required this.name, required this.price, required this.source});
}

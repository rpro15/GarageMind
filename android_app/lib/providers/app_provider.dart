import 'package:flutter/foundation.dart';
import '../models/tire_request.dart';
import '../models/product.dart';
import '../services/api_service.dart';

enum AppMode { chat, form }
enum ChatStep {
  brand, model, year, region, drivingStyle, season,
  productType, tireSize, wheelMaterial, deliverySpeed, budget, done
}

class AppProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  // ===== Состояние =====
  AppMode mode = AppMode.chat;
  ChatStep chatStep = ChatStep.brand;
  bool isLoading = false;
  bool isProcessing = false;

  // Данные пользователя
  String? selectedBrand;
  String? selectedModel;
  int? selectedYear;
  DrivingStyle? selectedStyle;
  Season? selectedSeason;
  int? selectedBudget;
  
  // Новые поля
  String region = 'Москва';
  String city = 'Москва';
  ProductType productType = ProductType.tires;
  DeliverySpeed deliverySpeed = DeliverySpeed.any;
  String? wheelMaterial; // "steel" | "alloy"
  int? tireWidth;
  int? tireProfile;
  int? tireDiameter;

  // Результаты
  RecommendationResult? result;
  String? errorMessage;

  // Данные для форм
  List<String> brands = [];
  List<String> models = [];
  bool brandsLoaded = false;

  // ===== Загрузка брендов =====
  Future<void> loadBrands() async {
    if (brandsLoaded) return;
    try {
      brands = await _api.getBrands();
      brandsLoaded = true;
      notifyListeners();
    } catch (e) {
      errorMessage = 'Ошибка загрузки брендов: $e';
      notifyListeners();
    }
  }

  Future<void> loadModels(String brand) async {
    try {
      models = await _api.getModels(brand);
      notifyListeners();
    } catch (e) {
      models = [];
      notifyListeners();
    }
  }

  // ===== Сброс =====
  void reset() {
    selectedBrand = null;
    selectedModel = null;
    selectedYear = null;
    selectedStyle = null;
    selectedSeason = null;
    selectedBudget = null;
    region = 'Москва';
    city = 'Москва';
    productType = ProductType.tires;
    deliverySpeed = DeliverySpeed.any;
    wheelMaterial = null;
    tireWidth = null;
    tireProfile = null;
    tireDiameter = null;
    result = null;
    errorMessage = null;
    chatStep = ChatStep.brand;
    isProcessing = false;
    notifyListeners();
  }

  void switchMode(AppMode newMode) {
    mode = newMode;
    notifyListeners();
  }

  // ===== Подсказка для чата =====
  String get chatHint {
    switch (chatStep) {
      case ChatStep.brand: return 'Напишите марку автомобиля...';
      case ChatStep.model: return 'Модель автомобиля...';
      case ChatStep.year: return 'Год выпуска (1980-2026)...';
      case ChatStep.region: return 'Ваш регион и город...';
      case ChatStep.drivingStyle: return 'Комфорт, Спорт или Эконом...';
      case ChatStep.season: return 'Лето, Зима или Всесезон...';
      case ChatStep.productType: return 'Шины, диски или колёса в сборе...';
      case ChatStep.tireSize: return 'Размер шин (напр. 205/55 R16) или "не знаю"...';
      case ChatStep.wheelMaterial: return 'Штамповка или литьё?';
      case ChatStep.deliverySpeed: return 'Срочно / В течение недели / Не важно...';
      case ChatStep.budget: return 'Бюджет в рублях или "любой"...';
      case ChatStep.done: return '...';
    }
  }

  // ===== Обработка чата =====
  void handleChatInput(String text) {
    if (isProcessing) return;
    
    switch (chatStep) {
      case ChatStep.brand:
        final found = brands.where(
          (b) => b.toLowerCase().contains(text.toLowerCase())
        ).toList();
        if (found.isNotEmpty) {
          selectedBrand = found.first;
          chatStep = ChatStep.model;
          loadModels(selectedBrand!);
          notifyListeners();
        } else {
          errorMessage = 'Марка не найдена. Попробуйте: ${brands.take(6).join(", ")}...';
          notifyListeners();
        }
        break;

      case ChatStep.model:
        final found = models.where(
          (m) => m.toLowerCase().contains(text.toLowerCase())
        ).toList();
        if (found.isNotEmpty) {
          selectedModel = found.first;
          chatStep = ChatStep.year;
          notifyListeners();
        } else {
          errorMessage = 'Модель не найдена для $selectedBrand';
          notifyListeners();
        }
        break;

      case ChatStep.year:
        final year = int.tryParse(text.trim());
        if (year != null && year >= 1980 && year <= 2026) {
          selectedYear = year;
          chatStep = ChatStep.region;
          notifyListeners();
        } else {
          errorMessage = 'Введите год цифрами (1980-2026)';
          notifyListeners();
        }
        break;

      case ChatStep.region:
        // Парсим: "Москва" или "Краснодар, Сочи"
        final parts = text.split(RegExp(r'[, ]{1,3}')).where((p) => p.isNotEmpty).toList();
        if (parts.length >= 2) {
          region = parts[0];
          city = parts[1];
        } else {
          region = text.trim();
          city = text.trim();
        }
        chatStep = ChatStep.drivingStyle;
        notifyListeners();
        break;

      case ChatStep.drivingStyle:
        final t = text.toLowerCase();
        if (t.contains('комфорт') || t.contains('comfort')) {
          selectedStyle = DrivingStyle.comfort;
        } else if (t.contains('спорт') || t.contains('sport')) {
          selectedStyle = DrivingStyle.sport;
        } else if (t.contains('эконом') || t.contains('economy')) {
          selectedStyle = DrivingStyle.economy;
        }
        if (selectedStyle != null) {
          chatStep = ChatStep.season;
          notifyListeners();
        } else {
          errorMessage = 'Выберите: Комфорт, Спорт или Эконом';
          notifyListeners();
        }
        break;

      case ChatStep.season:
        final t = text.toLowerCase();
        if (t.contains('лето') || t.contains('summer')) {
          selectedSeason = Season.summer;
        } else if (t.contains('зим') || t.contains('winter')) {
          selectedSeason = Season.winter;
        } else if (t.contains('все') || t.contains('all')) {
          selectedSeason = Season.allSeason;
        }
        if (selectedSeason != null) {
          chatStep = ChatStep.productType;
          notifyListeners();
        } else {
          errorMessage = 'Выберите: Лето, Зима или Всесезон';
          notifyListeners();
        }
        break;

      case ChatStep.productType:
        final t = text.toLowerCase();
        if (t.contains('диск') || t.contains('wheel')) {
          productType = ProductType.wheels;
          chatStep = ChatStep.wheelMaterial;
        } else if (t.contains('сбор') || t.contains('assembly') || t.contains('комплект')) {
          productType = ProductType.assembly;
          chatStep = ChatStep.wheelMaterial;
        } else {
          productType = ProductType.tires;
          chatStep = ChatStep.tireSize;
        }
        notifyListeners();
        break;

      case ChatStep.tireSize:
        // Парсим: "205/55 R16" или "не знаю"
        final match = RegExp(r'(\d+)\s*[/]\s*(\d+)\s*R\s*(\d+)').firstMatch(text);
        if (match != null) {
          tireWidth = int.parse(match.group(1)!);
          tireProfile = int.parse(match.group(2)!);
          tireDiameter = int.parse(match.group(3)!);
        }
        chatStep = ChatStep.deliverySpeed;
        notifyListeners();
        break;

      case ChatStep.wheelMaterial:
        final t = text.toLowerCase();
        if (t.contains('штамп') || t.contains('steel') || t.contains('желез')) {
          wheelMaterial = 'steel';
        } else if (t.contains('лит') || t.contains('alloy')) {
          wheelMaterial = 'alloy';
        }
        chatStep = ChatStep.tireSize;
        notifyListeners();
        break;

      case ChatStep.deliverySpeed:
        final t = text.toLowerCase();
        if (t.contains('сроч') || t.contains('urgent')) {
          deliverySpeed = DeliverySpeed.urgent;
        } else if (t.contains('недел') || t.contains('week')) {
          deliverySpeed = DeliverySpeed.withinWeek;
        } else if (t.contains('3') || t.contains('three')) {
          deliverySpeed = DeliverySpeed.within3Days;
        } else {
          deliverySpeed = DeliverySpeed.any;
        }
        chatStep = ChatStep.budget;
        notifyListeners();
        break;

      case ChatStep.budget:
        final t = text.toLowerCase();
        if (t.contains('нет') || t.contains('any') || t.contains('любой')) {
          selectedBudget = null;
        } else {
          selectedBudget = int.tryParse(text.replaceAll(RegExp(r'[^0-9]'), ''));
        }
        chatStep = ChatStep.done;
        sendRequest();
        break;

      case ChatStep.done:
        break;
    }
  }

  // ===== Отправка запроса =====
  Future<void> sendRequest() async {
    isLoading = true;
    isProcessing = true;
    notifyListeners();

    try {
      final preferences = TirePreferences(
        tireWidth: tireWidth,
        tireProfile: tireProfile,
        tireDiameter: tireDiameter,
        wheelMaterial: wheelMaterial,
        productType: productType,
        deliverySpeed: deliverySpeed,
        onlyInStock: true,
      );
      final location = UserLocation(
        region: region,
        city: city,
      );
      final request = TireRequest(
        brand: selectedBrand ?? '',
        model: selectedModel ?? '',
        year: selectedYear ?? 2024,
        drivingStyle: selectedStyle ?? DrivingStyle.comfort,
        season: selectedSeason,
        budget: selectedBudget,
        preferences: preferences,
        location: location,
      );
      result = await _api.getRecommendation(request);
      errorMessage = null;
    } catch (e) {
      errorMessage = 'Ошибка: $e';
    }

    isLoading = false;
    isProcessing = false;
    notifyListeners();
  }

  // ===== Форма =====
  Future<void> submitForm({
    required String brand,
    required String model,
    required int year,
    required DrivingStyle style,
    required Season season,
    int? budget,
    String? region,
    String? city,
    ProductType? productType,
    DeliverySpeed? deliverySpeed,
  }) async {
    isLoading = true;
    notifyListeners();

    try {
      final preferences = TirePreferences(
        tireWidth: tireWidth,
        tireProfile: tireProfile,
        tireDiameter: tireDiameter,
        wheelMaterial: wheelMaterial,
        productType: productType ?? ProductType.tires,
        deliverySpeed: deliverySpeed ?? DeliverySpeed.any,
        onlyInStock: true,
      );
      final location = UserLocation(
        region: region ?? 'Москва',
        city: city ?? 'Москва',
      );
      final request = TireRequest(
        brand: brand,
        model: model,
        year: year,
        drivingStyle: style,
        season: season,
        budget: budget,
        preferences: preferences,
        location: location,
      );
      result = await _api.getRecommendation(request);
      errorMessage = null;
    } catch (e) {
      errorMessage = 'Ошибка: $e';
    }

    isLoading = false;
    notifyListeners();
  }
}

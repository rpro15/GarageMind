import 'package:flutter/foundation.dart';
import '../models/tire_request.dart';
import '../models/product.dart';
import '../services/api_service.dart';

enum AppMode { chat, form }
enum ChatStep {
  brand, model, year, drivingStyle, season, budget, done
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
          chatStep = ChatStep.drivingStyle;
          notifyListeners();
        } else {
          errorMessage = 'Введите год цифрами (1980-2026)';
          notifyListeners();
        }
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
          chatStep = ChatStep.budget;
          notifyListeners();
        } else {
          errorMessage = 'Выберите: Лето, Зима или Всесезон';
          notifyListeners();
        }
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
      final request = TireRequest(
        brand: selectedBrand ?? '',
        model: selectedModel ?? '',
        year: selectedYear ?? 2024,
        drivingStyle: selectedStyle ?? DrivingStyle.comfort,
        season: selectedSeason,
        budget: selectedBudget,
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
  }) async {
    isLoading = true;
    notifyListeners();

    try {
      final request = TireRequest(
        brand: brand,
        model: model,
        year: year,
        drivingStyle: style,
        season: season,
        budget: budget,
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

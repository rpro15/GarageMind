import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  // Для Android эмулятора используем 10.0.2.2, для реального устройства — IP сервера
  static const String _baseUrl = 'http://10.0.2.2:8000';

  final http.Client _client;

  ApiService({http.Client? client}) : _client = client ?? http.Client();

  /// Загрузка списка марок
  Future<List<String>> fetchBrands() async {
    try {
      final response = await _client.get(
        Uri.parse('$_baseUrl/api/brands'),
        headers: {'Accept': 'application/json'},
      );
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.cast<String>();
      }
    } catch (e) {
      print('fetchBrands error: $e');
    }
    return _defaultBrands();
  }

  /// Загрузка моделей для марки
  Future<List<String>> fetchModels(String brand) async {
    try {
      final response = await _client.get(
        Uri.parse('$_baseUrl/api/models?brand=$brand'),
        headers: {'Accept': 'application/json'},
      );
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.cast<String>();
      }
    } catch (e) {
      print('fetchModels error: $e');
    }
    return _defaultModels(brand);
  }

  /// Отправка запроса на подбор шин
  Future<Map<String, dynamic>?> recommendTires({
    required String brand,
    required String model,
    required int year,
    required String drivingStyle,
    String? season,
    int? budget,
  }) async {
    try {
      final body = {
        'brand': brand,
        'model': model,
        'year': year,
        'driving_style': drivingStyle,
        if (season != null) 'season': season,
        if (budget != null) 'budget': budget,
      };
      final response = await _client.post(
        Uri.parse('$_baseUrl/api/recommend_tires'),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode(body),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      print('recommendTires error: $e');
    }
    return null;
  }

  /// Распознавание детали по фото (base64)
  Future<Map<String, dynamic>?> recognizePart(String imageBase64) async {
    try {
      final response = await _client.post(
        Uri.parse('$_baseUrl/api/recognize-part'),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode({'image_base64': imageBase64}),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      print('recognizePart error: $e');
    }
    return null;
  }

  // Локальные заглушки на случай недоступности сервера
  List<String> _defaultBrands() {
    return [
      'Lada', 'Kia', 'Hyundai', 'Toyota', 'Volkswagen',
      'Skoda', 'Nissan', 'Mitsubishi', 'BMW', 'Mercedes-Benz',
      'Audi', 'Ford', 'Renault', 'Chevrolet', 'Mazda',
    ];
  }

  List<String> _defaultModels(String brand) {
    const models = {
      'Lada': ['Granta', 'Vesta', 'Niva Legend', 'Niva Travel', 'Largus'],
      'Kia': ['Rio', 'Sportage', 'Cerato', 'Soul', 'Seltos'],
      'Hyundai': ['Solaris', 'Creta', 'Tucson', 'Elantra', 'Santa Fe'],
      'Toyota': ['Camry', 'Corolla', 'RAV4', 'Land Cruiser 300', 'Yaris'],
      'Volkswagen': ['Polo', 'Golf', 'Passat', 'Tiguan', 'Jetta'],
    };
    return models[brand] ?? ['Стандартная'];
  }

  void dispose() {
    _client.close();
  }
}

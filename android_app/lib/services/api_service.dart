import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/tire_request.dart';
import '../models/product.dart';
import '../models/car_brand.dart';

class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000/api';

  Future<RecommendationResult> getRecommendation(TireRequest request) async {
    final response = await http.post(
      Uri.parse('$baseUrl/recommend_tires'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(request.toJson()),
    );
    if (response.statusCode == 200) {
      return RecommendationResult.fromJson(jsonDecode(response.body));
    }
    throw Exception('Ошибка: ${response.statusCode} ${response.body}');
  }

  Future<List<String>> getBrands() async {
    final response = await http.get(Uri.parse('$baseUrl/brands'));
    if (response.statusCode == 200) {
      return List<String>.from(jsonDecode(response.body));
    }
    throw Exception('Ошибка загрузки брендов');
  }

  Future<List<String>> getModels(String brand) async {
    final response = await http.get(Uri.parse('$baseUrl/models?brand=$brand'));
    if (response.statusCode == 200) {
      return List<String>.from(jsonDecode(response.body));
    }
    throw Exception('Ошибка загрузки моделей');
  }
}

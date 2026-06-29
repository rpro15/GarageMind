import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;
import 'package:shared_preferences/shared_preferences.dart';

class LocalizationService {
  static const String _prefKey = 'app_language';
  static const String defaultLang = 'ru';

  String _currentLang = defaultLang;
  Map<String, String> _translations = {};
  
  String get currentLang => _currentLang;
  bool get isLoaded => _translations.isNotEmpty;

  Future<void> loadLanguage(String langCode) async {
    try {
      final jsonStr = await rootBundle.loadString('assets/lang/$langCode.json');
      final map = jsonDecode(jsonStr) as Map<String, dynamic>;
      _translations = map.map((k, v) => MapEntry(k, v.toString()));
      _currentLang = langCode;
      
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefKey, langCode);
    } catch (e) {
      if (langCode != defaultLang) {
        await loadLanguage(defaultLang);
      }
    }
  }

  Future<void> loadSavedLanguage() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_prefKey) ?? defaultLang;
    await loadLanguage(saved);
  }

  String translate(String key, {Map<String, String>? params}) {
    String text = _translations[key] ?? key;
    if (params != null) {
      params.forEach((k, v) {
        text = text.replaceAll('{$k}', v);
      });
    }
    return text;
  }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/tire_request.dart';
import '../providers/app_provider.dart';

class FormScreen extends StatefulWidget {
  const FormScreen({super.key});

  @override
  State<FormScreen> createState() => _FormScreenState();
}

class _FormScreenState extends State<FormScreen> {
  // Основные
  String? _brand;
  String? _model;
  int? _year;
  DrivingStyle _style = DrivingStyle.comfort;
  Season _season = Season.summer;
  final _budgetController = TextEditingController();
  
  // Новые поля
  final _regionController = TextEditingController(text: 'Москва');
  final _cityController = TextEditingController(text: 'Москва');
  ProductType _productType = ProductType.tires;
  DeliverySpeed _deliverySpeed = DeliverySpeed.any;
  String? _tireSize;
  String? _wheelMaterial;

  @override
  void dispose() {
    _budgetController.dispose();
    _regionController.dispose();
    _cityController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_brand == null || _model == null || _year == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Заполните все поля')),
      );
      return;
    }

    // Парсим размер если есть
    int? tireWidth, tireProfile, tireDiameter;
    if (_tireSize != null && _tireSize!.isNotEmpty) {
      final match = RegExp(r'(\d+)\s*[/]\s*(\d+)\s*R\s*(\d+)').firstMatch(_tireSize!);
      if (match != null) {
        tireWidth = int.tryParse(match.group(1)!);
        tireProfile = int.tryParse(match.group(2)!);
        tireDiameter = int.tryParse(match.group(3)!);
      }
    }

    await context.read<AppProvider>().submitForm(
      brand: _brand!,
      model: _model!,
      year: _year!,
      style: _style,
      season: _season,
      budget: int.tryParse(_budgetController.text.replaceAll(RegExp(r'[^0-9]'), '')),
      region: _regionController.text,
      city: _cityController.text,
      productType: _productType,
      deliverySpeed: _deliverySpeed,
    );
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AppProvider>();
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '📋 Быстрый подбор',
            style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),

          // ===== Основные =====
          _buildSectionTitle('Автомобиль'),
          Row(
            children: [
              Expanded(child: _buildDropdown('Марка', provider.brands, _brand, (v) => _brand = v)),
              const SizedBox(width: 8),
              if (_brand != null)
                Expanded(child: _buildDropdown('Модель', provider.models, _model, (v) => _model = v)),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(child: _buildTextField('Год', '2024', _year?.toString() ?? '', (v) => _year = int.tryParse(v))),
              const SizedBox(width: 8),
              Expanded(child: _buildTextField('Бюджет, ₽', '50000', _budgetController.text, (v) => _budgetController.text = v)),
            ],
          ),
          const SizedBox(height: 16),

          // ===== Регион =====
          _buildSectionTitle('📍 Регион'),
          Row(
            children: [
              Expanded(child: _buildTextField('Регион', 'Москва', _regionController.text, (v) => _regionController.text = v)),
              const SizedBox(width: 8),
              Expanded(child: _buildTextField('Город', 'Москва', _cityController.text, (v) => _cityController.text = v)),
            ],
          ),
          const SizedBox(height: 16),

          // ===== Тип товара =====
          _buildSectionTitle('🔧 Что ищем?'),
          SizedBox(
            height: 36,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: ProductType.values.map((t) {
                final isSelected = _productType == t;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(
                      t == ProductType.tires ? '🛞 Шины' :
                      t == ProductType.wheels ? '🛞 Диски' :
                      t == ProductType.bolts ? '🔩 Крепёж' : '⚙️ В сборе',
                      style: TextStyle(fontSize: 12, color: isSelected ? Colors.black : Colors.white),
                    ),
                    selected: isSelected,
                    onSelected: (v) => setState(() => _productType = t),
                    backgroundColor: const Color(0xFF111820),
                    selectedColor: const Color(0xFF00D4FF),
                    side: BorderSide(color: isSelected ? const Color(0xFF00D4FF) : const Color(0xFF1A2630)),
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 16),

          // ===== Дополнительно =====
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildSectionTitle('🌤️ Сезон'),
                    SizedBox(
                      height: 36,
                      child: ListView(
                        scrollDirection: Axis.horizontal,
                        children: Season.values.map((s) {
                          final isSelected = _season == s;
                          return Padding(
                            padding: const EdgeInsets.only(right: 6),
                            child: ChoiceChip(
                              label: Text(
                                s == Season.summer ? '☀️ Лето' :
                                s == Season.winter ? '❄️ Зима' : '🌿 Всесезон',
                                style: TextStyle(fontSize: 11, color: isSelected ? Colors.black : Colors.white),
                              ),
                              selected: isSelected,
                              onSelected: (v) => setState(() => _season = s),
                              backgroundColor: const Color(0xFF111820),
                              selectedColor: const Color(0xFF00D4FF),
                              side: BorderSide(color: isSelected ? const Color(0xFF00D4FF) : const Color(0xFF1A2630)),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),

          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildSectionTitle('🏎️ Стиль'),
                    SizedBox(
                      height: 36,
                      child: ListView(
                        scrollDirection: Axis.horizontal,
                        children: DrivingStyle.values.map((s) {
                          final isSelected = _style == s;
                          return Padding(
                            padding: const EdgeInsets.only(right: 6),
                            child: ChoiceChip(
                              label: Text(
                                s == DrivingStyle.comfort ? '😌 Комфорт' :
                                s == DrivingStyle.sport ? '🚀 Спорт' : '💰 Эконом',
                                style: TextStyle(fontSize: 11, color: isSelected ? Colors.black : Colors.white),
                              ),
                              selected: isSelected,
                              onSelected: (v) => setState(() => _style = s),
                              backgroundColor: const Color(0xFF111820),
                              selectedColor: const Color(0xFF00D4FF),
                              side: BorderSide(color: isSelected ? const Color(0xFF00D4FF) : const Color(0xFF1A2630)),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),

          Row(
            children: [
              Expanded(child: _buildTextField('Размер шин', '205/55 R16', _tireSize ?? '', (v) => _tireSize = v)),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildSectionTitle('📦 Доставка'),
                    SizedBox(
                      height: 36,
                      child: ListView(
                        scrollDirection: Axis.horizontal,
                        children: DeliverySpeed.values.map((s) {
                          final isSelected = _deliverySpeed == s;
                          return Padding(
                            padding: const EdgeInsets.only(right: 6),
                            child: ChoiceChip(
                              label: Text(
                                s == DeliverySpeed.any ? 'Не важно' :
                                s == DeliverySpeed.urgent ? '🔥 Срочно' :
                                s == DeliverySpeed.within3Days ? '📦 3 дня' : '📦 Неделя',
                                style: TextStyle(fontSize: 10, color: isSelected ? Colors.black : Colors.white),
                              ),
                              selected: isSelected,
                              onSelected: (v) => setState(() => _deliverySpeed = s),
                              backgroundColor: const Color(0xFF111820),
                              selectedColor: const Color(0xFFFFD700),
                              side: BorderSide(color: isSelected ? const Color(0xFFFFD700) : const Color(0xFF1A2630)),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // ===== Кнопка =====
          SizedBox(
            width: double.infinity,
            height: 48,
            child: Container(
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [Color(0xFF00D4FF), Color(0xFF0088CC)]),
                borderRadius: BorderRadius.circular(30),
              ),
              child: ElevatedButton(
                onPressed: provider.isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  shadowColor: Colors.transparent,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                ),
                child: provider.isLoading
                    ? const SizedBox(
                        width: 20, height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Подобрать 🚀',
                        style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 16)),
              ),
            ),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6, top: 4),
      child: Text(title, style: const TextStyle(color: Color(0xFF8899AA), fontSize: 12, fontWeight: FontWeight.w600)),
    );
  }

  Widget _buildDropdown(String hint, List<String> items, String? value, ValueChanged<String?> onChanged) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF111820),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1A2630)),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          hint: Text(hint, style: const TextStyle(color: Color(0xFF556677), fontSize: 13)),
          dropdownColor: const Color(0xFF111820),
          isExpanded: true,
          items: items.map((item) => DropdownMenuItem(
            value: item,
            child: Text(item, style: const TextStyle(color: Colors.white, fontSize: 13)),
          )).toList(),
          onChanged: (v) {
            onChanged(v);
            if (hint == 'Марка' && v != null) {
              context.read<AppProvider>().loadModels(v);
            }
          },
        ),
      ),
    );
  }

  Widget _buildTextField(String hint, String placeholder, String value, ValueChanged<String> onChanged) {
    return TextField(
      controller: value.isNotEmpty ? TextEditingController(text: value) : null,
      decoration: InputDecoration(
        hintText: placeholder,
        labelText: hint,
        filled: true,
        fillColor: const Color(0xFF111820),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF1A2630)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF1A2630)),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        hintStyle: const TextStyle(color: Color(0xFF556677), fontSize: 13),
        labelStyle: const TextStyle(color: Color(0xFF8899AA), fontSize: 11),
      ),
      style: const TextStyle(color: Colors.white, fontSize: 13),
      keyboardType: hint.contains('Год') || hint.contains('Бюджет') ? TextInputType.number : TextInputType.text,
      onChanged: onChanged,
    );
  }
}

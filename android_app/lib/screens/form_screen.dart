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
  String? _selectedBrand;
  String? _selectedModel;
  final TextEditingController _yearController = TextEditingController();
  final TextEditingController _budgetController = TextEditingController();
  DrivingStyle _drivingStyle = DrivingStyle.comfort;
  Season _season = Season.summer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppProvider>().loadBrands();
    });
  }

  @override
  void dispose() {
    _yearController.dispose();
    _budgetController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, app, _) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Подзаголовок
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF00D4FF).withOpacity(0.05),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF00D4FF).withOpacity(0.1)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.tune, color: Color(0xFF00D4FF), size: 18),
                    SizedBox(width: 8),
                    Text(
                      'Быстрый подбор шин',
                      style: TextStyle(color: Color(0xFFE0E8F0), fontSize: 14),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Марка
              _buildLabel('Марка автомобиля', Icons.directions_car),
              const SizedBox(height: 8),
              _buildDropdown<String>(
                value: _selectedBrand,
                hint: 'Выберите марку',
                items: app.brands,
                onChanged: (val) {
                  setState(() {
                    _selectedBrand = val;
                    _selectedModel = null;
                  });
                  if (val != null) app.loadModels(val);
                },
                display: (b) => b,
              ),
              const SizedBox(height: 20),

              // Модель
              _buildLabel('Модель', Icons.directions_car_filled),
              const SizedBox(height: 8),
              _buildDropdown<String>(
                value: _selectedModel,
                hint: _selectedBrand == null ? 'Сначала выберите марку' : 'Выберите модель',
                items: app.models,
                onChanged: (val) => setState(() => _selectedModel = val),
                display: (m) => m,
                enabled: _selectedBrand != null,
              ),
              const SizedBox(height: 20),

              // Год и бюджет
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildLabel('Год выпуска', Icons.calendar_today),
                        const SizedBox(height: 8),
                        TextField(
                          controller: _yearController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                            hintText: '2024',
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildLabel('Бюджет (₽)', Icons.monetization_on),
                        const SizedBox(height: 8),
                        TextField(
                          controller: _budgetController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                            hintText: 'Не обязательно',
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Стиль вождения
              _buildLabel('Стиль вождения', Icons.alt_route),
              const SizedBox(height: 8),
              Row(
                children: [
                  _buildRadioChip(
                    icon: Icons.directions_car,
                    label: 'Комфорт',
                    selected: _drivingStyle == DrivingStyle.comfort,
                    onTap: () => setState(() => _drivingStyle = DrivingStyle.comfort),
                  ),
                  const SizedBox(width: 8),
                  _buildRadioChip(
                    icon: Icons.flag,
                    label: 'Спорт',
                    selected: _drivingStyle == DrivingStyle.sport,
                    onTap: () => setState(() => _drivingStyle = DrivingStyle.sport),
                  ),
                  const SizedBox(width: 8),
                  _buildRadioChip(
                    icon: Icons.eco,
                    label: 'Эконом',
                    selected: _drivingStyle == DrivingStyle.economy,
                    onTap: () => setState(() => _drivingStyle = DrivingStyle.economy),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Сезон
              _buildLabel('Сезон', Icons.cloud),
              const SizedBox(height: 8),
              Row(
                children: [
                  _buildRadioChip(
                    icon: Icons.wb_sunny,
                    label: 'Лето',
                    selected: _season == Season.summer,
                    onTap: () => setState(() => _season = Season.summer),
                  ),
                  const SizedBox(width: 8),
                  _buildRadioChip(
                    icon: Icons.ac_unit,
                    label: 'Зима',
                    selected: _season == Season.winter,
                    onTap: () => setState(() => _season = Season.winter),
                  ),
                  const SizedBox(width: 8),
                  _buildRadioChip(
                    icon: Icons.sync,
                    label: 'Всесезон',
                    selected: _season == Season.allSeason,
                    onTap: () => setState(() => _season = Season.allSeason),
                  ),
                ],
              ),
              const SizedBox(height: 32),

              // Кнопка отправки
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _submit,
                  icon: const Icon(Icons.auto_awesome, size: 18),
                  label: const Text('Подобрать шины', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        );
      },
    );
  }

  Widget _buildLabel(String text, IconData icon) {
    return Row(
      children: [
        Icon(icon, color: const Color(0xFF00D4FF), size: 14),
        const SizedBox(width: 6),
        Text(
          text,
          style: const TextStyle(
            color: Color(0xFF8899AA),
            fontSize: 13,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildDropdown<T>({
    required T? value,
    required String hint,
    required List<T> items,
    required ValueChanged<T?> onChanged,
    required String Function(T) display,
    bool enabled = true,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF111820),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1A2630)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<T>(
          value: value,
          hint: Text(hint, style: const TextStyle(color: Color(0xFF556677))),
          onChanged: enabled ? onChanged : null,
          isExpanded: true,
          dropdownColor: const Color(0xFF111820),
          style: const TextStyle(color: Colors.white, fontSize: 14),
          items: items.map((item) {
            return DropdownMenuItem(value: item, child: Text(display(item)));
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildRadioChip({
    required IconData icon,
    required String label,
    required bool selected,
    required VoidCallback onTap,
  }) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: selected
                ? const Color(0xFF00D4FF).withOpacity(0.1)
                : const Color(0xFF111820),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: selected
                  ? const Color(0xFF00D4FF)
                  : const Color(0xFF1A2630),
              width: selected ? 1.5 : 1,
            ),
          ),
          child: Column(
            children: [
              Icon(icon, color: selected ? const Color(0xFF00D4FF) : const Color(0xFF556677), size: 20),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  color: selected ? Colors.white : const Color(0xFF556677),
                  fontSize: 12,
                  fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _submit() {
    if (_selectedBrand == null || _selectedModel == null || _yearController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Заполните все обязательные поля')),
      );
      return;
    }

    final year = int.tryParse(_yearController.text);
    if (year == null || year < 1980 || year > 2026) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Введите корректный год (1980-2026)')),
      );
      return;
    }

    final budget = _budgetController.text.isNotEmpty
        ? int.tryParse(_budgetController.text)
        : null;

    context.read<AppProvider>().submitForm(
      brand: _selectedBrand!,
      model: _selectedModel!,
      year: year,
      style: _drivingStyle,
      season: _season,
      budget: budget,
    );
  }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../services/api_service.dart';

class FormScreen extends StatefulWidget {
  const FormScreen({super.key});

  @override
  State<FormScreen> createState() => _FormScreenState();
}

class _FormScreenState extends State<FormScreen> {
  final _formKey = GlobalKey<FormState>();
  List<String> _brands = [];
  List<String> _models = [];
  bool _loadingBrands = true;

  @override
  void initState() {
    super.initState();
    _loadBrands();
  }

  Future<void> _loadBrands() async {
    final state = context.read<AppState>();
    final brands = await state.getBrands();
    setState(() {
      _brands = brands;
      _loadingBrands = false;
    });
  }

  Future<void> _loadModels(String brand) async {
    final state = context.read<AppState>();
    final models = await state.getModels(brand);
    setState(() => _models = models);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Быстрый подбор'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Consumer<AppState>(
        builder: (context, state, _) {
          return Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                // Марка
                _buildLabel('Марка', Icons.directions_car),
                const SizedBox(height: 8),
                _loadingBrands
                    ? const Center(child: CircularProgressIndicator())
                    : DropdownButtonFormField<String>(
                        value: state.selectedBrand,
                        decoration: _inputDecoration(),
                        dropdownColor: const Color(0xFF0A0F1C),
                        items: _brands.map((b) => DropdownMenuItem(
                          value: b, child: Text(b, style: const TextStyle(color: Color(0xFFE8EDF5))),
                        )).toList(),
                        onChanged: (val) {
                          state.selectedBrand = val;
                          state.selectedModel = null;
                          state.notifyListeners();
                          if (val != null) _loadModels(val);
                        },
                      ),
                const SizedBox(height: 20),

                // Модель
                _buildLabel('Модель', Icons.model_training),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: state.selectedModel,
                  decoration: _inputDecoration(),
                  dropdownColor: const Color(0xFF0A0F1C),
                  items: _models.map((m) => DropdownMenuItem(
                    value: m, child: Text(m, style: const TextStyle(color: Color(0xFFE8EDF5))),
                  )).toList(),
                  onChanged: (val) {
                    state.selectedModel = val;
                    state.notifyListeners();
                  },
                ),
                const SizedBox(height: 20),

                // Год
                _buildLabel('Год выпуска', Icons.calendar_today),
                const SizedBox(height: 8),
                TextFormField(
                  initialValue: state.selectedYear?.toString() ?? '',
                  keyboardType: TextInputType.number,
                  style: const TextStyle(color: Color(0xFFE8EDF5)),
                  decoration: _inputDecoration(hint: 'Например: 2020'),
                  onChanged: (val) {
                    state.selectedYear = int.tryParse(val);
                  },
                ),
                const SizedBox(height: 20),

                // Стиль вождения
                _buildLabel('Стиль вождения', Icons.speed),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _buildRadio('Комфорт', 'comfort', state.drivingStyle, (v) {
                      state.drivingStyle = v;
                      state.notifyListeners();
                    }),
                    const SizedBox(width: 8),
                    _buildRadio('Спорт', 'sport', state.drivingStyle, (v) {
                      state.drivingStyle = v;
                      state.notifyListeners();
                    }),
                    const SizedBox(width: 8),
                    _buildRadio('Эконом', 'economy', state.drivingStyle, (v) {
                      state.drivingStyle = v;
                      state.notifyListeners();
                    }),
                  ],
                ),
                const SizedBox(height: 20),

                // Сезон
                _buildLabel('Сезон', Icons.wb_sunny),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _buildRadio('Лето', 'summer', state.season, (v) {
                      state.season = v;
                      state.notifyListeners();
                    }),
                    const SizedBox(width: 8),
                    _buildRadio('Зима', 'winter', state.season, (v) {
                      state.season = v;
                      state.notifyListeners();
                    }),
                    const SizedBox(width: 8),
                    _buildRadio('Всесезон', 'all_season', state.season, (v) {
                      state.season = v;
                      state.notifyListeners();
                    }),
                  ],
                ),
                const SizedBox(height: 20),

                // Бюджет
                _buildLabel('Бюджет (₽)', Icons.monetization_on),
                const SizedBox(height: 8),
                TextFormField(
                  initialValue: state.budget?.toString() ?? '',
                  keyboardType: TextInputType.number,
                  style: const TextStyle(color: Color(0xFFE8EDF5)),
                  decoration: _inputDecoration(hint: 'Например: 50000'),
                  onChanged: (val) {
                    state.budget = int.tryParse(val);
                  },
                ),
                const SizedBox(height: 32),

                // Кнопка
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00D4FF),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                      elevation: 4,
                      shadowColor: const Color(0xFF00D4FF).withOpacity(0.25),
                    ),
                    onPressed: state.isLoading ? null : () async {
                      if (state.selectedBrand == null ||
                          state.selectedModel == null ||
                          state.selectedYear == null) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Заполните марку, модель и год')),
                        );
                        return;
                      }
                      await state.submitForm();
                      if (context.mounted) {
                        Navigator.pushNamed(context, '/result');
                      }
                    },
                    child: state.isLoading
                        ? const SizedBox(
                            width: 24, height: 24,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                          )
                        : const Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.search, color: Colors.white),
                              SizedBox(width: 12),
                              Text(
                                'Подобрать шины',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 17,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ],
                          ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildLabel(String text, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 14, color: const Color(0xFF00D4FF)),
        const SizedBox(width: 8),
        Text(
          text,
          style: const TextStyle(
            color: Color(0xFF8899BB),
            fontSize: 13,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ],
    );
  }

  InputDecoration _inputDecoration({String? hint}) {
    return InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(color: Color(0xFF2E4060)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    );
  }

  Widget _buildRadio(String label, String value, String groupValue, ValueChanged<String> onChanged) {
    final selected = value == groupValue;
    return Expanded(
      child: GestureDetector(
        onTap: () => onChanged(value),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: selected
                ? const Color(0xFF00D4FF).withOpacity(0.08)
                : const Color(0xFF0A0F1C),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: selected ? const Color(0xFF00D4FF) : const Color(0xFF1B2740),
            ),
          ),
          child: Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: selected ? const Color(0xFF00D4FF) : const Color(0xFF6B80A0),
              fontWeight: FontWeight.w500,
              fontSize: 13,
            ),
          ),
        ),
      ),
    );
  }
}

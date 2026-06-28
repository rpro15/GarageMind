import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../widgets/product_card.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Рекомендации'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Consumer<AppState>(
        builder: (context, state, _) {
          if (state.advice == null) {
            return const Center(child: CircularProgressIndicator());
          }

          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              // Иконка
              Container(
                width: 60, height: 60,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: const Color(0xFF00D4FF).withOpacity(0.1),
                ),
                child: const Icon(Icons.check_circle, color: Color(0xFF00D4FF), size: 32),
              ),
              const SizedBox(height: 16),
              const Text(
                'Подбор завершён!',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Color(0xFFE8EDF5),
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 24),

              // Совет AI
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      const Color(0xFF00D4FF).withOpacity(0.04),
                      const Color(0xFF00D4FF).withOpacity(0.02),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(14),
                  border: Border(
                    left: BorderSide(
                      color: const Color(0xFF00D4FF).withOpacity(0.3),
                      width: 3,
                    ),
                    top: BorderSide(
                      color: const Color(0xFF00D4FF).withOpacity(0.12),
                    ),
                    right: BorderSide(
                      color: const Color(0xFF00D4FF).withOpacity(0.12),
                    ),
                    bottom: BorderSide(
                      color: const Color(0xFF00D4FF).withOpacity(0.12),
                    ),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.auto_awesome, color: Color(0xFF00D4FF), size: 16),
                        const SizedBox(width: 8),
                        const Text(
                          'Совет AI',
                          style: TextStyle(
                            color: Color(0xFF00D4FF),
                            fontWeight: FontWeight.w600,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      state.advice!,
                      style: const TextStyle(
                        color: Color(0xFFE8EDF5),
                        fontSize: 13,
                        height: 1.7,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Товары
              const Text(
                'Подходящие шины',
                style: TextStyle(
                  color: Color(0xFFE8EDF5),
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 12),
              ...state.products.map((p) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: ProductCard(product: p),
              )),

              const SizedBox(height: 32),

              // Кнопка "На главную"
              SizedBox(
                width: double.infinity,
                height: 52,
                child: OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Color(0xFF1B2740)),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
                  child: const Text(
                    'На главную',
                    style: TextStyle(color: Color(0xFF6B80A0), fontSize: 15),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

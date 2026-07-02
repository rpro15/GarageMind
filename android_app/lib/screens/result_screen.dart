import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_provider.dart';
import '../widgets/product_card.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading) {
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                CircularProgressIndicator(color: Color(0xFF00D4FF)),
                SizedBox(height: 16),
                Text('Ищем лучшие варианты...', style: TextStyle(color: Color(0xFF8899AA))),
              ],
            ),
          );
        }

        if (provider.errorMessage != null) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, color: Color(0xFFFF4444), size: 48),
                  const SizedBox(height: 16),
                  Text(provider.errorMessage!, style: const TextStyle(color: Colors.white)),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: () => provider.reset(),
                    child: const Text('Начать заново'),
                  ),
                ],
              ),
            ),
          );
        }

        final result = provider.result;
        if (result == null) {
          return const Center(child: Text('Нет данных', style: TextStyle(color: Color(0xFF556677))));
        }

        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ===== Заголовок =====
              Text(
                '🎯 Результат подбора',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${provider.selectedBrand} ${provider.selectedModel} '
                '(${provider.selectedYear})',
                style: const TextStyle(color: Color(0xFF8899AA), fontSize: 13),
              ),
              const SizedBox(height: 16),

              // ===== AI Совет =====
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      const Color(0xFF00D4FF).withOpacity(0.1),
                      const Color(0xFF0088CC).withOpacity(0.05),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF00D4FF).withOpacity(0.2)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.auto_awesome, color: Color(0xFF00D4FF), size: 18),
                        SizedBox(width: 8),
                        Text(
                          'Совет AI',
                          style: TextStyle(
                            color: Color(0xFF00D4FF),
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      result.advice,
                      style: const TextStyle(color: Color(0xFFE0E8F0), fontSize: 13, height: 1.5),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // ===== Предупреждения =====
              if (result.warnings.isNotEmpty) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFD700).withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFFFD700).withOpacity(0.15)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'ℹ️ Важно',
                        style: TextStyle(color: Color(0xFFFFD700), fontSize: 12, fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 4),
                      ...result.warnings.map((w) => Padding(
                        padding: const EdgeInsets.only(bottom: 2),
                        child: Text(w, style: const TextStyle(color: Color(0xFF8899AA), fontSize: 11)),
                      )),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // ===== Популярный выбор =====
              if (result.popularPick != null) ...[
                const Text(
                  '⭐ Наш выбор',
                  style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                ProductCard(product: result.popularPick!, isBestPrice: true),
                const SizedBox(height: 16),
              ],

              // ===== Товары =====
              const Text(
                '🛒 Подходящие товары',
                style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              ...result.products.map((p) => ProductCard(product: p)),

              // ===== Кнопки действий =====
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: _ActionButton(
                      icon: '🛞',
                      label: 'Нужны диски?',
                      subtitle: 'Подобрать к шинам',
                      onTap: () {
                        provider.productType = ProductType.wheels;
                        provider.chatStep = ChatStep.wheelMaterial;
                        provider.switchMode(AppMode.chat);
                      },
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _ActionButton(
                      icon: '🔩',
                      label: 'Крепёж?',
                      subtitle: 'Болты / гайки',
                      onTap: () {
                        provider.productType = ProductType.bolts;
                        provider.sendRequest();
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: _ActionButton(
                      icon: '⚙️',
                      label: 'В сборе',
                      subtitle: 'Шины + диски',
                      onTap: () {
                        provider.productType = ProductType.assembly;
                        provider.chatStep = ChatStep.wheelMaterial;
                        provider.switchMode(AppMode.chat);
                      },
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _ActionButton(
                      icon: '🔄',
                      label: 'Другой регион',
                      subtitle: 'Сменить город',
                      onTap: () {
                        provider.chatStep = ChatStep.region;
                        provider.switchMode(AppMode.chat);
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // ===== Кнопка сброса =====
              Center(
                child: TextButton.icon(
                  onPressed: () => provider.reset(),
                  icon: const Icon(Icons.refresh, color: Color(0xFF556677)),
                  label: const Text('Новый подбор', style: TextStyle(color: Color(0xFF556677))),
                ),
              ),
              const SizedBox(height: 32),
            ],
          ),
        );
      },
    );
  }
}

class _ActionButton extends StatelessWidget {
  final String icon;
  final String label;
  final String subtitle;
  final VoidCallback onTap;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF111820),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1A2630)),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              children: [
                Text(icon, style: const TextStyle(fontSize: 22)),
                const SizedBox(height: 4),
                Text(
                  label,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  subtitle,
                  style: const TextStyle(color: Color(0xFF556677), fontSize: 9),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

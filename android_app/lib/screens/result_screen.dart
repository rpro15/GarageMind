import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../providers/app_provider.dart';
import '../models/product.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, app, _) {
        final result = app.result;
        if (result == null) return const SizedBox.shrink();

        return GestureDetector(
          onTap: () => Navigator.of(context).pop(),
          child: Container(
            color: Colors.black87,
            child: GestureDetector(
              onTap: () {},
              child: DraggableScrollableSheet(
                initialChildSize: 0.85,
                minChildSize: 0.5,
                maxChildSize: 0.95,
                builder: (context, scrollController) {
                  return Container(
                    decoration: const BoxDecoration(
                      color: Color(0xFF0A0D14),
                      borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                    ),
                    child: ListView(
                      controller: scrollController,
                      padding: const EdgeInsets.all(20),
                      children: [
                        // Полоска для драга
                        Center(
                          child: Container(
                            width: 40,
                            height: 4,
                            decoration: BoxDecoration(
                              color: const Color(0xFF1A2630),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Заголовок
                        Row(
                          children: [
                            const Icon(Icons.auto_awesome, color: Color(0xFF00D4FF), size: 20),
                            const SizedBox(width: 8),
                            const Expanded(
                              child: Text(
                                'Рекомендации AI',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.close, color: Color(0xFF556677)),
                              onPressed: () {
                                app.reset();
                                Navigator.of(context).pop();
                              },
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),

                        // Совет AI
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: const Color(0xFF111820),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: const Color(0xFF1A2630)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  const Icon(Icons.lightbulb_outline, color: Color(0xFFFFD700), size: 16),
                                  const SizedBox(width: 8),
                                  const Text(
                                    'Совет AI',
                                    style: TextStyle(
                                      color: Color(0xFFFFD700),
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                result.advice,
                                style: const TextStyle(
                                  color: Color(0xFFE0E8F0),
                                  fontSize: 14,
                                  height: 1.5,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Народный выбор
                        if (result.popularPick != null) ...[
                          _buildPopularPick(result.popularPick!),
                          const SizedBox(height: 16),
                        ],

                        // Товары
                        const Row(
                          children: [
                            Icon(Icons.shopping_bag_outlined, color: Color(0xFF00D4FF), size: 16),
                            SizedBox(width: 8),
                            Text(
                              'Где купить по лучшей цене',
                              style: TextStyle(
                                color: Color(0xFF8899AA),
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        ...result.products.map((p) => _buildProductCard(p)),
                        const SizedBox(height: 20),

                        // Кнопка поделиться
                        SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed: () {},
                            icon: const Icon(Icons.share, size: 16),
                            label: const Text('Поделиться рекомендацией'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: const Color(0xFF00D4FF),
                              side: const BorderSide(color: Color(0xFF00D4FF).withOpacity(0.3)),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(30),
                              ),
                              padding: const EdgeInsets.symmetric(vertical: 14),
                            ),
                          ),
                        ),
                        const SizedBox(height: 20),
                      ],
                    ),
                  );
                },
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildPopularPick(Product product) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFFFFD700).withOpacity(0.05),
            const Color(0xFFFFD700).withOpacity(0.01),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFFFD700).withOpacity(0.2)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.whatshot, color: Color(0xFFFFD700), size: 16),
                    const SizedBox(width: 6),
                    const Text(
                      'Народный выбор',
                      style: TextStyle(
                        color: Color(0xFFFFD700),
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  product.name,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(
                      '${product.price.toStringAsFixed(0)} ₽',
                      style: const TextStyle(
                        color: Color(0xFFFFD700),
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(width: 8),
                    if (product.rating != null)
                      Text(
                        '★ ${product.rating!.toStringAsFixed(1)}',
                        style: const TextStyle(
                          color: Color(0xFF556677),
                          fontSize: 12,
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
          Container(
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFFFFD700), Color(0xFFE6C200)],
              ),
              borderRadius: BorderRadius.circular(30),
            ),
            child: TextButton(
              onPressed: () => _openLink(product.partnerLink),
              child: const Text(
                'Выбрать',
                style: TextStyle(
                  color: Colors.black,
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProductCard(Product product) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF111820),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1A2630)),
      ),
      child: Row(
        children: [
          // Изображение
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: const Color(0xFF0A0D14),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF1A2630)),
            ),
            child: product.imageUrl != null
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.network(
                      product.imageUrl!,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => const Icon(
                        Icons.image_outlined,
                        color: Color(0xFF556677),
                      ),
                    ),
                  )
                : const Icon(Icons.image_outlined, color: Color(0xFF556677)),
          ),
          const SizedBox(width: 12),
          // Инфо
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  product.name,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    if (product.rating != null) ...[
                      const Icon(Icons.star, color: Color(0xFFFFD700), size: 12),
                      const SizedBox(width: 2),
                      Text(
                        product.rating!.toStringAsFixed(1),
                        style: const TextStyle(color: Color(0xFF8899AA), fontSize: 11),
                      ),
                      const SizedBox(width: 8),
                    ],
                    Text(
                      '${product.price.toStringAsFixed(0)} ₽',
                      style: const TextStyle(
                        color: Color(0xFF00D4FF),
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                if (product.source != null)
                  Text(
                    product.source!,
                    style: const TextStyle(color: Color(0xFF556677), fontSize: 11),
                  ),
              ],
            ),
          ),
          // Кнопка
          Container(
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF00D4FF), Color(0xFF0088CC)],
              ),
              borderRadius: BorderRadius.circular(30),
            ),
            child: TextButton(
              onPressed: () => _openLink(product.partnerLink),
              child: const Text(
                'Купить',
                style: TextStyle(
                  color: Colors.black,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _openLink(String? url) {
    if (url != null) {
      launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
    }
  }
}

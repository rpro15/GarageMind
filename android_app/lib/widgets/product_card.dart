import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/product.dart';

class ProductCard extends StatelessWidget {
  final Product product;
  final bool isBestPrice;
  final bool isPopular;

  const ProductCard({
    super.key,
    required this.product,
    this.isBestPrice = false,
    this.isPopular = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      child: Stack(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFF111820),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isBestPrice
                    ? const Color(0xFFFFD700).withOpacity(0.3)
                    : const Color(0xFF1A2630),
              ),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Изображение
                _buildImage(),
                const SizedBox(width: 12),
                // Инфо
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Тип товара + название
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: Color(product.typeColor).withOpacity(0.15),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              product.typeIcon,
                              style: const TextStyle(fontSize: 12),
                            ),
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              product.name,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 13,
                                fontWeight: FontWeight.w500,
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      // Размер / характеристики
                      if (product.tireSize != null)
                        _infoChip('📐 ${product.tireSize}'),
                      if (product.boltThread != null)
                        _infoChip('🔩 ${product.boltThread}'),
                      if (product.wheelMaterial != null)
                        _infoChip(product.wheelMaterial == 'alloy' ? '🎨 Литьё' : '🔘 Штамповка'),
                      const SizedBox(height: 4),
                      // Рейтинг и цена
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
                          // Доставка
                          if (product.deliveryDays != null)
                            Text(
                              '📦 ${product.deliveryDays} дн.',
                              style: const TextStyle(color: Color(0xFF556677), fontSize: 11),
                            ),
                          const Spacer(),
                          // Цена
                          Text(
                            '${product.price.toStringAsFixed(0)} ₽',
                            style: TextStyle(
                              color: isBestPrice
                                  ? const Color(0xFFFFD700)
                                  : const Color(0xFF00D4FF),
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      // Наличие
                      if (!product.inStock)
                        const Text(
                          '❌ Нет в наличии',
                          style: TextStyle(color: Color(0xFFFF4444), fontSize: 11),
                        ),
                      if (product.pickupAvailable)
                        const Text(
                          '📍 Можно забрать',
                          style: TextStyle(color: Color(0xFF00FF88), fontSize: 11),
                        ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                // Кнопка
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: isBestPrice
                              ? [const Color(0xFFFFD700), const Color(0xFFE6C200)]
                              : [const Color(0xFF00D4FF), const Color(0xFF0088CC)],
                        ),
                        borderRadius: BorderRadius.circular(30),
                      ),
                      child: TextButton(
                        onPressed: () => _openLink(product.partnerLink),
                        child: Text(
                          isBestPrice ? 'Выбрать' : 'Купить',
                          style: const TextStyle(
                            color: Colors.black,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 4),
                    if (product.source != null)
                      Text(
                        product.source!.replaceAll('_', ' '),
                        style: const TextStyle(color: Color(0xFF556677), fontSize: 9),
                      ),
                  ],
                ),
              ],
            ),
          ),
          // Бейдж лучшей цены
          if (isBestPrice)
            Positioned(
              top: -4,
              left: 8,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFFFFD700), Color(0xFFE6C200)],
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.crown, size: 10, color: Colors.black),
                    SizedBox(width: 3),
                    Text(
                      'Лучшая цена',
                      style: TextStyle(
                        color: Colors.black,
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildImage() {
    return Container(
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
          : Icon(
              product.productType == 'wheels'
                  ? Icons.circle_outlined
                  : Icons.image_outlined,
              color: Color(product.typeColor),
            ),
    );
  }

  Widget _infoChip(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Text(
        text,
        style: const TextStyle(
          color: Color(0xFF8899AA),
          fontSize: 11,
          fontFamily: 'monospace',
        ),
      ),
    );
  }

  void _openLink(String? url) {
    if (url != null) {
      launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
    }
  }
}

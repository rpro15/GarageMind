import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_provider.dart';

class HeaderWidget extends StatelessWidget {
  const HeaderWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, app, _) {
        return Container(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
          decoration: const BoxDecoration(
            border: Border(
              bottom: BorderSide(color: Color(0xFF1A2630), width: 1),
            ),
          ),
          child: Row(
            children: [
              // Логотип
              Row(
                children: [
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: const Color(0xFF00D4FF), width: 2),
                    ),
                    child: const Icon(Icons.play_arrow_rounded, color: Color(0xFF00D4FF), size: 16),
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'Авто',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Text(
                    'Эксперт',
                    style: TextStyle(
                      color: Color(0xFF00D4FF),
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Container(
                    margin: const EdgeInsets.only(left: 2),
                    padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                    decoration: BoxDecoration(
                      color: const Color(0xFF00D4FF),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      'AI',
                      style: TextStyle(
                        color: Colors.black,
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const Spacer(),
              // Кнопки действий
              Row(
                children: [
                  // Переключатель режимов
                  _IconButton(
                    icon: app.mode == AppMode.chat
                        ? Icons.list_rounded
                        : Icons.chat_rounded,
                    onTap: () {
                      app.switchMode(
                        app.mode == AppMode.chat ? AppMode.form : AppMode.chat,
                      );
                    },
                  ),
                  const SizedBox(width: 4),
                  // Бейдж Online
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFF00D4FF).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFF00D4FF).withOpacity(0.2)),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.fiber_manual_record, color: Color(0xFF00D4FF), size: 8),
                        SizedBox(width: 4),
                        Text(
                          'Online',
                          style: TextStyle(
                            color: Color(0xFF00D4FF),
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}

class _IconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _IconButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            color: const Color(0xFF00D4FF).withOpacity(0.08),
          ),
          child: Icon(icon, color: const Color(0xFF00D4FF), size: 18),
        ),
      ),
    );
  }
}

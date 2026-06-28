import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../main.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Шапка
            _buildHeader(context),
            // Тело
            Expanded(child: _buildBody(context)),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
      decoration: const BoxDecoration(
        color: Color(0xFF0E1422),
        border: Border(bottom: BorderSide(color: Color(0xFF1B2740))),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Бренд
              Row(
                children: [
                  Icon(Icons.memory, color: const Color(0xFF00D4FF), size: 24),
                  const SizedBox(width: 10),
                  Text(
                    'Авто Эксперт ',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: const Color(0xFFE8EDF5),
                    ),
                  ),
                  Text(
                    'AI',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: const Color(0xFF00D4FF),
                      shadows: [
                        Shadow(
                          color: const Color(0xFF00D4FF).withOpacity(0.3),
                          blurRadius: 20,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              // Статус
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFF00E676).withOpacity(0.08),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: const Color(0xFF00E676).withOpacity(0.15),
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 6, height: 6,
                      decoration: const BoxDecoration(
                        color: Color(0xFF00E676),
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 6),
                    const Text(
                      'Online',
                      style: TextStyle(
                        fontSize: 11,
                        color: Color(0xFF00E676),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Icon(Icons.smart_toy_outlined, size: 14, color: const Color(0xFF00D4FF)),
              const SizedBox(width: 6),
              Text(
                'AI-консультант по подбору шин',
                style: TextStyle(
                  fontSize: 12,
                  color: const Color(0xFF6B80A0),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, state, _) {
        return Column(
          children: [
            // Переключатель
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF131B2C),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: const Color(0xFF1B2740)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: GestureDetector(
                        onTap: () => state.switchMode(true),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          decoration: BoxDecoration(
                            color: state.isChatMode
                                ? const Color(0xFF00D4FF).withOpacity(0.1)
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.chat_bubble_outline,
                                size: 18,
                                color: state.isChatMode
                                    ? const Color(0xFF00D4FF)
                                    : const Color(0xFF6B80A0),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'Чат',
                                style: TextStyle(
                                  fontWeight: FontWeight.w600,
                                  color: state.isChatMode
                                      ? const Color(0xFF00D4FF)
                                      : const Color(0xFF6B80A0),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    Expanded(
                      child: GestureDetector(
                        onTap: () => state.switchMode(false),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          decoration: BoxDecoration(
                            color: !state.isChatMode
                                ? const Color(0xFFFF6B35).withOpacity(0.1)
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.list_alt_outlined,
                                size: 18,
                                color: !state.isChatMode
                                    ? const Color(0xFFFF6B35)
                                    : const Color(0xFF6B80A0),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'Форма',
                                style: TextStyle(
                                  fontWeight: FontWeight.w600,
                                  color: !state.isChatMode
                                      ? const Color(0xFFFF6B35)
                                      : const Color(0xFF6B80A0),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            // Содержимое
            Expanded(
              child: state.isChatMode
                  ? const _ChatBody()
                  : const _FormBody(),
            ),
          ],
        );
      },
    );
  }
}

// ===== Базовый чат =====
class _ChatBody extends StatefulWidget {
  const _ChatBody();

  @override
  State<_ChatBody> createState() => _ChatBodyState();
}

class _ChatBodyState extends State<_ChatBody> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().sendMessage('');
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Сообщения
        Expanded(
          child: Consumer<AppState>(
            builder: (context, state, _) {
              WidgetsBinding.instance.addPostFrameCallback((_) {
                if (_scrollController.hasClients) {
                  _scrollController.animateTo(
                    _scrollController.position.maxScrollExtent,
                    duration: const Duration(milliseconds: 300),
                    curve: Curves.easeOut,
                  );
                }
              });
              return ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: state.messages.length + (state.isLoading ? 1 : 0),
                itemBuilder: (context, index) {
                  if (index == state.messages.length && state.isLoading) {
                    return const _TypingIndicator();
                  }
                  final msg = state.messages[index];
                  return _MessageBubble(message: msg);
                },
              );
            },
          ),
        ),
        // Поле ввода
        Container(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          decoration: const BoxDecoration(
            color: Color(0xFF0E1422),
            border: Border(top: BorderSide(color: Color(0xFF1B2740))),
          ),
          child: Row(
            children: [
              // Микрофон
              Container(
                width: 44, height: 44,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: const Color(0xFF1B2740)),
                  color: const Color(0xFF131B2C),
                ),
                child: IconButton(
                  icon: const Icon(Icons.mic, color: Color(0xFF6B80A0)),
                  onPressed: () {},
                ),
              ),
              const SizedBox(width: 8),
              // Поле
              Expanded(
                child: TextField(
                  controller: _controller,
                  decoration: InputDecoration(
                    hintText: 'Напишите или нажмите микрофон...',
                    hintStyle: const TextStyle(color: Color(0xFF2E4060)),
                    filled: true,
                    fillColor: const Color(0xFF0A0F1C),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(24),
                      borderSide: const BorderSide(color: Color(0xFF1B2740)),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(24),
                      borderSide: const BorderSide(color: Color(0xFF00D4FF)),
                    ),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  ),
                  style: const TextStyle(color: Color(0xFFE8EDF5)),
                  onSubmitted: (text) {
                    context.read<AppState>().sendMessage(text);
                    _controller.clear();
                  },
                ),
              ),
              const SizedBox(width: 8),
              // Отправить
              Container(
                width: 44, height: 44,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: const LinearGradient(
                    colors: [Color(0xFF00D4FF), Color(0xFF0088CC)],
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF00D4FF).withOpacity(0.25),
                      blurRadius: 20,
                    ),
                  ],
                ),
                child: IconButton(
                  icon: const Icon(Icons.send, color: Colors.white, size: 18),
                  onPressed: () {
                    context.read<AppState>().sendMessage(_controller.text);
                    _controller.clear();
                  },
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// ===== Пузырёк сообщения =====
class _MessageBubble extends StatelessWidget {
  final ChatMessage message;
  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!message.isUser) ...[
            Container(
              width: 32, height: 32,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [
                    const Color(0xFF00D4FF).withOpacity(0.15),
                    const Color(0xFF00D4FF).withOpacity(0.05),
                  ],
                ),
                border: Border.all(color: const Color(0xFF00D4FF).withOpacity(0.2)),
              ),
              child: const Icon(Icons.smart_toy, size: 16, color: Color(0xFF00D4FF)),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: message.isUser
                    ? const Color(0xFF00D4FF).withOpacity(0.06)
                    : const Color(0xFF131B2C),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(message.isUser ? 16 : 4),
                  bottomRight: Radius.circular(message.isUser ? 4 : 16),
                ),
                border: Border.all(
                  color: message.isUser
                      ? const Color(0xFF00D4FF).withOpacity(0.15)
                      : const Color(0xFF1B2740),
                ),
              ),
              child: Text(
                message.text,
                style: const TextStyle(
                  color: Color(0xFFE8EDF5),
                  fontSize: 14,
                  height: 1.6,
                ),
              ),
            ),
          ),
          if (message.isUser) ...[
            const SizedBox(width: 8),
            Container(
              width: 32, height: 32,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [
                    const Color(0xFFFF6B35).withOpacity(0.15),
                    const Color(0xFFFF6B35).withOpacity(0.05),
                  ],
                ),
                border: Border.all(color: const Color(0xFFFF6B35).withOpacity(0.2)),
              ),
              child: const Icon(Icons.person, size: 16, color: Color(0xFFFF6B35)),
            ),
          ],
        ],
      ),
    );
  }
}

// ===== Индикатор печати =====
class _TypingIndicator extends StatelessWidget {
  const _TypingIndicator();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Container(
            width: 32, height: 32,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: [
                  const Color(0xFF00D4FF).withOpacity(0.15),
                  const Color(0xFF00D4FF).withOpacity(0.05),
                ],
              ),
              border: Border.all(color: const Color(0xFF00D4FF).withOpacity(0.2)),
            ),
            child: const Icon(Icons.smart_toy, size: 16, color: Color(0xFF00D4FF)),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFF131B2C),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF1B2740)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: List.generate(3, (i) {
                return TweenAnimationBuilder<double>(
                  duration: const Duration(milliseconds: 600),
                  tween: Tween(begin: 0.3, end: 1.0),
                  builder: (context, value, _) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 2),
                      child: Container(
                        width: 6, height: 6,
                        decoration: BoxDecoration(
                          color: const Color(0xFF00D4FF).withOpacity(value),
                          shape: BoxShape.circle,
                        ),
                      ),
                    );
                  },
                );
              }),
            ),
          ),
        ],
      ),
    );
  }
}

// ===== Форма (заглушка — полная версия в form_screen.dart) =====
class _FormBody extends StatelessWidget {
  const _FormBody();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.list_alt, size: 48, color: Color(0xFFFF6B35)),
          SizedBox(height: 16),
          Text(
            'Форма быстрого подбора',
            style: TextStyle(
              color: Color(0xFFE8EDF5),
              fontSize: 18,
              fontWeight: FontWeight.w600,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Заполните параметры автомобиля',
            style: TextStyle(color: Color(0xFF6B80A0)),
          ),
          SizedBox(height: 24),
        ],
      ),
    );
  }
}

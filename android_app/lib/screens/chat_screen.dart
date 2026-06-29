import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_provider.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _addBotMessage(_getGreeting());
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  String _getStepQuestion(AppProvider app) {
    switch (app.chatStep) {
      case ChatStep.brand:
        return 'Привет! Я AI-консультант по подбору шин 🚗\n\nС какой маркой автомобиля?';
      case ChatStep.model:
        return 'Отлично, ${app.selectedBrand}! Какая модель?';
      case ChatStep.year:
        return 'Какой год выпуска?';
      case ChatStep.drivingStyle:
        return 'Стиль вождения?\n\n🚗 Комфорт — плавная езда\n🏎️ Спорт — динамика\n⛽ Эконом — экономия';
      case ChatStep.season:
        return 'Какой сезон?\n\n☀️ Лето\n❄️ Зима\n🌦️ Всесезон';
      case ChatStep.budget:
        return 'Какой бюджет? (₽)\n\nМожно пропустить — напишите "любой"';
      case ChatStep.done:
        return '';
    }
  }

  String _getGreeting() {
    return 'Привет! Я AI-консультант по подбору шин 🚗\n\nС какой маркой автомобиля?';
  }

  void _addBotMessage(String text) {
    setState(() {
      _messages.add(ChatMessage(text: text, isBot: true));
    });
    _scrollDown();
  }

  void _addUserMessage(String text) {
    setState(() {
      _messages.add(ChatMessage(text: text, isBot: false));
    });
    _scrollDown();
  }

  void _scrollDown() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _handleSend() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    _addUserMessage(text);
    _controller.clear();

    final app = context.read<AppProvider>();
    final prevStep = app.chatStep;
    app.handleChatInput(text);

    // Ждём обновления провайдера
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final app2 = context.read<AppProvider>();
      if (app2.errorMessage != null && app2.chatStep == prevStep) {
        _addBotMessage(app2.errorMessage!);
        app2.errorMessage = null;
      } else if (app2.chatStep != ChatStep.done && app2.chatStep != prevStep) {
        _addBotMessage(_getStepQuestion(app2));
      } else if (app2.chatStep == ChatStep.done && app2.isLoading) {
        _addBotMessage('Спасибо! Анализирую рынок... 🤖');
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, app, _) {
        // Проверяем, если первый запуск и нет сообщений
        if (_messages.isEmpty) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (_messages.isEmpty) {
              _addBotMessage(_getStepQuestion(app));
            }
          });
        }

        return Column(
          children: [
            // Заголовок-подсказка
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: const BoxDecoration(
                border: Border(
                  bottom: BorderSide(color: Color(0xFF1A2630), width: 0.5),
                ),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF00D4FF).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.smart_toy_outlined, color: Color(0xFF00D4FF), size: 16),
                  ),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'AI-консультант по подбору шин',
                      style: TextStyle(color: Color(0xFF8899AA), fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),

            // Сообщения
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.all(16),
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  final msg = _messages[index];
                  return _MessageBubble(message: msg);
                },
              ),
            ),

            // Input area
            Container(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
              decoration: const BoxDecoration(
                border: Border(
                  top: BorderSide(color: Color(0xFF1A2630), width: 0.5),
                ),
              ),
              child: Row(
                children: [
                  // Микрофон
                  Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF00D4FF).withOpacity(0.08),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: IconButton(
                      icon: const Icon(Icons.mic, color: Color(0xFF00D4FF), size: 20),
                      onPressed: () {},
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Поле ввода
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      style: const TextStyle(color: Colors.white, fontSize: 14),
                      decoration: InputDecoration(
                        hintText: 'Напишите марку, модель...',
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        suffixIcon: Container(
                          margin: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: const Color(0xFF00D4FF).withOpacity(0.08),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: IconButton(
                            icon: const Icon(Icons.camera_alt_outlined, color: Color(0xFF00D4FF), size: 18),
                            onPressed: () {},
                          ),
                        ),
                      ),
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _handleSend(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Отправить
                  Container(
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF00D4FF), Color(0xFF0088CC)],
                      ),
                      borderRadius: BorderRadius.circular(30),
                    ),
                    child: IconButton(
                      icon: const Icon(Icons.send_rounded, color: Colors.black, size: 18),
                      onPressed: _handleSend,
                    ),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}

class ChatMessage {
  final String text;
  final bool isBot;

  ChatMessage({required this.text, required this.isBot});
}

class _MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            message.isBot ? MainAxisAlignment.start : MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (message.isBot) ...[
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: const Color(0xFF00D4FF).withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.smart_toy, color: Color(0xFF00D4FF), size: 16),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: message.isBot
                    ? const Color(0xFF111820)
                    : const Color(0xFF00D4FF).withOpacity(0.1),
                borderRadius: BorderRadius.circular(
                  message.isBot ? 16 : 16,
                ).copyWith(
                  topLeft: message.isBot ? const Radius.circular(4) : null,
                  topRight: !message.isBot ? const Radius.circular(4) : null,
                ),
                border: Border.all(
                  color: message.isBot
                      ? const Color(0xFF1A2630)
                      : const Color(0xFF00D4FF).withOpacity(0.2),
                ),
              ),
              child: Text(
                message.text,
                style: TextStyle(
                  color: message.isBot ? const Color(0xFFE0E8F0) : Colors.white,
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
            ),
          ),
          if (!message.isBot) ...[
            const SizedBox(width: 8),
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: const Color(0xFF00D4FF).withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.person, color: Color(0xFF00D4FF), size: 16),
            ),
          ],
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../main.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _scrollController = ScrollController();
  final _textController = TextEditingController();

  @override
  void dispose() {
    _scrollController.dispose();
    _textController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 32, height: 32,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [Color(0xFF00D4FF), Color(0xFF0088CC)],
                ),
              ),
              child: const Icon(Icons.auto_awesome, size: 16, color: Colors.white),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('AI Консультант', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                Text('онлайн', style: TextStyle(fontSize: 11, color: Color(0xFF00D4FF))),
              ],
            ),
          ],
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Consumer<AppState>(
        builder: (context, state, _) {
          return Column(
            children: [
              // Сообщения
              Expanded(
                child: ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                  itemCount: state.messages.length,
                  itemBuilder: (context, index) {
                    final msg = state.messages[index];
                    return _buildMessage(msg);
                  },
                ),
              ),

              // Индикатор загрузки
              if (state.isLoading)
                const Padding(
                  padding: EdgeInsets.only(bottom: 8),
                  child: SizedBox(
                    width: 16, height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Color(0xFF00D4FF),
                    ),
                  ),
                ),

              // Поле ввода
              Container(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
                decoration: const BoxDecoration(
                  color: Color(0xFF0E1422),
                  border: Border(top: BorderSide(color: Color(0xFF1B2740))),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _textController,
                        style: const TextStyle(color: Color(0xFFE8EDF5), fontSize: 15),
                        decoration: InputDecoration(
                          hintText: 'Введите марку и модель...',
                          hintStyle: const TextStyle(color: Color(0xFF2E4060)),
                          filled: true,
                          fillColor: const Color(0xFF080B14),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(20),
                            borderSide: const BorderSide(color: Color(0xFF1B2740)),
                          ),
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        ),
                        textInputAction: TextInputAction.send,
                        onSubmitted: _sendMessage,
                      ),
                    ),
                    const SizedBox(width: 8),
                    GestureDetector(
                      onTap: () => _sendMessage(_textController.text),
                      child: Container(
                        width: 44, height: 44,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: LinearGradient(
                            colors: [Color(0xFF00D4FF), Color(0xFF0088CC)],
                          ),
                        ),
                        child: const Icon(Icons.send_rounded, color: Colors.white, size: 20),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  void _sendMessage(String text) {
    if (text.trim().isEmpty) return;
    final state = context.read<AppState>();
    state.sendMessage(text);
    _textController.clear();
    _scrollToBottom();
  }

  Widget _buildMessage(dynamic msg) {
    final isUser = msg.isUser;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Аватар AI
          if (!isUser)
            Container(
              width: 28, height: 28,
              margin: const EdgeInsets.only(right: 8, top: 4),
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [Color(0xFF00D4FF), Color(0xFF0088CC)],
                ),
              ),
              child: const Icon(Icons.auto_awesome, size: 14, color: Colors.white),
            ),

          // Сообщение
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isUser
                    ? const Color(0xFF00D4FF).withOpacity(0.12)
                    : const Color(0xFF131B2C),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: isUser ? const Radius.circular(16) : Radius.zero,
                  bottomRight: isUser ? Radius.zero : const Radius.circular(16),
                ),
                border: Border.all(
                  color: isUser
                      ? const Color(0xFF00D4FF).withOpacity(0.2)
                      : const Color(0xFF1B2740),
                ),
              ),
              child: Text(
                msg.text,
                style: TextStyle(
                  color: const Color(0xFFE8EDF5),
                  fontSize: 14,
                  height: 1.6,
                ),
              ),
            ),
          ),

          // Аватар пользователя
          if (isUser)
            Container(
              width: 28, height: 28,
              margin: const EdgeInsets.only(left: 8, top: 4),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF1B2740),
              ),
              child: const Icon(Icons.person, size: 16, color: Color(0xFF6B80A0)),
            ),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_provider.dart';
import '../widgets/header_widget.dart';
import 'chat_screen.dart';
import 'form_screen.dart';
import 'result_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppProvider>(
      builder: (context, app, _) {
        return Scaffold(
          body: SafeArea(
            child: Column(
              children: [
                const HeaderWidget(),
                Expanded(
                  child: Stack(
                    children: [
                      if (app.mode == AppMode.chat) const ChatScreen() else const FormScreen(),
                      if (app.result != null) const ResultScreen(),
                      if (app.isLoading) _buildLoader(context),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildLoader(BuildContext context) {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Container(
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(
            color: const Color(0xFF111820),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFF1A2630)),
          ),
          child: const Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(
                width: 48,
                height: 48,
                child: CircularProgressIndicator(
                  strokeWidth: 3,
                  valueColor: AlwaysStoppedAnimation(Color(0xFF00D4FF)),
                ),
              ),
              SizedBox(height: 16),
              Text(
                'AI анализирует рынок...',
                style: TextStyle(color: Color(0xFF8899AA), fontSize: 14),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

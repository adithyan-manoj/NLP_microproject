import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'features/chat/chat_screen.dart';

void main() {
  runApp(const CricInsightApp());
}

class CricInsightApp extends StatelessWidget {
  const CricInsightApp({super.key});

  @override
  Widget build(BuildContext context) {
    final apiService = ApiService();

    return MaterialApp(
      title: 'CricInsight — Conversational Cricket Analytics',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0D1117),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00E5FF),
          secondary: Color(0xFF00E676),
          surface: Color(0xFF161B22),
          background: Color(0xFF0D1117),
        ),
        fontFamily: 'Segoe UI',
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF161B22),
          elevation: 0,
        ),
      ),
      home: ChatScreen(apiService: apiService),
    );
  }
}

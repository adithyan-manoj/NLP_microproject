import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/chat_response.dart';

class ApiService {
  final String baseUrl;

  ApiService({this.baseUrl = 'http://localhost:8000/api'});

  Future<ChatResponse> sendQuery({required String query, String? conversationId}) async {
    return queryChat(query, context: conversationId != null ? {'conversation_id': conversationId} : null);
  }

  Future<ChatResponse> queryChat(String prompt, {Map<String, dynamic>? context}) async {
    final uri = Uri.parse('$baseUrl/chat/query');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'prompt': prompt,
        'context': context,
      }),
    ).timeout(const Duration(seconds: 35));

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      return ChatResponse.fromJson(data);
    } else {
      throw Exception('API Server returned status ${response.statusCode}: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> getDatasetCoverage() async {
    final uri = Uri.parse('$baseUrl/dataset/coverage');
    final response = await http.get(uri).timeout(const Duration(seconds: 10));
    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw Exception('Failed to fetch dataset coverage');
  }

  Future<Map<String, dynamic>> getDatasetStatus() async {
    final uri = Uri.parse('$baseUrl/dataset/status');
    final response = await http.get(uri).timeout(const Duration(seconds: 5));
    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw Exception('Failed to fetch dataset status');
  }

  Future<Map<String, dynamic>> checkHealth() async {
    final uri = Uri.parse('$baseUrl/health');
    final response = await http.get(uri).timeout(const Duration(seconds: 5));
    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw Exception('API health check failed');
  }

  Future<Map<String, dynamic>> getEvaluationSummary() async {
    final uri = Uri.parse('$baseUrl/evaluation/summary');
    final response = await http.get(uri).timeout(const Duration(seconds: 10));
    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw Exception('Failed to fetch evaluation summary');
  }

  Future<Map<String, dynamic>> getEvaluationProviders() async {
    final uri = Uri.parse('$baseUrl/evaluation/providers');
    final response = await http.get(uri).timeout(const Duration(seconds: 5));
    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw Exception('Failed to fetch provider status');
  }

  Future<List<dynamic>> getEvaluationQueries({int limit = 50}) async {
    final uri = Uri.parse('$baseUrl/evaluation/queries?limit=$limit');
    final response = await http.get(uri).timeout(const Duration(seconds: 10));
    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw Exception('Failed to fetch query logs');
  }

  Future<Map<String, dynamic>> runEvaluation() async {
    final uri = Uri.parse('$baseUrl/evaluation/run');
    final response = await http.post(uri).timeout(const Duration(seconds: 60));
    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    throw Exception('Evaluation run failed');
  }
}

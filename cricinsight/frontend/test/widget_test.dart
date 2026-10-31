import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cricinsight/main.dart';
import 'package:cricinsight/services/api_service.dart';
import 'package:cricinsight/features/presentation/kpi_card_grid.dart';
import 'package:cricinsight/features/charts/fl_chart_renderer.dart';
import 'package:cricinsight/features/evaluation/evaluation_dashboard_screen.dart';

void main() {
  testWidgets('CricInsightApp smoke and initialization test', (WidgetTester tester) async {
    await tester.pumpWidget(const CricInsightApp());

    // Verify app title and welcome message render
    expect(find.text('CricInsight'), findsOneWidget);
    expect(find.textContaining('Welcome to CricInsight'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
    expect(find.byIcon(Icons.send_rounded), findsOneWidget);
  });

  testWidgets('KpiCardGrid renders calculated metrics correctly', (WidgetTester tester) async {
    final testMetrics = {
      'player_name': 'Virat Kohli',
      'total_runs': 12898,
      'batting_average': 57.32,
      'strike_rate': 93.62,
      'high_score': 183,
      'high_score_not_out': false,
      'centuries': 46,
      'fifties': 65,
      'fours': 1211,
      'sixes': 138,
      'std_deviation': 28.4,
    };

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: KpiCardGrid(metrics: testMetrics),
        ),
      ),
    );

    expect(find.text('Total Runs'), findsOneWidget);
    expect(find.text('12898'), findsOneWidget);
    expect(find.text('Batting Average'), findsOneWidget);
    expect(find.text('57.32'), findsOneWidget);
    expect(find.text('Strike Rate'), findsOneWidget);
    expect(find.text('93.62'), findsOneWidget);
  });

  testWidgets('FlChartRenderer renders line chart with data points', (WidgetTester tester) async {
    final chartSpec = {
      'chart_type': 'line',
      'title': "Virat Kohli's Recent Innings",
      'subtitle': 'Last 3 innings chronologically',
      'x_axis': {
        'label': 'Innings Sequence',
        'categories': ['Innings 1', 'Innings 2', 'Innings 3'],
      },
      'y_axis': {'label': 'Runs Scored', 'min': 0, 'max': 120},
      'series': [
        {
          'name': 'Runs',
          'color': '#00E5FF',
          'data': [
            {'x': 0, 'y': 82, 'label': '82* vs PAK'},
            {'x': 1, 'y': 49, 'label': '49 vs SA'},
            {'x': 2, 'y': 101, 'label': '101* vs AFG'},
          ],
        }
      ],
      'empty_state_message': 'No data available',
    };

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: FlChartRenderer(chartSpec: chartSpec),
          ),
        ),
      ),
    );

    expect(find.text("Virat Kohli's Recent Innings"), findsOneWidget);
    expect(find.text('Last 3 innings chronologically'), findsOneWidget);
  });

  testWidgets('EvaluationDashboardScreen renders benchmark metrics and provider status', (WidgetTester tester) async {
    final mockApi = MockApiService();

    await tester.pumpWidget(
      MaterialApp(
        home: EvaluationDashboardScreen(apiService: mockApi),
      ),
    );

    // Initial pump triggers Future.wait
    await tester.pumpAndSettle();

    // Verify header and metrics
    expect(find.text('NLP & Retrieval Evaluation Dashboard'), findsOneWidget);
    expect(find.text('Intent Accuracy'), findsOneWidget);
    expect(find.text('83.3%'), findsOneWidget);
    expect(find.text('Entity F1-Score'), findsOneWidget);
    expect(find.text('76.7%'), findsOneWidget);
    expect(find.text('Format Normalization'), findsOneWidget);
    expect(find.text('Clarification Detection'), findsOneWidget);
    expect(find.text('100.0%'), findsWidgets);

    // Verify providers
    expect(find.text('LLM Providers & Failover Architecture'), findsOneWidget);
    expect(find.text('Recent Live Queries & Observability Logs'), findsOneWidget);
    expect(find.text('How has Virat Kohli performed in ODIs?'), findsOneWidget);
  });
}

class MockApiService extends ApiService {
  @override
  Future<Map<String, dynamic>> getEvaluationSummary() async {
    return {
      'total_benchmark_questions': 30,
      'intent_accuracy': 83.3,
      'entity_precision': 95.8,
      'entity_recall': 63.9,
      'entity_f1': 76.7,
      'format_accuracy': 100.0,
      'clarification_accuracy': 100.0,
      'average_latency_ms': 139.2,
      'fallback_frequency': 100.0,
      'primary_provider': 'deterministic',
      'fallback_provider': 'qwen2.5:3b-instruct',
      'timestamp': '2026-10-30T13:38:57Z',
    };
  }

  @override
  Future<Map<String, dynamic>> getEvaluationProviders() async {
    return {
      'primary_provider': {
        'name': 'gemini',
        'model': 'gemini-2.5-flash',
        'configured': false,
        'timeout_seconds': 10,
      },
      'fallback_provider': {
        'name': 'qwen',
        'model': 'qwen2.5:3b-instruct',
        'enabled': true,
        'timeout_seconds': 20,
      },
      'resilience_engine': {
        'name': 'deterministic',
        'model': 'rule_based_python',
        'status': 'active',
      },
      'max_overall_deadline_seconds': 32,
    };
  }

  @override
  Future<List<dynamic>> getEvaluationQueries({int limit = 50}) async {
    return [
      {
        'query': 'How has Virat Kohli performed in ODIs?',
        'intent': 'player_performance',
        'provider': 'deterministic',
        'status': 'success',
        'latency_ms': 12,
      }
    ];
  }
}

import 'package:flutter/material.dart';
import '../../models/chat_response.dart';
import '../../services/api_service.dart';
import '../charts/fl_chart_renderer.dart';
import '../presentation/kpi_card_grid.dart';
import '../transparency/nlp_transparency_card.dart';
import '../dataset/dataset_status_dialog.dart';
import '../evaluation/evaluation_dashboard_screen.dart';

class ChatMessage {
  final bool isUser;
  final String text;
  final ChatResponse? response;
  final String? errorMessage;

  ChatMessage({
    required this.isUser,
    required this.text,
    this.response,
    this.errorMessage,
  });
}

class ChatScreen extends StatefulWidget {
  final ApiService apiService;

  const ChatScreen({super.key, required this.apiService});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;
  String? _conversationId;

  final List<String> _suggestedPrompts = [
    'How has Virat Kohli performed in ODIs?',
    'Compare Virat Kohli and Rohit Sharma in ODIs',
    "Show Virat Kohli's last 10 innings as a line chart",
    'How consistent has Virat Kohli been across his innings?',
  ];

  @override
  void initState() {
    super.initState();
    _conversationId = 'conv_${DateTime.now().millisecondsSinceEpoch}';
    // Add welcome message
    _messages.add(
      ChatMessage(
        isUser: false,
        text: 'Welcome to CricInsight! Ask any question about player statistics, opponent analysis, form trends, or player comparisons grounded in official Cricsheet records.',
      ),
    );
  }

  void _sendMessage([String? promptOverride]) async {
    final query = promptOverride ?? _controller.text.trim();
    if (query.isEmpty || _isLoading) return;

    _controller.clear();
    setState(() {
      _messages.add(ChatMessage(isUser: true, text: query));
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final response = await widget.apiService.sendQuery(
        query: query,
        conversationId: _conversationId,
      );

      setState(() {
        _isLoading = false;
        _messages.add(ChatMessage(
          isUser: false,
          text: response.answer,
          response: response,
        ));
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _messages.add(ChatMessage(
          isUser: false,
          text: 'Error processing request.',
          errorMessage: e.toString(),
        ));
      });
    }

    _scrollToBottom();
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
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        elevation: 0,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: const Color(0xFF00E5FF).withOpacity(0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.sports_cricket, color: Color(0xFF00E5FF), size: 20),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'CricInsight',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                Text(
                  'Cricket Analytics grounded in Cricsheet data',
                  style: TextStyle(fontSize: 10, color: Colors.white54),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.analytics_outlined, color: Color(0xFF00E5FF)),
            tooltip: 'NLP Evaluation Dashboard',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => EvaluationDashboardScreen(apiService: widget.apiService),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.storage_outlined, color: Colors.white70),
            tooltip: 'Dataset Coverage & Freshness',
            onPressed: () {
              showDialog(
                context: context,
                builder: (context) => DatasetStatusDialog(apiService: widget.apiService),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white70),
            tooltip: 'New Conversation',
            onPressed: () {
              setState(() {
                _conversationId = 'conv_${DateTime.now().millisecondsSinceEpoch}';
                _messages.clear();
                _messages.add(
                  ChatMessage(
                    isUser: false,
                    text: 'Conversation reset. What player or match would you like to explore?',
                  ),
                );
              });
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                itemCount: _messages.length,
                itemBuilder: (context, idx) {
                  return _buildMessageItem(_messages[idx]);
                },
              ),
            ),
            if (_isLoading)
              Container(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF00E5FF)),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      'Analyzing Cricsheet records...',
                      style: TextStyle(fontSize: 12, color: Colors.cyanAccent.shade200),
                    ),
                  ],
                ),
              ),
            _buildSuggestedChips(),
            _buildInputArea(),
          ],
        ),
      ),
    );
  }

  Widget _buildSuggestedChips() {
    return Container(
      height: 42,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: _suggestedPrompts.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, idx) {
          final prompt = _suggestedPrompts[idx];
          return ActionChip(
            label: Text(
              prompt,
              style: const TextStyle(fontSize: 11, color: Colors.white70),
            ),
            backgroundColor: const Color(0xFF161B22),
            side: const BorderSide(color: Color(0xFF30363D)),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            onPressed: () => _sendMessage(prompt),
          );
        },
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: const BoxDecoration(
        color: Color(0xFF161B22),
        border: Border(top: BorderSide(color: Color(0xFF30363D))),
      ),
      child: Row(
        children: [
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              decoration: BoxDecoration(
                color: const Color(0xFF0D1117),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: const Color(0xFF30363D)),
              ),
              child: TextField(
                controller: _controller,
                style: const TextStyle(color: Colors.white, fontSize: 13),
                decoration: const InputDecoration(
                  hintText: 'Ask cricket question (e.g. Compare Kohli and Rohit)...',
                  hintStyle: TextStyle(color: Colors.white38, fontSize: 13),
                  border: InputBorder.none,
                ),
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
          ),
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.send_rounded, color: Color(0xFF00E5FF)),
            onPressed: () => _sendMessage(),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageItem(ChatMessage msg) {
    if (msg.isUser) {
      return Align(
        alignment: Alignment.centerRight,
        child: Container(
          margin: const EdgeInsets.only(bottom: 12, left: 48),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(
            color: const Color(0xFF1F6FEB),
            borderRadius: BorderRadius.circular(16).copyWith(bottomRight: const Radius.circular(2)),
          ),
          child: Text(
            msg.text,
            style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4),
          ),
        ),
      );
    }

    if (msg.errorMessage != null) {
      return Container(
        margin: const EdgeInsets.only(bottom: 12, right: 32),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.red.withOpacity(0.12),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.redAccent.withOpacity(0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.error_outline, size: 18, color: Colors.redAccent),
                const SizedBox(width: 8),
                const Text(
                  'Query Execution Failed',
                  style: TextStyle(fontWeight: FontWeight.bold, color: Colors.redAccent, fontSize: 12),
                ),
                const Spacer(),
                TextButton(
                  onPressed: () => _sendMessage(msg.text),
                  child: const Text('Retry', style: TextStyle(color: Colors.cyanAccent, fontSize: 11)),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              msg.errorMessage!,
              style: const TextStyle(color: Colors.white70, fontSize: 11),
            ),
          ],
        ),
      );
    }

    final resp = msg.response;
    return Container(
      margin: const EdgeInsets.only(bottom: 16, right: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF161B22),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF30363D)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    const CircleAvatar(
                      radius: 12,
                      backgroundColor: Color(0xFF238636),
                      child: Icon(Icons.check, size: 14, color: Colors.white),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      resp != null && resp.status == 'clarification_required'
                          ? 'Clarification Needed'
                          : 'CricInsight Verified Analysis',
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const Spacer(),
                    if (resp != null && resp.status == 'success')
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFF238636).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: const Color(0xFF238636)),
                        ),
                        child: const Text(
                          'Ground Truth Evidence',
                          style: TextStyle(fontSize: 10, color: Color(0xFF3FB950), fontWeight: FontWeight.w600),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  msg.text,
                  style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.45),
                ),
                if (resp != null && resp.clarificationRequired && resp.clarificationQuestion != null) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.orange.withOpacity(0.3)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          resp.clarificationQuestion!,
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.orangeAccent),
                        ),
                        if (resp.clarificationOptions != null && resp.clarificationOptions!.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Wrap(
                            spacing: 6,
                            runSpacing: 6,
                            children: resp.clarificationOptions!
                                .map((opt) => ActionChip(
                                      label: Text(opt, style: const TextStyle(fontSize: 11, color: Colors.white)),
                                      backgroundColor: const Color(0xFF21262D),
                                      onPressed: () => _sendMessage(opt),
                                    ))
                                .toList(),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (resp != null) ...[
            if (resp.metrics.length == 1) ...[
              const SizedBox(height: 10),
              KpiCardGrid(metrics: resp.metrics.first),
            ] else if (resp.metrics.length > 1) ...[
              const SizedBox(height: 10),
              _buildComparisonCards(resp.metrics),
            ],
            if (resp.chart.isNotEmpty && resp.chart['chart_type'] != 'empty') ...[
              const SizedBox(height: 8),
              FlChartRenderer(chartSpec: resp.chart),
            ],
            NlpTransparencyCard(
              interpretation: resp.interpretation,
              confidence: resp.confidence.toMap(),
              provider: resp.provider.toMap(),
              limitations: resp.limitations,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildComparisonCards(List<Map<String, dynamic>> playersMetrics) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Head-to-Head Comparison',
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 10),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              headingRowColor: MaterialStateProperty.all(const Color(0xFF21262D)),
              columns: const [
                DataColumn(label: Text('Player', style: TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold))),
                DataColumn(label: Text('Runs', style: TextStyle(color: Colors.white))),
                DataColumn(label: Text('Avg', style: TextStyle(color: Colors.white))),
                DataColumn(label: Text('SR', style: TextStyle(color: Colors.white))),
                DataColumn(label: Text('100s/50s', style: TextStyle(color: Colors.white))),
                DataColumn(label: Text('HS', style: TextStyle(color: Colors.white))),
              ],
              rows: playersMetrics.map((p) {
                final name = p['player_name'] ?? 'Unknown';
                final runs = p['total_runs'] ?? 0;
                final avg = p['batting_average']?.toString() ?? 'N/A';
                final sr = p['strike_rate']?.toString() ?? '0.0';
                final tons = '${p['centuries'] ?? 0}/${p['fifties'] ?? 0}';
                final hs = '${p['high_score'] ?? 0}${p['high_score_not_out'] == true ? '*' : ''}';

                return DataRow(cells: [
                  DataCell(Text(name, style: const TextStyle(fontWeight: FontWeight.w600, color: Colors.white))),
                  DataCell(Text('$runs', style: const TextStyle(color: Colors.white70))),
                  DataCell(Text(avg, style: const TextStyle(color: Color(0xFF00E676), fontWeight: FontWeight.bold))),
                  DataCell(Text(sr, style: const TextStyle(color: Color(0xFFFFD600)))),
                  DataCell(Text(tons, style: const TextStyle(color: Colors.white70))),
                  DataCell(Text(hs, style: const TextStyle(color: Colors.white70))),
                ]);
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

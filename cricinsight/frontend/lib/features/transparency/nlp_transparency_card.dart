import 'package:flutter/material.dart';

class NlpTransparencyCard extends StatefulWidget {
  final Map<String, dynamic> interpretation;
  final Map<String, dynamic> confidence;
  final Map<String, dynamic> provider;
  final List<dynamic>? limitations;

  const NlpTransparencyCard({
    super.key,
    required this.interpretation,
    required this.confidence,
    required this.provider,
    this.limitations,
  });

  @override
  State<NlpTransparencyCard> createState() => _NlpTransparencyCardState();
}

class _NlpTransparencyCardState extends State<NlpTransparencyCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    final overallConf = (widget.confidence['overall_confidence'] as num?)?.toDouble() ?? 0.0;
    final confPercent = (overallConf * 100).toStringAsFixed(1);
    final providerName = widget.provider['provider'] ?? 'system';
    final modelName = widget.provider['model'] ?? 'deterministic';
    final latency = widget.provider['latency_ms'] ?? 0;
    final intent = widget.interpretation['intent'] ?? 'unknown';

    Color confColor = Colors.orangeAccent;
    if (overallConf >= 0.8) {
      confColor = const Color(0xFF00E676);
    } else if (overallConf < 0.5) {
      confColor = Colors.redAccent;
    }

    return Container(
      margin: const EdgeInsets.only(top: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF131720),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        children: [
          InkWell(
            onTap: () {
              setState(() {
                _isExpanded = !_isExpanded;
              });
            },
            borderRadius: BorderRadius.circular(10),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Row(
                children: [
                  Icon(Icons.psychology, size: 18, color: Colors.cyanAccent.shade200),
                  const SizedBox(width: 8),
                  Text(
                    'NLP: $intent',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Colors.white70,
                    ),
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: confColor.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(color: confColor.withOpacity(0.4)),
                    ),
                    child: Text(
                      '$confPercent% Conf',
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: confColor),
                    ),
                  ),
                  const SizedBox(width: 6),
                  Icon(
                    _isExpanded ? Icons.expand_less : Icons.expand_more,
                    size: 18,
                    color: Colors.white54,
                  ),
                ],
              ),
            ),
          ),
          if (_isExpanded) ...[
            const Divider(height: 1, color: Colors.white10),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildRow('Provider / Model:', '$providerName ($modelName) • ${latency}ms'),
                  _buildRow('Intent:', intent),
                  if (widget.interpretation['players'] != null)
                    _buildRow('Resolved Players:', (widget.interpretation['players'] as List).join(', ')),
                  if (widget.interpretation['opponent'] != null)
                    _buildRow('Opponent:', widget.interpretation['opponent']),
                  if (widget.interpretation['format'] != null)
                    _buildRow('Format Filter:', widget.interpretation['format']),
                  if (widget.interpretation['last_n_innings'] != null)
                    _buildRow('Recent Window:', 'Last ${widget.interpretation['last_n_innings']} innings'),
                  if (widget.interpretation['metrics'] != null)
                    _buildRow('Metrics:', (widget.interpretation['metrics'] as List).join(', ')),
                  if (widget.limitations != null && widget.limitations!.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      'Data Coverage Limitations:',
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.amber.shade300),
                    ),
                    const SizedBox(height: 2),
                    for (final lim in widget.limitations!)
                      Text('• $lim', style: const TextStyle(fontSize: 11, color: Colors.white60)),
                  ],
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2.5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(fontSize: 11, color: Colors.white54),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }
}

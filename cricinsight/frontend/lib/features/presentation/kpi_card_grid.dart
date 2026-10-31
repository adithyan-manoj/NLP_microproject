import 'package:flutter/material.dart';

class KpiCardGrid extends StatelessWidget {
  final Map<String, dynamic> metrics;

  const KpiCardGrid({super.key, required this.metrics});

  @override
  Widget build(BuildContext context) {
    final runs = metrics['total_runs'] ?? 0;
    final avg = metrics['batting_average'] != null ? '${metrics['batting_average']}' : 'N/A';
    final sr = metrics['strike_rate'] != null ? '${metrics['strike_rate']}' : '0.0';
    final hs = '${metrics['high_score'] ?? 0}${metrics['high_score_not_out'] == true ? '*' : ''}';
    final centuries = metrics['centuries'] ?? 0;
    final fifties = metrics['fifties'] ?? 0;
    final boundaries = '${metrics['fours'] ?? 0} fours / ${metrics['sixes'] ?? 0} sixes';
    final stdDev = '${metrics['std_deviation'] ?? 0.0}';

    final cards = [
      _KpiItem('Total Runs', runs.toString(), Icons.sports_cricket, const Color(0xFF00E5FF)),
      _KpiItem('Batting Average', avg, Icons.trending_up, const Color(0xFF00E676)),
      _KpiItem('Strike Rate', sr, Icons.speed, const Color(0xFFFFD600)),
      _KpiItem('High Score', hs, Icons.emoji_events, const Color(0xFFFF9100)),
      _KpiItem('Centuries / 50s', '$centuries / $fifties', Icons.workspace_premium, const Color(0xFFE040FB)),
      _KpiItem('Boundaries', boundaries, Icons.sports_score, const Color(0xFF7C4DFF)),
      _KpiItem('Consistency (σ)', stdDev, Icons.analytics, const Color(0xFF2979FF)),
    ];

    return LayoutBuilder(
      builder: (context, constraints) {
        final crossAxisCount = constraints.maxWidth > 700 ? 4 : (constraints.maxWidth > 400 ? 2 : 1);
        return GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: crossAxisCount,
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
            childAspectRatio: 1.3,
          ),
          itemCount: cards.length,
          itemBuilder: (context, idx) => _buildCard(cards[idx]),
        );
      },
    );
  }

  Widget _buildCard(_KpiItem item) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF1E222D),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.white10),
      ),
      child: FittedBox(
        fit: BoxFit.scaleDown,
        alignment: Alignment.centerLeft,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Icon(item.icon, size: 16, color: item.accentColor),
                const SizedBox(width: 6),
                Text(
                  item.label,
                  style: const TextStyle(fontSize: 12, color: Colors.white60, fontWeight: FontWeight.w500),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              item.value,
              style: const TextStyle(fontSize: 20, color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }
}

class _KpiItem {
  final String label;
  final String value;
  final IconData icon;
  final Color accentColor;

  _KpiItem(this.label, this.value, this.icon, this.accentColor);
}

import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class FlChartRenderer extends StatelessWidget {
  final Map<String, dynamic> chartSpec;

  const FlChartRenderer({super.key, required this.chartSpec});

  @override
  Widget build(BuildContext context) {
    final chartType = chartSpec['chart_type'] as String? ?? 'empty';
    final title = chartSpec['title'] as String? ?? 'Data Visualization';
    final subtitle = chartSpec['subtitle'] as String? ?? '';

    if (chartType == 'empty') {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: const Color(0xFF1E222D),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white10),
        ),
        child: Column(
          children: [
            const Icon(Icons.bar_chart, size: 48, color: Colors.white24),
            const SizedBox(height: 12),
            Text(
              chartSpec['empty_state_message'] ?? 'No visualization available.',
              style: const TextStyle(color: Colors.white70),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 12),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1F2C),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2E384D)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 10,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          if (subtitle.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              subtitle,
              style: const TextStyle(fontSize: 13, color: Colors.white60),
            ),
          ],
          const SizedBox(height: 24),
          SizedBox(
            height: 280,
            child: chartType == 'line'
                ? _buildLineChart(context)
                : _buildGroupedBarChart(context),
          ),
        ],
      ),
    );
  }

  Widget _buildLineChart(BuildContext context) {
    final seriesList = chartSpec['series'] as List<dynamic>? ?? [];
    if (seriesList.isEmpty) return const SizedBox();

    final primarySeries = seriesList[0] as Map<String, dynamic>;
    final points = primarySeries['points'] as List<dynamic>? ?? [];
    if (points.isEmpty) return const SizedBox();

    final spots = <FlSpot>[];
    double maxY = 0;

    for (int i = 0; i < points.length; i++) {
      final p = points[i];
      final y = (p['y'] as num).toDouble();
      if (y > maxY) maxY = y;
      spots.add(FlSpot(i.toDouble() + 1, y));
    }

    return LineChart(
      LineChartData(
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          getDrawingHorizontalLine: (value) => const FlLine(
            color: Colors.white10,
            strokeWidth: 1,
          ),
        ),
        titlesData: FlTitlesData(
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 30,
              interval: points.length > 10 ? 2 : 1,
              getTitlesWidget: (value, meta) {
                final idx = value.toInt() - 1;
                if (idx >= 0 && idx < points.length) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      '#${value.toInt()}',
                      style: const TextStyle(color: Colors.white54, fontSize: 11),
                    ),
                  );
                }
                return const SizedBox();
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              getTitlesWidget: (value, meta) {
                return Text(
                  value.toInt().toString(),
                  style: const TextStyle(color: Colors.white54, fontSize: 11),
                );
              },
            ),
          ),
        ),
        borderData: FlBorderData(show: false),
        minX: 1,
        maxX: spots.length.toDouble(),
        minY: 0,
        maxY: maxY > 0 ? (maxY * 1.15) : 50,
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: const Color(0xFF00E5FF),
            barWidth: 3.5,
            isStrokeCapRound: true,
            dotData: FlDotData(
              show: true,
              getDotPainter: (spot, percent, barData, index) => FlDotCirclePainter(
                radius: 4.5,
                color: const Color(0xFF00E5FF),
                strokeWidth: 2,
                strokeColor: Colors.white,
              ),
            ),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                colors: [
                  const Color(0xFF00E5FF).withOpacity(0.35),
                  const Color(0xFF00E5FF).withOpacity(0.0),
                ],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
          ),
        ],
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (touchedSpots) {
              return touchedSpots.map((spot) {
                final idx = spot.spotIndex;
                final tooltipText = (idx >= 0 && idx < points.length)
                    ? points[idx]['tooltip'] ?? '${spot.y.toInt()} runs'
                    : '${spot.y.toInt()} runs';
                return LineTooltipItem(
                  tooltipText,
                  const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
                );
              }).toList();
            },
          ),
        ),
      ),
    );
  }

  Widget _buildGroupedBarChart(BuildContext context) {
    final series = chartSpec['series'] as List<dynamic>? ?? [];
    if (series.isEmpty) return const SizedBox();

    final barGroups = <BarChartGroupData>[];
    final players = <String>[];

    final firstSeriesBars = (series[0]['bars'] as List<dynamic>?) ?? [];
    for (int i = 0; i < firstSeriesBars.length; i++) {
      players.add(firstSeriesBars[i]['x'] ?? 'P$i');
    }

    final colors = [
      const Color(0xFF00E5FF),
      const Color(0xFF00E676),
      const Color(0xFFFFD600),
    ];

    double maxY = 0;

    for (int pIdx = 0; pIdx < players.length; pIdx++) {
      final rods = <BarChartRodData>[];
      for (int sIdx = 0; sIdx < series.length; sIdx++) {
        final bars = series[sIdx]['bars'] as List<dynamic>? ?? [];
        final yVal = (pIdx < bars.length) ? (bars[pIdx]['y'] as num).toDouble() : 0.0;
        if (yVal > maxY) maxY = yVal;
        rods.add(
          BarChartRodData(
            toY: yVal,
            color: colors[sIdx % colors.length],
            width: 14,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
          ),
        );
      }
      barGroups.add(
        BarChartGroupData(
          x: pIdx,
          barRods: rods,
          barsSpace: 4,
        ),
      );
    }

    return Column(
      children: [
        // Legend
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(series.length, (idx) {
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Row(
                children: [
                  Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      color: colors[idx % colors.length],
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    series[idx]['name'] ?? 'Metric',
                    style: const TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                ],
              ),
            );
          }),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: BarChart(
            BarChartData(
              barGroups: barGroups,
              gridData: const FlGridData(show: false),
              borderData: FlBorderData(show: false),
              maxY: maxY > 0 ? (maxY * 1.15) : 100,
              titlesData: FlTitlesData(
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      final idx = value.toInt();
                      if (idx >= 0 && idx < players.length) {
                        return Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            players[idx],
                            style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600),
                          ),
                        );
                      }
                      return const SizedBox();
                    },
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 40,
                    getTitlesWidget: (value, meta) {
                      return Text(
                        value.toInt().toString(),
                        style: const TextStyle(color: Colors.white54, fontSize: 11),
                      );
                    },
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

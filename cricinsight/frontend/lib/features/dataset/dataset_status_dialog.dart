import 'package:flutter/material.dart';
import '../../services/api_service.dart';

class DatasetStatusDialog extends StatefulWidget {
  final ApiService apiService;

  const DatasetStatusDialog({super.key, required this.apiService});

  @override
  State<DatasetStatusDialog> createState() => _DatasetStatusDialogState();
}

class _DatasetStatusDialogState extends State<DatasetStatusDialog> {
  late Future<Map<String, dynamic>> _coverageFuture;

  @override
  void initState() {
    super.initState();
    _coverageFuture = widget.apiService.getDatasetCoverage();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: const Color(0xFF161B26),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        padding: const EdgeInsets.all(24),
        constraints: const BoxConstraints(maxWidth: 550),
        child: FutureBuilder<Map<String, dynamic>>(
          future: _coverageFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const SizedBox(
                height: 200,
                child: Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF))),
              );
            }
            if (snapshot.hasError) {
              return Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
                  const SizedBox(height: 12),
                  Text(
                    'Failed to load dataset status:\n${snapshot.error}',
                    style: const TextStyle(color: Colors.white70),
                    textAlign: TextAlign.center,
                  ),
                ],
              );
            }

            final data = snapshot.data ?? {};
            final matchCount = data['total_matches'] ?? 0;
            final lastUpdated = data['last_updated'] ?? 'N/A';
            final formats = (data['formats'] as List?)?.map((e) => e.toString()).toList() ?? [];
            final teams = (data['teams'] as List?)?.map((e) => e.toString()).toList() ?? [];
            final limitations = (data['limitations'] as List?)?.map((e) => e.toString()).toList() ?? [];

            return Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.storage, color: Color(0xFF00E5FF), size: 28),
                    const SizedBox(width: 12),
                    const Text(
                      'Cricsheet Dataset Status',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    const Spacer(),
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white54),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ],
                ),
                const Divider(color: Colors.white12, height: 24),
                _statItem('Primary Source of Truth:', 'Authoritative Cricsheet JSON'),
                _statItem('Ingested Matches:', '$matchCount matches'),
                _statItem('Last Ingestion Timestamp:', lastUpdated),
                const SizedBox(height: 12),
                const Text(
                  'Available Formats:',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.white70),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: formats.isEmpty
                      ? [const Chip(label: Text('None (Import Needed)'))]
                      : formats
                          .map((f) => Chip(
                                label: Text(f, style: const TextStyle(fontSize: 11, color: Colors.white)),
                                backgroundColor: const Color(0xFF232B3E),
                              ))
                          .toList(),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Covered Teams:',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.white70),
                ),
                const SizedBox(height: 6),
                Text(
                  teams.isEmpty ? 'No teams ingested yet.' : teams.join(', '),
                  style: const TextStyle(fontSize: 12, color: Colors.white60),
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
                if (limitations.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.amber.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.amber.withOpacity(0.3)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.info_outline, size: 16, color: Colors.amber.shade300),
                            const SizedBox(width: 6),
                            Text(
                              'Coverage Limitations',
                              style: TextStyle(
                                  fontSize: 12, fontWeight: FontWeight.bold, color: Colors.amber.shade300),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        for (final lim in limitations)
                          Text('• $lim', style: const TextStyle(fontSize: 11, color: Colors.white70)),
                      ],
                    ),
                  ),
                ],
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _statItem(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: Colors.white54)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
              textAlign: TextAlign.end,
            ),
          ),
        ],
      ),
    );
  }
}

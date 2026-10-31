class ConfidenceData {
  final double overallConfidence;
  final double modelConfidence;
  final bool schemaValid;
  final double entityResolutionScore;
  final bool temporalValid;

  ConfidenceData({
    required this.overallConfidence,
    required this.modelConfidence,
    required this.schemaValid,
    required this.entityResolutionScore,
    required this.temporalValid,
  });

  factory ConfidenceData.fromJson(Map<String, dynamic> json) {
    return ConfidenceData(
      overallConfidence: (json['overall_confidence'] as num?)?.toDouble() ?? 0.0,
      modelConfidence: (json['model_confidence'] as num?)?.toDouble() ?? 0.0,
      schemaValid: json['schema_valid'] ?? true,
      entityResolutionScore: (json['entity_resolution_score'] as num?)?.toDouble() ?? 0.0,
      temporalValid: json['temporal_valid'] ?? true,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'overall_confidence': overallConfidence,
      'model_confidence': modelConfidence,
      'schema_valid': schemaValid,
      'entity_resolution_score': entityResolutionScore,
      'temporal_valid': temporalValid,
    };
  }
}

class ProviderData {
  final String provider;
  final String model;
  final double latencyMs;
  final bool fallbackUsed;
  final String? fallbackReason;

  ProviderData({
    required this.provider,
    required this.model,
    required this.latencyMs,
    required this.fallbackUsed,
    this.fallbackReason,
  });

  factory ProviderData.fromJson(Map<String, dynamic> json) {
    return ProviderData(
      provider: json['provider'] ?? json['name'] ?? 'unknown',
      model: json['model'] ?? 'unknown',
      latencyMs: (json['latency_ms'] as num?)?.toDouble() ?? 0.0,
      fallbackUsed: json['fallback_used'] ?? false,
      fallbackReason: json['fallback_reason'],
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'provider': provider,
      'model': model,
      'latency_ms': latencyMs,
      'fallback_used': fallbackUsed,
      'fallback_reason': fallbackReason,
    };
  }
}

class ChatQueryResponseModel {
  final String requestId;
  final String status;
  final String answer;
  final Map<String, dynamic> interpretation;
  final ConfidenceData confidence;
  final ProviderData provider;
  final List<Map<String, dynamic>> metrics;
  final Map<String, dynamic> chart;
  final List<dynamic> evidence;
  final Map<String, dynamic> datasetCoverage;
  final List<String> limitations;
  final bool clarificationRequired;
  final String? clarificationQuestion;
  final List<String> clarificationOptions;

  ChatQueryResponseModel({
    required this.requestId,
    required this.status,
    required this.answer,
    required this.interpretation,
    required this.confidence,
    required this.provider,
    required this.metrics,
    required this.chart,
    required this.evidence,
    required this.datasetCoverage,
    required this.limitations,
    required this.clarificationRequired,
    this.clarificationQuestion,
    required this.clarificationOptions,
  });

  factory ChatQueryResponseModel.fromJson(Map<String, dynamic> json) {
    final rawMetrics = json['metrics'] as List<dynamic>? ?? [];
    final typedMetrics = rawMetrics.map((m) => Map<String, dynamic>.from(m as Map)).toList();

    return ChatQueryResponseModel(
      requestId: json['request_id'] ?? '',
      status: json['status'] ?? 'unknown',
      answer: json['answer'] ?? '',
      interpretation: (json['interpretation'] as Map<String, dynamic>?) ?? {},
      confidence: ConfidenceData.fromJson(json['confidence'] ?? {}),
      provider: ProviderData.fromJson(json['provider'] ?? {}),
      metrics: typedMetrics,
      chart: (json['chart'] as Map<String, dynamic>?) ?? {},
      evidence: json['evidence'] ?? [],
      datasetCoverage: (json['dataset_coverage'] as Map<String, dynamic>?) ?? {},
      limitations: (json['limitations'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      clarificationRequired: json['clarification_required'] ?? false,
      clarificationQuestion: json['clarification_question'] ?? json['interpretation']?['clarification_question'],
      clarificationOptions: (json['clarification_options'] as List<dynamic>?)?.map((e) => e.toString()).toList() ??
          (json['interpretation']?['clarification_options'] as List<dynamic>?)?.map((e) => e.toString()).toList() ??
          [],
    );
  }
}

typedef ChatResponse = ChatQueryResponseModel;

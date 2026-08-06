import 'deviation_design_system.dart';

// ============================================================================
// Design Quality Scorer — Template for per-screen deviation scoring
//
// Copy this file and customize the engine scores for each screen.
// Target: ≥80 internal, ≥85 public-facing, ≥90 ±30σ.
//
// Each screen gets a Map<DeviationEngine, double> where:
//   - 0.0 = engine not applied / completely failing
//   - 0.5 = partially applied
//   - 1.0 = fully applied / ±30σ quality
// ============================================================================

class DesignQualityScorer {
  const DesignQualityScorer._();

  /// Score a single screen. Customize the engine scores per screen.
  static DesignScore scoreMyScreen() {
    return DeviationDesignSystem.scoreScreen(const {
      // Physics engines (±30σ)
      DeviationEngine.quantumTunneling: 0.8,
      DeviationEngine.pauliExclusion: 0.85,
      DeviationEngine.casimirPressure: 0.9,
      DeviationEngine.fineTuning: 1.0,
      DeviationEngine.hawkingRadiation: 0.7,
      DeviationEngine.speedOfLight: 0.9,
      DeviationEngine.absoluteZero: 1.0,
      DeviationEngine.phaseTransition: 0.6,
      DeviationEngine.bellEntanglement: 0.8,
      DeviationEngine.vacuumFluctuation: 0.7,
      // Cognitive engines (±20σ)
      DeviationEngine.gravityEscape: 0.6,
      DeviationEngine.realityAnchor: 0.9,
      DeviationEngine.feynmanXRay: 0.5,
      // Nature engines (±20σ)
      DeviationEngine.antColonyPheromone: 0.7,
      DeviationEngine.beeForaging: 0.85,
      DeviationEngine.slimeMoldNetwork: 0.5,
    });
  }

  /// Score all screens and return aggregate.
  static AggregateScore scoreAll() {
    final scores = {
      'Screen1': scoreMyScreen(),
      // Add more screens here
    };

    final avg = scores.values
            .fold<double>(0, (sum, s) => sum + s.normalized) /
        scores.length;

    final lowest = scores.entries.reduce(
        (a, b) => a.value.normalized < b.value.normalized ? a : b);
    final highest = scores.entries.reduce(
        (a, b) => a.value.normalized > b.value.normalized ? a : b);

    return AggregateScore(
      screenScores: scores,
      averageNormalized: avg,
      lowestScreen: lowest.key,
      lowestScore: lowest.value,
      highestScreen: highest.key,
      highestScore: highest.value,
      tier: DeviationDesignSystem.tierFor(avg),
    );
  }
}

class AggregateScore {
  const AggregateScore({
    required this.screenScores,
    required this.averageNormalized,
    required this.lowestScreen,
    required this.lowestScore,
    required this.highestScreen,
    required this.highestScore,
    required this.tier,
  });

  final Map<String, DesignScore> screenScores;
  final double averageNormalized;
  final String lowestScreen;
  final DesignScore lowestScore;
  final String highestScreen;
  final DesignScore highestScore;
  final QualityTier tier;
}

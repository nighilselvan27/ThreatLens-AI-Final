from risk_scorer import RiskScorer


test_probabilities = [
    0.01,
    0.10,
    0.25,
    0.49,
    0.50,
    0.75,
    0.9743,
    0.99
]


print("=" * 60)
print("THREATLENS RISK SCORING TEST")
print("=" * 60)


for probability in test_probabilities:

    result = RiskScorer.analyze(probability)

    print(
        f"\nProbability : {probability:.4f}"
        f"\nVerdict     : {result['verdict']}"
        f"\nRisk Score  : {result['risk_score']}/100"
        f"\nRisk Level  : {result['risk_level']}"
    )


print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
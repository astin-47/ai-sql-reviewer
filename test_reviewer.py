
from reviewer import review_sql

sample_sql = """
SELECT *
FROM orders
WHERE DATE(order_date) = '2026-01-01';
"""

result = review_sql(sample_sql, dialect="PostgreSQL")

print("\n=== SQL REVIEW ===")
print("Summary:", result["summary"])
print("Overall risk:", result["overall_risk"])

print("\n=== FINDINGS ===")
for finding in result["findings"]:
    print(f"\n[{finding['severity'].upper()}] {finding['title']}")
    print("Category:", finding["category"])
    print("Explanation:", finding["explanation"])
    print("Recommendation:", finding["recommendation"])

print("\n=== SUGGESTED SQL ===")
print(result["suggested_sql"])

print("\n=== CAVEATS ===")
for caveat in result["caveats"]:
    print("-", caveat)

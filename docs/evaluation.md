# AI Evaluation Framework & Results

## Evaluation Methodology

The evaluation framework benchmark compares extracted field values and decision routing against a curated test dataset (`data/evaluation/dataset.json`).

### Tested Dimensions:
- **Field Exact-Match Accuracy**: Normalizes dates, currency, and decimal representations to evaluate exact agreement on invoice number, supplier name, date, subtotal, tax amount, and total amount.
- **Classification Performance**: Evaluates correct categorization across document categories (`invoice`, `receipt`, `purchase_order`, `contract`, `unknown`).
- **Decision Engine Consistency**: Validates that auto-eligible cases, review-required cases (such as amount limits and arithmetic mismatches), and duplicate submissions route as specified.
- **Operational Latency**: Measures median and p95 duration per document.

### Benchmark Results (from `scripts/evaluate_extraction.py`):
- Classification Accuracy: 100.0%
- Decision Routing Accuracy: 100.0%
- Field Extraction Accuracy: 100.0%
- Median Processing Latency: ~5.2 ms
- 95th Percentile Latency: ~24.7 ms

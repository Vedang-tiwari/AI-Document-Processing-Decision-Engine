import json
import sys
import time
from pathlib import Path
from decimal import Decimal
import numpy as np

# Ensure root dir in sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.services.document_parser import DocumentParserService
from backend.app.services.classification import ClassificationService
from backend.app.services.extraction import get_extraction_provider
from backend.app.services.validation import ValidationService
from backend.app.services.confidence import ConfidenceService
from backend.app.services.business_rules import BusinessRuleEngine
from backend.app.services.decision_engine import DecisionEngineService
from backend.app.services.duplicate_detection import DuplicateCheckResult
from backend.app.db.session import SessionLocal


def evaluate():
    eval_file = root_dir / "data" / "evaluation" / "dataset.json"
    samples_dir = root_dir / "data" / "samples"

    if not eval_file.exists():
        print(f"Error: {eval_file} not found.")
        return

    with open(eval_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    db = SessionLocal()
    provider = get_extraction_provider()

    total_samples = len(dataset)
    exact_matches = {
        "invoice_number": 0,
        "invoice_date": 0,
        "supplier_name": 0,
        "total_amount": 0,
        "subtotal": 0,
        "tax_amount": 0,
    }
    classification_correct = 0
    decision_correct = 0
    durations = []

    print(f"\n=======================================================")
    print(f" AI DOCUMENT PROCESSING & DECISION ENGINE - EVALUATION ")
    print(f"=======================================================")
    print(f"Dataset size: {total_samples} samples | Provider: {provider.__class__.__name__}\n")

    for item in dataset:
        filename = item["filename"]
        filepath = samples_dir / filename
        if not filepath.exists():
            print(f"Warning: sample file {filename} does not exist.")
            continue

        with open(filepath, "rb") as f:
            content = f.read()

        t0 = time.time()
        # 1. Parse
        parsed = DocumentParserService.parse(content, "application/pdf")
        # 2. Classify
        classification = ClassificationService.classify(parsed.full_text)
        # 3. Extract
        ext_data, evidence = provider.extract_invoice(parsed)
        # 4. Validate
        val_res = ValidationService.validate_invoice(ext_data)
        # 5. Confidence
        conf_res = ConfidenceService.calculate_confidence(
            ext_data, evidence, val_res, parsed.metadata.get("extraction_methods", [])
        )
        # 6. Rules & Decision
        rules = BusinessRuleEngine.evaluate_all(db, ext_data, is_duplicate=False)
        decision = DecisionEngineService.evaluate(
            document_type=classification.predicted_type,
            validation_result=val_res,
            confidence_result=conf_res,
            duplicate_result=DuplicateCheckResult(is_duplicate=False),
            anomalies=[],
            rule_results=rules,
        )
        elapsed_ms = (time.time() - t0) * 1000
        durations.append(elapsed_ms)

        # Compare Classification
        if classification.predicted_type == item["expected_classification"]:
            classification_correct += 1

        # Compare Extractions
        expected_ext = item["expected_extraction"]
        if ext_data.get("invoice_number") == expected_ext.get("invoice_number"):
            exact_matches["invoice_number"] += 1
        if ext_data.get("invoice_date") == expected_ext.get("invoice_date"):
            exact_matches["invoice_date"] += 1
        if (ext_data.get("supplier") or {}).get("name") == expected_ext.get("supplier_name"):
            exact_matches["supplier_name"] += 1
        if ext_data.get("total_amount") == expected_ext.get("total_amount"):
            exact_matches["total_amount"] += 1
        if ext_data.get("subtotal") == expected_ext.get("subtotal"):
            exact_matches["subtotal"] += 1
        if ext_data.get("tax_amount") == expected_ext.get("tax_amount"):
            exact_matches["tax_amount"] += 1

        # Compare Decision
        if decision.outcome == item["expected_decision"]:
            decision_correct += 1

        print(f"Sample: {filename:<32} | Decision: {decision.outcome:<15} (Expected: {item['expected_decision']}) | Time: {elapsed_ms:.1f}ms")

    db.close()

    print("\n------------------ METRICS REPORT ---------------------")
    print(f"Classification Accuracy:    {classification_correct / total_samples * 100:.1f}%")
    print(f"Decision Routing Accuracy:  {decision_correct / total_samples * 100:.1f}%")
    print("\nField Extraction Exact-Match Accuracies:")
    for field, count in exact_matches.items():
        print(f"  - {field:<24}: {count / total_samples * 100:.1f}%")

    print("\nOperational Quality:")
    print(f"  - Median duration:        {float(np.median(durations)):.1f} ms")
    print(f"  - 95th percentile duration: {float(np.percentile(durations, 95)):.1f} ms")
    print("=======================================================\n")


if __name__ == "__main__":
    evaluate()

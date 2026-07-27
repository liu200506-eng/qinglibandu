"""Quick check: how many questions in questions.json have resolved status."""
import json
from pathlib import Path

p = Path(__file__).parent / "questions.json"
qs = json.loads(p.read_text(encoding="utf-8"))

resolved = 0
unresolved = 0
for q in qs:
    status = q.get("chunk_resolution", {}).get("status", "missing")
    ids = q.get("relevant_chunk_ids", [])
    if status == "resolved" and ids:
        resolved += 1
    elif status == "unresolved":
        unresolved += 1
    else:
        print(f"  OTHER: {q.get('question_id')} status={status} ids={len(ids)}")

print(f"\nTotal: {len(qs)}, Resolved: {resolved}, Unresolved: {unresolved}")
print(f"Sum check: {resolved + unresolved} == {len(qs)}")

# Show sample resolved question's structure
for q in qs:
    if q.get("chunk_resolution", {}).get("status") == "resolved":
        print(f"\nSample resolved: {q['question_id']}")
        print(f"  relevant_chunk_ids: {q['relevant_chunk_ids']}")
        meta = q.get("resolved_chunk_metadata", [])
        if meta:
            print(f"  first metadata: point_id={meta[0].get('point_id')}, score={meta[0].get('score')}, doc={meta[0].get('document')}")
        break
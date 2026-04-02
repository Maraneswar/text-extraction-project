"""Quick API test script for Alldocex."""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

# Upload the test document
print("Uploading test_document.docx...")
with open("test_document.docx", "rb") as f:
    res = requests.post(
        f"{BASE_URL}/api/upload",
        files={"file": ("test_document.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )

data = res.json()
print(f"Upload response: {data['status']} - File ID: {data['file_id']}")
task_id = data["file_id"]

# Poll for results
print("Waiting for processing...")
for i in range(30):
    time.sleep(1)
    res = requests.get(f"{BASE_URL}/api/status/{task_id}")
    result = res.json()
    status = result["status"]
    print(f"  Poll {i+1}: {status}")
    if status in ("completed", "error"):
        break

print(f"\n{'='*50}")
print(f"STATUS: {result['status']}")
print(f"Processing time: {round(result.get('processing_time_ms', 0), 1)} ms")
print(f"{'='*50}")

# Extraction
if result.get("extraction"):
    ext = result["extraction"]
    print(f"\n--- EXTRACTION ---")
    print(f"Success: {ext['success']}")
    print(f"Word count: {ext['metadata']['word_count']}")
    print(f"Char count: {ext['metadata']['character_count']}")
    print(f"File type: {ext['metadata']['file_type']}")
    print(f"First 300 chars:\n{ext['raw_text'][:300]}")

# Summary
if result.get("summary"):
    s = result["summary"]
    print(f"\n--- SUMMARY ---")
    print(f"Algorithm: {s['algorithm']}")
    print(f"Original length: {s['original_length']}")
    print(f"Summary length: {s['summary_length']}")
    print(f"Compression: {round((1 - s['compression_ratio']) * 100, 1)}%")
    print(f"Summary:\n{s['summary'][:500]}")

# Entities
if result.get("entities"):
    e = result["entities"]
    print(f"\n--- ENTITIES ---")
    print(f"Total entities: {e['total_entities']}")
    print(f"Categories: {json.dumps(e['entity_counts'], indent=2)}")
    for ent in e["entities"][:20]:
        print(f"  [{ent['label']:8s}] {ent['text']} (x{ent['count']})")

# Sentiment
if result.get("sentiment"):
    sent = result["sentiment"]
    print(f"\n--- SENTIMENT ---")
    print(f"Label: {sent['overall_label']}")
    print(f"Compound: {sent['overall_compound']}")
    print(f"Positive: {sent['overall_positive']}")
    print(f"Negative: {sent['overall_negative']}")
    print(f"Neutral: {sent['overall_neutral']}")
    print(f"Sentence breakdowns: {len(sent['sentence_breakdown'])}")
    for sb in sent["sentence_breakdown"][:5]:
        print(f"  [{sb['label']:15s}] {sb['text'][:80]}...")

print("\n=== TEST COMPLETE ===")

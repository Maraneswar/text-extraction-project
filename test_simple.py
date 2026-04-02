"""Simple API test - writes results to file."""
import requests, time, json

BASE = "http://localhost:8000"
out = []

with open("test_document.docx", "rb") as f:
    res = requests.post(f"{BASE}/api/upload", files={"file": ("test_document.docx", f)})
data = res.json()
task_id = data["file_id"]
out.append(f"Upload: {data['status']} (ID: {task_id})")

for i in range(30):
    time.sleep(1)
    res = requests.get(f"{BASE}/api/status/{task_id}")
    result = res.json()
    if result["status"] in ("completed", "error"):
        break

out.append(f"Status: {result['status']}")
out.append(f"Time: {round(result.get('processing_time_ms', 0))}ms")

if result.get("extraction"):
    e = result["extraction"]
    out.append(f"\nEXTRACTION: success={e['success']}, words={e['metadata']['word_count']}")
    out.append(f"Text preview: {e['raw_text'][:200]}...")

if result.get("summary"):
    s = result["summary"]
    out.append(f"\nSUMMARY ({s['algorithm']}): compression={round((1-s['compression_ratio'])*100)}%")
    out.append(s["summary"][:400])

if result.get("entities"):
    ent = result["entities"]
    out.append(f"\nENTITIES: {ent['total_entities']} found")
    out.append(f"Categories: {json.dumps(ent['entity_counts'])}")
    for e in ent["entities"][:15]:
        out.append(f"  [{e['label']}] {e['text']} (x{e['count']})")

if result.get("sentiment"):
    s = result["sentiment"]
    out.append(f"\nSENTIMENT: {s['overall_label']} (compound={s['overall_compound']})")
    out.append(f"Pos={s['overall_positive']} Neg={s['overall_negative']} Neu={s['overall_neutral']}")

out.append("\nDONE")
text = "\n".join(out)
with open("test_output.txt", "w", encoding="utf-8") as f:
    f.write(text)
print(text)

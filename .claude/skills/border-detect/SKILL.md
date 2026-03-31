---
name: border-detect
description: Run multi-spectrum border detection diagnostic on an image — shows all 40 techniques ranked, agreement analysis, calibration weights.
---

# Border Detection Diagnostic

Run the full 40-technique multi-spectrum border detector in test mode (D) and display a diagnostic report.

## Steps

1. **Ensure server is running:**
   - Check if serve.py is responding at http://127.0.0.1:8080
   - If not, start it: `.venv/Scripts/python.exe serve.py` (or use `tests/helpers/server_manager.py`)

2. **Select test image:**
   - If user specified an image path, use that
   - Otherwise use the dark reference source: `input/Example quality image extraction/Dark background examples/Original Image dark background.png`

3. **Call /api/border-detect in test mode:**

```bash
.venv/Scripts/python.exe -c "
import base64, json, urllib.request
from pathlib import Path

img_path = '<IMAGE_PATH>'
ref_path = r'C:\Dev\Image generator\input\Example quality image extraction\Dark background examples\example preview ectraction dark background removed.PNG'

with open(img_path, 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

payload = json.dumps({
    'image': img_b64,
    'mode': 'test',
    'reference_path': ref_path
}).encode()

req = urllib.request.Request(
    'http://127.0.0.1:8080/api/border-detect',
    data=payload,
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req, timeout=60) as resp:
    result = json.loads(resp.read())

print(f'Techniques run: {result[\"techniques_run\"]}')
print(f'Processing time: {result[\"processing_ms\"]}ms')
print(f'Max consensus: {result[\"consensus_count\"]} techniques agree')

if 'diagnostics' in result:
    d = result['diagnostics']
    print(f'\nTOP 5: {d[\"top_5\"]}')
    print(f'BOTTOM 5: {d[\"bottom_5\"]}')
    print('\nAll technique scores (ranked):')
    scores = d['technique_scores']
    for tid, s in sorted(scores.items(), key=lambda x: x[1].get('composite', 0), reverse=True):
        ref = f'ref={s[\"iou_vs_reference\"]:.3f}' if 'iou_vs_reference' in s else 'ref=N/A'
        print(f'  {tid:25s} composite={s.get(\"composite\", 0):.4f}  {ref}  consensus={s.get(\"iou_vs_consensus\", 0):.4f}')
"
```

4. **Report results:**
   - Print the ranked technique scorecard
   - Highlight which techniques agree/disagree on border regions
   - Show calibration weight changes if any
   - Note overall border map quality (IoU vs reference if available)

5. **Save artifacts:**
   - Calibration updated in `tests/reports/border_calibration.json`
   - Border map can be saved via the endpoint response

"""Debug: download the ComfyUI mask and analyze its pixel values."""
import json, urllib.request, time
from PIL import Image
import numpy as np

BASE = "http://127.0.0.1:8000"

# Upload
print("Uploading...")
with open("C:/Dev/Image generator/input/Example UI 1.png", "rb") as f:
    import io
    from urllib.parse import urlencode
    boundary = b"----boundary123"
    body = b"------boundary123\r\nContent-Disposition: form-data; name=\"image\"; filename=\"test.png\"\r\nContent-Type: image/png\r\n\r\n" + f.read() + b"\r\n------boundary123\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n------boundary123--\r\n"
    req = urllib.request.Request(f"{BASE}/upload/image", data=body)
    req.add_header("Content-Type", "multipart/form-data; boundary=----boundary123")
    resp = urllib.request.urlopen(req)
    print("Upload:", json.loads(resp.read()))

# Queue with MASK_IMAGE output (index 2)
workflow = {
    "1": {"class_type": "LoadImage", "inputs": {"image": "test.png"}},
    "2": {"class_type": "RMBG", "inputs": {"model": "RMBG-2.0", "image": ["1", 0], "sensitivity": 1.0, "process_res": 1024, "mask_blur": 0, "mask_offset": 0, "invert_output": False, "refine_foreground": True, "background": "Alpha", "background_color": "#222222"}},
    "3": {"class_type": "SaveImage", "inputs": {"filename_prefix": "_debug_mask", "images": ["2", 2]}}
}
req = urllib.request.Request(f"{BASE}/prompt", data=json.dumps({"prompt": workflow}).encode(), headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
prompt_id = result["prompt_id"]
print(f"Queued: {prompt_id}")

# Poll
for _ in range(30):
    time.sleep(2)
    resp = urllib.request.urlopen(f"{BASE}/history/{prompt_id}")
    history = json.loads(resp.read())
    if prompt_id in history:
        entry = history[prompt_id]
        if entry.get("status", {}).get("status_str") == "success":
            break
        if entry.get("status", {}).get("status_str") == "error":
            print("ERROR:", entry["status"])
            exit(1)

# Download mask
outputs = entry["outputs"]
for nid, out in outputs.items():
    if "images" in out:
        img_info = out["images"][0]
        fn = img_info["filename"]
        url = f"{BASE}/view?filename={fn}&type=output"
        urllib.request.urlretrieve(url, "debug_mask.png")
        print(f"Downloaded: {fn}")

# Analyze
img = Image.open("debug_mask.png")
arr = np.array(img)
print(f"\nMask shape: {arr.shape}")
print(f"Channels: {arr.shape[2] if len(arr.shape) > 2 else 1}")
if len(arr.shape) > 2:
    for c, name in enumerate(["R", "G", "B", "A"][:arr.shape[2]]):
        ch = arr[:, :, c]
        print(f"  {name}: min={ch.min()} max={ch.max()} mean={ch.mean():.1f} zeros={np.sum(ch==0)} full={np.sum(ch==255)}")

    # Check: is the mask in RGB or alpha?
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    rgb_varies = r.min() != r.max()
    alpha_varies = arr.shape[2] == 4 and arr[:,:,3].min() != arr[:,:,3].max()
    print(f"\n  RGB varies: {rgb_varies}")
    print(f"  Alpha varies: {alpha_varies}")
    print(f"  Mask is in: {'ALPHA' if alpha_varies else 'RGB'}")

    # What percentage is white vs black in RGB?
    luminance = np.max(arr[:,:,:3], axis=2)
    white_pct = np.sum(luminance > 128) / luminance.size * 100
    print(f"  White pixels (RGB>128): {white_pct:.1f}%")
    print(f"  -> {'Needs invert (background is white)' if white_pct > 50 else 'Correct polarity (foreground is white)'}")

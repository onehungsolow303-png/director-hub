## Scripted Background Removal

This folder contains a small local tool for removing near-black backgrounds from flat UI sheets.

It works better than AI background removal when:

- the background is mostly black or very dark
- the foreground is a UI panel, icon sheet, or decorative frame
- you want a clean transparent PNG

### Presets

- `ui-balanced`: good default for most UI sheets
- `ui-soft`: preserves more soft shadow and dark edge glow
- `ui-hard`: cuts harder and removes more dark fringe

### Single Image

```powershell
$env:PYTHONPATH="C:\Dev\Image generator\.venv\Lib\site-packages"
& "C:\Users\bp303\AppData\Roaming\uv\python\cpython-3.12.11-windows-x86_64-none\python.exe" `
  C:\Dev\Image generator\scripted\remove_black_bg.py `
  --input "C:\path\to\image.png" `
  --output "C:\Dev\Image generator\output\my_asset.png" `
  --preset ui-balanced `
  --split-components `
  --crop-transparent-bounds
```

### Batch A Folder

```powershell
$env:PYTHONPATH="C:\Dev\Image generator\.venv\Lib\site-packages"
& "C:\Users\bp303\AppData\Roaming\uv\python\cpython-3.12.11-windows-x86_64-none\python.exe" `
  C:\Dev\Image generator\scripted\remove_black_bg.py `
  --input-dir "C:\Dev\Image generator\input" `
  --output-dir "C:\Dev\Image generator\output\batch" `
  --preset ui-soft `
  --split-components `
  --crop-transparent-bounds `
  --asset-subfolders
```

Batch mode now skips files that already look generated, such as names containing `_transparent` or `_part_`, unless you add `--include-processed`.

### Useful Overrides

```powershell
--threshold 20
--softness 20
--alpha-floor 8
--alpha-ceiling 245
--component-alpha-threshold 220
--min-component-pixels 5000
--component-pad 8
--max-components 2
```

### Output

By default the script writes:

- a transparent PNG with `_transparent` appended
- if `--split-components` is used, separate cropped PNGs with `_part_01`, `_part_02`, etc.
- if `--asset-subfolders` is used in batch mode, each source image gets its own output folder

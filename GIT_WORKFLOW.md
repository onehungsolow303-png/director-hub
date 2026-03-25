# Git Workflow

This project now has local git history. Use this workflow to keep changes easy to review and recover.

## Repo root

- [C:\Dev\Image generator](C:\Dev\Image generator)

## Current baseline

- Initial baseline commit:
  - `Initial baseline for UI asset cleanup app`

## Day-to-day workflow

1. Check current state

```powershell
git status
git log --oneline -n 10
```

2. Review what changed

```powershell
git diff
```

3. Stage intended files

```powershell
git add index.html app.js styles.css
```

Or stage everything relevant:

```powershell
git add .
```

4. Make a focused commit

Examples:

```powershell
git commit -m "Improve light-background edge cleanup"
git commit -m "Add imported AI mask refinement controls"
git commit -m "Document AI mask workflow and QA process"
```

## Commit style

Keep commit messages short and task-focused.

Good examples:

- `Improve split gallery usefulness sorting`
- `Add full-sheet positioned panel exports`
- `Fix imported AI mask validation`
- `Add session history and repo baseline`

Avoid:

- vague messages like `stuff`, `changes`, or `update`
- giant mixed commits when one feature could be separated cleanly

## Suggested change groups

Try to group commits by one clear purpose:

- UI controls and layout
- extraction logic
- mask pipeline
- docs and runbooks
- scripts and launchers

## Recovery commands

See recent history:

```powershell
git log --oneline --decorate --graph -n 20
```

See what changed in the last commit:

```powershell
git show --stat
```

Compare working tree against the last commit:

```powershell
git diff HEAD
```

## Notes for this project

- Large generated folders are intentionally ignored in [.gitignore](C:\Dev\Image generator\.gitignore):
  - `.venv`
  - `custom_nodes`
  - `models`
  - `temp`
  - `user`
  - `output`
  - `input`
- Core tracked app files are:
  - [index.html](C:\Dev\Image generator\index.html)
  - [app.js](C:\Dev\Image generator\app.js)
  - [styles.css](C:\Dev\Image generator\styles.css)
- Core tracked documentation includes:
  - [SESSION_HISTORY.md](C:\Dev\Image generator\SESSION_HISTORY.md)
  - [PROJECT_MEMORY.md](C:\Dev\Image generator\PROJECT_MEMORY.md)
  - [QA_RUNBOOK.md](C:\Dev\Image generator\QA_RUNBOOK.md)
  - [AI_MASK_WORKFLOW_GUIDE.md](C:\Dev\Image generator\AI_MASK_WORKFLOW_GUIDE.md)

## Recommended habit

After each meaningful improvement:

1. verify the app still works
2. verify JS syntax for [app.js](C:\Dev\Image generator\app.js)
3. update docs if behavior changed
4. make one clear commit

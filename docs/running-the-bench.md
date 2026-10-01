# Running the bench: folders

Keep the public repository and the place where AIs work apart:

```
~/MainStreetBench/
├── mainstreetbench/   git clone, synced with GitHub: tasks, graders, docs, published results
├── runs/              not git: one folder per attempt; the only place an AI ever sees
├── keys/              not git: each attempt's answer key, moved out right after building
└── evidence/          not git: frozen submissions, owner reports, logs, grades
```

Rules:

1. **The AI only sees `runs/<run>/workspace`.** Its sandbox denies the repository, `keys/`, `evidence/`, other runs, prior sessions and memories. The repository holds the answers: the fixed shop, the planted problems and the grader.
2. **Nothing under `runs/`, `keys/` or `evidence/` goes into git**, and none of them lives inside the repository.
3. **Every run comes from a clean, pulled commit.** `tools/new_run.py` refuses to build with uncommitted changes and records the commit in `evidence/<run>/run.json`.
4. **Publishing is a deliberate copy.** After grading, copy the write-up and the evidence you want public into `results/` in the repository, then commit and push.

Start a run:

```sh
cd ~/MainStreetBench/mainstreetbench && git pull
python3 tools/new_run.py --model sol
```

It prints the working folder and prompt to give the AI, the folders to deny, and the grading commands.

## Open source and contamination

Everything in this repository is public on purpose, so anyone can check how problems are planted and graded. The cost is that a future model, or an agent with web access, could have seen the answers. To limit that:

- **Run agents without web access**, as all recorded runs do.
- **Note the date.** Report each model's release date next to its score, and treat models released after this benchmark went public with caution.
- **Hold back a private variant.** Before publishing a headline comparison, consider running it on one: the same kinds of problems with different records, numbers and wording. Publish that variant after the comparison.

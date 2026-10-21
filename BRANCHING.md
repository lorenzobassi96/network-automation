# Course branches

The repository keeps shared material separate from year-specific course editions:

- `main` is the shared baseline for tooling and material that is not tied to an edition.
- `course/2026` contains the material and changes for the 2026 course.

Students should clone the edition they are attending:

```bash
git clone --branch course/2026 https://github.com/lorenzobassi96/network-automation.git
```

Keep changes that only apply to the 2026 course on `course/2026`. Make reusable fixes on `main`, then cherry-pick those commits into `course/2026` when the edition needs them. Do not merge the entire course branch back into `main`.

Use tags such as `course-2026-v1` to identify a stable course release. Create a branch for a future edition only when that edition is ready to be prepared; no 2027 branch is created yet.

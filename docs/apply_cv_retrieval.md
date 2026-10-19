# Apply and validate CV ingestion and retrieval

## 1. Apply the update

Extract the downloaded package to a separate folder. Do not replace your entire
project folder. The installer updates only listed files and removes the two
renamed legacy files. It leaves `.git`, `.env`, virtual environments and private
CVs alone. It checks the uploaded baseline before writing and backs up changed
files under `.update-backups/`. Line-ending differences are ignored during checks.

From PowerShell, after extracting beside the ZIP in Downloads:

```powershell
Set-Location "$env:USERPROFILE\Downloads\CareerMatch_CV_Retrieval_Update"
python .\apply_update.py --target "D:\Projects\Job_Match_Agent"
python .\apply_update.py --target "D:\Projects\Job_Match_Agent" --apply
Set-Location "D:\Projects\Job_Match_Agent"
```

The first command checks without changing files. Run the apply command only if
it reports no conflicts. A conflict means a local file differs from both the
uploaded snapshot and the update; compare it with `payload/<same path>` and
merge deliberately. Do not force overwrite. Reapplying an already applied
package is safe. Keep the printed backup path; its `backup.json` lists the
originally present and absent files. On an ordinary write failure, the installer
attempts automatic rollback. Keep a full local backup for interruption or disk
failure recovery.

## 2. Install and run offline checks

Activate the existing environment or invoke its Python directly:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements-retrieval.txt
python -m pytest
python -m scripts.evaluate_cv_retrieval
```

If PowerShell blocks activation, use `.\venv\Scripts\python.exe` instead of
`python` for each command; changing execution policy is unnecessary. If there
is no environment, create one with `py -3.12 -m venv venv` first.

Expected: 36 passed and one skipped integration test, subject to installed
package versions. The default offline benchmark should find 19/20 at top-3.
No API key or Docker service is needed for these checks. Requirements preserve
the extraction package pins from your uploaded project. If a pin cannot be
installed, keep the error output rather than silently changing package versions.

## 3. Configure local PostgreSQL

Preserve your existing `.env` and OpenAI settings. Add these settings, choosing
your own local password and using the same value in both places. Use letters,
numbers and underscores to avoid URL-escaping issues during initial setup.

```dotenv
POSTGRES_PASSWORD=replace_with_local_password
DATABASE_URL=postgresql://careermatch:replace_with_local_password@localhost:5432/careermatch
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

Install/start Docker Desktop, then run:

```powershell
docker compose up -d --wait
python -m scripts.cv init-db
$env:TEST_DATABASE_URL = (Get-Content .env | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -Last 1) -replace '^DATABASE_URL=', ''
python -m pytest tests/integration -q
Remove-Item Env:TEST_DATABASE_URL
```

The integration test creates unique test CV IDs and cleans them up. It checks
real vector search, CV isolation, replacement, rollback and deletion without
paid API calls. A skip here is not a pass: check the DSN and psycopg installation.

Port 5432 must be free. If occupied, change the host side to `5433:5432` in
Compose and the port in DATABASE_URL to 5433. Changing the password in `.env`
after a database volume exists does not change the password inside PostgreSQL.
Do not delete a populated volume just to fix a configuration mismatch.

## 4. Run the full synthetic example

These commands make paid OpenAI calls using the existing API key:

```powershell
python -m scripts.cv ingest data/fixtures/sample_cv.md --cv-id demo
python -m scripts.cv search "What is the German language level?" --cv-id demo
python -m scripts.cv ask "What is the German language level?" --cv-id demo
python -m scripts.evaluate_cv_retrieval --live
```

The expected source includes `German B1`. The live benchmark ingests the
synthetic CV at four chunk sizes into unique temporary CV IDs, evaluates 20
questions per configuration and deletes those temporary records. It never
replaces your `demo` CV. Inspect `evaluation/results/retrieval_live.json` and
its default-configuration hit rate. A nonzero exit may mean the 80% acceptance
gate failed. Keep the report and investigate misses before claiming completion.

The live retrieval benchmark evaluates retrieval, not answer quality. Also ask
an unsupported question, such as `What salary does the candidate expect?`, and
check that Q&A abstains. Record relevance or abstention failures as evaluation
cases. Local semantic retrieval results and two Q&A smoke checks are recorded in
`benchmarks/retrieval_baseline.md`. Broader Q&A evaluation remains pending.

For a personal CV, place a text PDF or Markdown copy in `data/private/` and use a
new CV ID. Ingest sends its chunks to OpenAI. Reusing a CV ID replaces its content.

```powershell
python -m scripts.cv ingest data/private/my_cv.pdf --cv-id my-cv
python -m scripts.cv search "Experience with machine learning" --cv-id my-cv
python -m scripts.cv delete --cv-id my-cv
```

## 5. Review and commit

Create the feature branch after applying the package, then inspect all changes:

```powershell
git switch -c feat/cv-semantic-retrieval
git status --short
git diff --stat
git add .gitignore .env.example README.md requirements.txt requirements-retrieval.txt pytest.ini compose.yaml src scripts tests data/fixtures evaluation/results docs benchmarks
```

If the extraction foundation was never committed, that explicit staging command
includes it. `Roadmap/` stays ignored as in the original project. Historical
ignored patch files can remain locally but are excluded from the new delivery.
Check the staged set and do not stage secrets, personal CVs or virtual environments:

```powershell
git diff --cached --stat
git diff --cached | Select-String -Pattern "sk-"
git status --short
```

After the checks pass and the staged changes are reviewed:

```powershell
git commit -m "feat: add CV ingestion and semantic retrieval"
git push -u origin feat/cv-semantic-retrieval
```

Do not create a release tag until the PostgreSQL test and live retrieval
benchmark pass. No commit, push or remote verification was performed while
preparing this package.

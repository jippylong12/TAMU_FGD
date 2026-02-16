# OpenAI Output -> Frontend Local Test

## 1) Generate and publish `MasterDB.csv`
From `TAMU_FGD/`:

```bash
python3 scripts/generate_masterdb_from_openai.py \
  --eval-output eval_output/dt_fall2023 \
  --output-csv GradeDistributionsDB/MasterDBs/MasterDB.csv \
  --frontend-root ../TAMU_FGD_FRONT_END \
  --verbose
```

Expected frontend file:
- `../TAMU_FGD_FRONT_END/MasterDBs/MasterDB.csv`

## 2) Run frontend (recommended: local PHP)
Install PHP (if missing):

```bash
brew install php
```

Run server:

```bash
cd ../TAMU_FGD_FRONT_END
php -S 127.0.0.1:8080
```

Open:
- `http://127.0.0.1:8080/index.html`

## 3) Alternative without local PHP install (Docker)
From repository root (`tamu_fgd_mono/`):

```bash
docker run --rm -p 8080:80 \
  -v "$PWD/TAMU_FGD_FRONT_END":/var/www/html \
  php:8.2-apache
```

Open:
- `http://127.0.0.1:8080/index.html`

## Notes
- `python -m http.server` can only serve static files and will not execute `results.php`.
- Re-run step 1 whenever you regenerate OpenAI outputs.

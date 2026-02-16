#README

First and foremost, if you have found this to be useful please share the spreadsheets/the link to this repository around. I hope it does help any one who uses it. 

##### PROJECT #############################

This project is done in three parts. I have finished all three parts enough to get them to work. 

1) Download all the usable pdfs and store them in folders

2) Use OCR applications to get text from pdfs

3) Manipulate data to present in a workable format.

Something to work on in the future, besides eliminating bugs, are:

* Go back 3 or 5 years and create a master file for each college that holds all of that data

* Eliminate some of the manual work and make it all autonomous. 

Side note before the how-to: This project took me around 6 hours to complete. This could easily be the back-end to a server that a front end application can pull it's data from. I don't say that to gloat. I say that for how ridiculously easy this can be for one person let alone a whole team of people. This program is not perfect and it still needs lots of hours to get perfect but it get's the job done and I don't even have direct access to the data like I'm sure that other website does. Just a thought. 

HOW-TO:

(The Hey This Is Pretty Cool And I Want To Help Expand On This Person)

First off, great. 

Second off, once you downloaded it I apologize for my poor commenting. Some things to know are:

* Forget all that stuff about a lot of manual work! This latest version only requires you to have a google account with drive and that's it! It should work all the way through. All you need is the year and it will do it's thing. There are some bugs with selenium when it only only downloads .part files of the pdfs and I don't know why it happens because it only happens sometimes. Other than that it should run smoothly. 

* I tried to make this as universal as possible but then I realized that most people who would want to help me are probably using Linux because it's "So much better man you don't understand" and to that I say you're entitled to 
your own opinion, but I made this on Windows so you will have to probably change the file paths format to UNIX. Same for the Mac folk. 

* The comments although poor in quality should help you out enough.

Hope it helps. <3
## Source drift notes (college code aliases)

TAMU has intermittently renamed college report codes in newer terms. The regex pipeline keeps historical codes and applies downloader alias fallbacks for known transitions:

* `AC` -> `AR`
* `DT` -> `DN`
* `DT_PROF` -> `DN_PROF`
* `EH` -> `ED`
* `MN` -> `MD`
* `PM_PROF` -> `CP_PROF`
* `VT` -> `VM`
* `VT_PROF` -> `VM_PROF`

If additional aliases appear, update `TAMU_FGD/src/tamu_fgd/tools/download_pdfs_http.py` under `CODE_ALIASES` before the next refresh run.

## Data refresh runbook

### 1) Rerun the full dataset (2012 → 2025) from existing PDFs

This does **not** download new PDFs again. It reparses available PDFs under `GradeDistributionsDB/<Semester><Year>` and rebuilds the merged `MasterDB.csv`.

```bash
cd /Users/marcus.salinas/Programming/Personal/tamu_fgd_mono/TAMU_FGD
bash scripts/run_regex_year_range_to_masterdb.sh \
  --start-year 2012 \
  --end-year 2025 \
  --semesters spring,summer,fall \
  --output-root eval_output/all_terms_regex \
  --output-csv GradeDistributionsDB/MasterDBs/MasterDB.csv \
  --frontend-root ../TAMU_FGD_FRONT_END \
  --jobs 16 \
  --force-all
```

Tips:
- `--force-all` regenerates `regex.json` for each term even if it already exists.
- Use `--strict` to stop on first term failure.
- This step is for re-running extraction + merged output after PDF files are already on disk.

### 2) Download new PDFs (fresh pulls from TAMU)

Use semester/year commands to fetch PDFs and then parse that semester:

```bash
cd /Users/marcus.salinas/Programming/Personal/tamu_fgd_mono/TAMU_FGD
bash scripts/run_regex_semester_to_csv.sh --semester spring --year 2025 --download-insecure
bash scripts/run_regex_semester_to_csv.sh --semester summer --year 2025 --download-insecure
bash scripts/run_regex_semester_to_csv.sh --semester fall --year 2025 --download-insecure
```

To pull older/newer year ranges, extend the loop:

```bash
cd /Users/marcus.salinas/Programming/Personal/tamu_fgd_mono/TAMU_FGD
for year in 2024 2025; do
  bash scripts/run_regex_semester_to_csv.sh --semester spring --year "$year" --download-insecure
  bash scripts/run_regex_semester_to_csv.sh --semester summer --year "$year" --download-insecure
  bash scripts/run_regex_semester_to_csv.sh --semester fall --year "$year" --download-insecure
done
```

### 3) Generate `MasterDB.csv` only from existing `regex.json` files

If your PDFs were already downloaded and `regex.json` files already exist, run:

```bash
cd /Users/marcus.salinas/Programming/Personal/tamu_fgd_mono/TAMU_FGD
bash scripts/generate_masterdb_from_eval_root.sh \
  eval_output/all_terms_regex \
  GradeDistributionsDB/MasterDBs/MasterDB.csv \
  ../TAMU_FGD_FRONT_END \
  regex.json
```

This rebuilds:
- `MasterDB.csv`
- `MasterDB.index.json`
- `MasterDB.meta.json`

at the frontend publish root as long as `--frontend-root` is provided.

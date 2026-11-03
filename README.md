# Curricular

Lab practical code for SPPU Computer Engineering (BE). Each folder has its own README with run steps.

| Folder | Subject | Language |
| --- | --- | --- |
| [`LP2/`](LP2/README.md) | Artificial Intelligence: search, greedy, CSP, chatbot, expert systems | Python |
| [`cpp/`](cpp/) | LP2 programs in C++ | C++ |
| [`LP4/STQA/`](LP4/STQA/README.md) | Software Testing and Quality Assurance | Python, PHP, JS |
| [`LP4/CSDF/`](LP4/CSDF/README.md) | Cyber Security and Digital Forensics | Python |
| [`LP4/Multimedia/`](LP4/Multimedia/README.md) | Multimedia | Python, HTML/CSS/JS |
| `LinearSearch.apxc` | Linear search | Apex |

## Quick Start

```bash
pip install -r LP4/STQA/requirements.txt -r LP4/CSDF/requirements.txt
python LP4/STQA/run_all.py      # run every STQA test suite
python LP4/CSDF/run_all.py      # run every CSDF demo + self-check
```

Or with Docker:

```bash
docker build -t csdf LP4/CSDF && docker run --rm csdf
cd LP4/STQA && docker compose up -d covid-web tasktrack && docker compose run --rm tests
```

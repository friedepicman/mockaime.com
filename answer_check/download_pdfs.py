"""Step A: download the official contest PDFs into answer_check/pdfs/.

HMMT, PUMaC, SMT, BMT and CMIMC are crawled from their archive pages (crawl_pdfs.py);
Purple Comet uses purple_comet_scraper.py. Files already downloaded are skipped, so it
is safe to stop and rerun.

    python answer_check/download_pdfs.py                  # everything
    python answer_check/download_pdfs.py hmmt purple_comet
    python answer_check/download_pdfs.py cmimc --list     # show what the CMIMC crawler finds

The crawler has Claude name each PDF, so it needs ANTHROPIC_API_KEY. Add --list to see
the links it finds without downloading or calling Claude.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDF_DIR = HERE / "pdfs"
SCRAPERS = {
    # crawl_pdfs.py reads each contest's archive pages, collects the PDF links, and has
    # Claude name each file. --follow limits which pages it opens.
    "hmmt": ["crawl_pdfs.py", "--contest", "HMMT", "--start", "https://www.hmmt.org/www/archive/problems",
             "--follow", "/www/archive/"],
    "pumac": ["crawl_pdfs.py", "--contest", "PUMaC", "--start", "https://jason-shi-f9dm.squarespace.com/archives",
              "--depth", "0"],
    "smt": ["crawl_pdfs.py", "--contest", "SMT", "--start", "https://www.stanfordmathtournament.org/past-tests/problems",
            "--follow", "/past-tests/SMT/"],
    "bmt": ["crawl_pdfs.py", "--contest", "BMT", "--start", "https://berkeley.mt/archives/",
            "--follow", "/archives/bmt-", "--delay", "3"],
    "cmimc": ["crawl_pdfs.py", "--contest", "CMIMC", "--start", "https://cmimc.com/archive", "--depth", "0"],
    # Purple Comet's problem PDFs aren't plain links on its pages, and its official
    # answers are HTML tables, so it keeps its own scraper.
    "purple_comet": ["purple_comet_scraper.py"],
}


def main():
    args = sys.argv[1:]
    names = [a for a in args if not a.startswith("-")] or list(SCRAPERS)
    extra = [a for a in args if a.startswith("-")]
    PDF_DIR.mkdir(exist_ok=True)
    for name in names:
        if name not in SCRAPERS:
            print(f"unknown contest {name!r}; choose from {', '.join(SCRAPERS)}")
            continue
        cmd = [sys.executable, str(HERE / "scrapers" / SCRAPERS[name][0]), *SCRAPERS[name][1:], *extra]
        print(f"\n===== {name} =====")
        try:
            subprocess.run(cmd, cwd=PDF_DIR, check=False)
        except KeyboardInterrupt:
            print("\nStopped. Rerun to continue; finished files are kept.")
            return
    pdfs = list(PDF_DIR.rglob("*.pdf"))
    print(f"\n{len(pdfs)} PDFs in {PDF_DIR}")


if __name__ == "__main__":
    main()

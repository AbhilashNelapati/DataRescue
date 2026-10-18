# Publish DataRescue on GitHub Pages (mobile-friendly)

This folder contains a static, browser-based version of DataRescue. GitHub Pages does not execute Python/Streamlit, so this version uses HTML, CSS and JavaScript. It can load a built-in sample or a user's CSV, demonstrate failure injection and repairs, show a preview, and download a CSV/JSON/Markdown report. Files are processed locally in the browser.

## Publish into the existing repository

Repository: `https://github.com/AbhilashNelapati/DataRescue`

1. Download and extract `DataRescue_GitHubPages.zip` on your phone.
2. Open the repository in Chrome and go to the **Code** tab.
3. Tap **Add file → Upload files**.
4. Upload these three files from this folder to the **repository root**: `index.html`, `style.css`, and `app.js`.
5. Commit the changes to `main`.
6. In the repository, open **Settings → Pages**.
7. Under **Build and deployment**, choose **Deploy from a branch**.
8. Select branch **main** and folder **/(root)**, then tap **Save**.
9. Wait a few minutes, then open `https://abhilashnelapati.github.io/DataRescue/`.

If Settings → Pages already uses a different source, select `main` and `/(root)`. Keep your original Python files; they remain useful as the Python prototype, but GitHub Pages will serve the `index.html` browser edition.

## Test the website

1. Open the site and tap **Load sample dataset**.
2. Select **Duplicate records** and tap **Apply failure scenario**.
3. Tick **Remove exact duplicates** and tap **Run diagnosis & repair**.
4. Review the issue list and preview; download the CSV or audit report.
5. Also test CSV upload and reset.

## Scope note

This is not the Python/Streamlit backend running on GitHub Pages. It is a static demo edition that uses deterministic, client-side rules. It does not yet implement OmniRush agent orchestration. Do not claim agent integration unless you add and test it separately.

$ver = uv run .\helper\version.py
iscc /DMyAppVersion=$ver .\inno-setup.iss

# Work in progress

Developing a way to retrieve good resources.

## Issues
Reddit API wrapper `praw` [1] exhibits the following issue when type checking with `mypy`: `Skipping analyzing "praw": module is installed, but missing library stubs or py.typed marker  [import-untyped]`.
To solve (avoid) this, at the moment we just add `# type: ignore` whenever importing from `praw`.

I had some problems installing Sentence Transformers [2] with `pip`, hence I added a bash script with instructions that worked for me.

[1]: https://praw.readthedocs.io/en/stable/getting_started/quick_start.html
[2]: https://www.sbert.net/
# Comic Sol Studio

Comic Sol Studio is the browser distribution of [Comic Sol](https://github.com/wenn-id/comicsol).
It plans, generates, and QAs a comic project, then exports a private PDF or a portable
archive. It also exposes a [WebMCP tool surface](docs/webmcp-tools.md) so a browser agent
can create and revise a comic through the page.

Studio is a thin FastAPI application around the deterministic Comic Sol engine. It does
not contain the engine. It installs the engine as the `comic-sol` wheel and calls it
through `comic_sol_product.engine`.

## Engine pin

[`ENGINE_COMMIT`](ENGINE_COMMIT) pins the exact `wenn-id/comicsol` commit that Studio is
built and tested against. CI checks out that commit, builds the engine wheel from it,
installs it, and only then builds and tests Studio. To move to a newer engine, update
`ENGINE_COMMIT` (and the `comic-sol==` pin in `pyproject.toml` if the engine version
changed) in its own pull request.

## Local setup

Python 3.11, from the repository root. Use `-macos-` or `-windows-` lock names on those
platforms, and `.venv\Scripts\python.exe` on Windows.

```bash
python -m venv .venv
git clone https://github.com/wenn-id/comicsol.git .engine
git -C .engine checkout "$(cat ENGINE_COMMIT)"
.venv/bin/python -m pip install --require-hashes -r requirements/locks/web-linux-x86_64.txt
.venv/bin/python -m pip install --require-hashes -r .engine/requirements/locks/base-linux-x86_64.txt
(cd .engine && ../.venv/bin/python -m build --no-isolation --wheel -o dist)
.venv/bin/python -m pip install --no-deps .engine/dist/comic_sol-*.whl
.venv/bin/python -m pip install --no-deps -e .
```

Run the single-user loopback Studio:

```bash
.venv/bin/python -m comic_sol_web
```

Run the test suite and quality gates:

```bash
.venv/bin/python -m unittest discover -s tests -p "test_*.py"
.venv/bin/python -m ruff check comic_sol_web tests tools
.venv/bin/python -m mypy comic_sol_web tests
```

## Documentation

- [User guide](docs/index.md)
- [Provider matrix](docs/providers.md)
- [WebMCP tool surface](docs/webmcp-tools.md)
- [Security and privacy](docs/security.md)
- [Deployment](docs/deployment.md)
- [Rollback and recovery](docs/rollback.md)
- [Live evidence collection framework](docs/live-evidence.md)

## History

Studio was developed inside `wenn-id/comicsol` under `web/` and split into this
repository with its history preserved. Issues and pull requests before the split
(for example #251, #268, #321) live in the engine repository.

## License

MIT. See [LICENSE](LICENSE).

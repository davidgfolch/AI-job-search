# Contribute

I'm open for open source contributions, if you find a scrapper don't work anymore (maybe because they changed the page DOM structure in source web-page), or have any improvement to the application, please create a pull request.

Please contact me on Github for any comments or questions I'll be happy to answer when available.

## Development guide-lines

Documentation is part of the implementation: a pull request that changes behavior, configuration, commands, Docker services, or APIs must update the matching docs in the same change (module change → `apps/<module>/README.md`, new env var → root `README.md`, compose change → [DOCKER_DEV.md](DOCKER_DEV.md), new host requirement → [README_INSTALL.md](README_INSTALL.md)). The full change → docs map is in `.claude/rules/documentation-update.md`.

## Tests & coverage

See [.github/workflows](../.github/workflows/python-app.yml) for respective apps test & coverage runs.


## Related Documentation

- **Development Guide**: [README_DEVELOPMENT.md](README_DEVELOPMENT.md)
- **Installation Guide**: [README_INSTALL.md](README_INSTALL.md)
- **Docker Development**: [DOCKER_DEV.md](DOCKER_DEV.md)

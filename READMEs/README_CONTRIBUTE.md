# Contribute

I'm open for open source contributions, if you find a scrapper don't work anymore (maybe because they changed the page DOM structure in source web-page), or have any improvement to the application, please create a pull request.

Please contact me on Github for any comments or questions I'll be happy to answer when available.

## Development guide-lines

## Tests & coverage

```bash
# run tests
python -m pytest 
# run coverage
coverage run --source=src -m pytest 
coverage report -m
# see coverage
coverage html
```

All in one:

```bash
pytest && coverage run --source=src -m pytest && coverage report -m
```

## Generate coverage badge for README.md

```bash
cd backend
coverage-badge -o ../README.md_images/img/coverage.svg -f
```

NOTE: pipeline generation don't work

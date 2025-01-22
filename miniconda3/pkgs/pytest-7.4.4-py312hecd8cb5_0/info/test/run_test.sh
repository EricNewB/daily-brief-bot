

set -ex



pytest -h
pip check
pytest testing -v --markers --fixtures --ignore=testing/example_scripts
exit 0

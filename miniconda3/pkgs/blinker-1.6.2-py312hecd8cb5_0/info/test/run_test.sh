

set -ex



pip check
pytest --pyargs tests -vv
exit 0

echo "ruff"
ruff format --line-length=110 *.py
ruff check --fix --line-length=110 *.py

echo "pylint"
pylint --max-line-length=120 *.py

echo "mypy"
mypy *.py

# report any lint overrides
echo "------------------------"
echo " "
echo "Check linting overrides ..."
grep "# type" *.py
grep -E "# mypy:.*disable" *.py
grep "# pylint" *.py
grep "cast(" *.py

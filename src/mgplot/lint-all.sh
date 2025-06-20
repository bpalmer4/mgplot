echo "ruff"
ruff format --line-length=110 *.py
ruff check --select E,F,W,I,UP,C4,ISC,ICN,RET,SIM,TID,TC,PTH,TD,NPY,A,BLE,COM,FBT,N,DTZ,B,G,YTT,S --fix --line-length=110 *.py

## ruff - TRY

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


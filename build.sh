rm -rf python-lib
pip wheel . -w dist
mkdir -p python-lib/python
WHEEL_FILE=$(find dist -name 'python_liquid*.whl' -print -quit)
pip install "$WHEEL_FILE" -t python-lib/python
cd python-lib
zip -r python-liquid-layer.zip .
cd ..
pip uninstall python-liquid -y
pip install $WHEEL_FILE
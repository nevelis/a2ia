import sys, os
# Ensure the a2ia package (the inner one) is importable when running pytest from the submodule root.
PACKAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PACKAGE_ROOT)
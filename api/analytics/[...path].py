import sys, os

# includeFiles are placed alongside this file in the Lambda bundle root
bundle = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, bundle)
sys.path.insert(0, os.path.join(bundle, "services", "analytics-service"))

from src.main import handler

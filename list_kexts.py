import plistlib
import sys

with open(sys.argv[1], 'rb') as f:
    config = plistlib.load(f)

for kext in config['Kernel']['Add']:
    print(f"{kext['BundlePath'].ljust(45)} - {kext['Enabled']}")
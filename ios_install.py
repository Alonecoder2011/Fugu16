#!/usr/bin/env python3

import subprocess
import os


print("Welcome to the Fugu16 iOS installer.")
print("This script will build and install Fugu16 on your device.")
print("Before continuing, please read the requirements:")
print("    - You need a supported device running a supported iOS version (see README.md)")
print("    - The device must be connected via USB")
print("    - You need the IPSW for your device, *unzipped*")
print("    - You need to have Xcode installed")
print("    - You need to have iproxy and ideviceinstaller installed (brew install usbmuxd ideviceinstaller)")

print("You will now be asked a few questions")

build_jailbreakd = False

if build_jailbreakd:
    csIdentity = getAnswer("What is the name of your iOS Signing Certificate? [Apple Dev] ")
    if csIdentity == "":
        csIdentity = "Apple Dev"

    print("Patching arm/iOS/jailbreakd/build.sh...")
    with open("arm/iOS/jailbreakd/build.sh", "r") as f:
        build_sh = f.read()
    
    lines = []
    for line in build_sh.split("\n"):
        if line.startswith("CODESIGN_IDENTITY="):
            lines.append(f'CODESIGN_IDENTITY="{csIdentity}"')
        else:
            lines.append(line)

    with open("arm/iOS/jailbreakd/build.sh", "w") as f:
        f.write("\n".join(lines))

    print("Patched")

    print("Compiling jailbreakd...")

    try:
        subprocess.run(["/bin/bash", "build.sh"], check=True, cwd="arm/iOS/jailbreakd/")
    except subprocess.CalledProcessError as e:
        print(f"Failed to build jailbreakd! Exit status: {e.returncode}")
        exit(-1)

    print("Successfully built jailbreakd")

print("Getting CDHash of jailbreakd...")
try:
    out = subprocess.run(["/usr/bin/codesign", "-dvvv", "arm/iOS/Fugu16App/Fugu16App/jailbreakd"], capture_output=True, check=True)
except subprocess.CalledProcessError as e:
    print(f"Failed to get CDHash of jailbreakd! Codesign exit status: {e.returncode}")
    print("stdout:")
    print(e.stdout)
    print("stderr:")
    print(e.stderr)
    exit(-1)

cdhash = None
out = out.stderr.decode("utf8")
for line in out.split("\n"):
    if line.startswith("CDHash="):
        cdhash = line[7:]
        break
        
if cdhash is None:
    print("Error: Codesign did not output the CDHash for jailbreakd!")
    exit(-1)

print(f"CDHash of jailbreakd: {cdhash}")

print("Patching arm/iOS/Fugu16App/Fugu16App/closures.swift...")

with open("arm/iOS/Fugu16App/Fugu16App/closures.swift", "r") as f:
    closure_swift = f.read()

lines = []
for line in closure_swift.split("\n"):
    if line.startswith('        try simpleSetenv("JAILBREAKD_CDHASH", '):
        lines.append (f'        try simpleSetenv("JAILBREAKD_CDHASH", "{cdhash}")')
    else:
        lines.append(line)

with open("arm/iOS/Fugu16App/Fugu16App/closures.swift", "w") as f:
    f.write("\n".join(lines))

print("Patched")

print("Compiling Fugu16App")

try:
    subprocess.run(["xcodebuild", "-scheme", "Fugu16App", "-derivedDataPath", "build"], check=True, cwd="arm/iOS/Fugu16App/")
except subprocess.CalledProcessError as e:
    print(f"Failed to build Fugu16App! Exit status: {e.returncode}")
    print("If the build failed due to a codesign error, open arm/iOS/Fugu16App/Fugu16App.xcodeproj in Xcode")
    print("    and edit the Signing options in the Signing & Capabilities section.")
    exit(-1)

print("Successfully built Fugu16App")

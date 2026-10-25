[app]

# (str) Title of the application
title = SANX Player

# (str) Package name
package.name = sanxplayer

# (str) Package domain (needed for Android)
package.domain = org.sanx

# (str) Source code directory
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,ttf

# (str) Application version
version = 1.0

# (str) Application version code (Android)
version.code = 1

# (str) Author
author = SANX Player

# (list) Requirements (python3, kivy, ffpyplayer for video)
requirements = python3,kivy,ffpyplayer

# (str) Supported orientation
orientation = portrait

# (list) Android permissions (works on low & high API)
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK,FOREGROUND_SERVICE

# (int) Minimum Android API level (low API support - Android 5.0+)
android.minapi = 21

# (int) Target Android API level (high API support - Android 13+)
android.targetapi = 33

# (bool) Enable multi-touch on Android
android.multitouch = true

# (bool) Keep screen on while playing video
android.wakelock = true

# (list) Java classes to add
# android.add_jars =

# (str) Android NDK version (buildozer downloads automatically if not set)
# android.ndk = 21.4.7075529

# (str) Android SDK version
# android.sdk = 21

# (str) Python entry point (main file)
android.entrypoint = pl.py

# (list) Patterns to exclude
source.exclude_dirs = tests, bin, .venv, __pycache__, .buildozer

# (str) Log level
log_level = info

# (str) Show auth display
# auth_display =

[buildozer]

# (str) Log level for buildozer itself
log_level = info

# (int) Warn if buildozer version is older than this
warn_on_buildozer_version = 1.0.0

[app:source]
sudo apt update
sudo apt install -y openjdk-17-jdk zip unzip python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake gettext libssl-dev

# (str) Pattern to include/exclude when copying the source
# include_patterns =

[app:android]

# (str) Archive name for the output APK
# archive_name =

# (str) Deprecated - use android.gradle_dependencies
# add_gradle_dependencies =

# (list) Gradle dependencies
# gradle_dependencies =

# (bool) Enable AndroidX support
androidx = true

# (str) Version of the Android build tools to use
# build_tools = 30.0.2

[app:ios]

# (str) Name of the deployment certificate
# codesign.certificate =

# (str) Name of the provisioning profile
# provisioning.profile =

[buildozer:android:arch]

# (list) Architectures to build (armeabi-v7a covers most low/high API phones)
archs = armeabi-v7a, arm64-v8a

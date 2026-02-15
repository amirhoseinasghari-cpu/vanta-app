[app]
title = Vanta NFT
package.name = vanta
package.domain = com.vanta.nft
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0
requirements = python3,kivy==2.2.0,web3==6.11.0,eth-account==0.10.0,requests,pillow,cryptography,urllib3
orientation = portrait
fullscreen = 0
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.arch = arm64-v8a
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1
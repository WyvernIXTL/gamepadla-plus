from glob import glob

signtool = max(glob(r"C:/Program Files (x86)/Windows Kits/10/bin/*/x64/signtool.exe"))

print(signtool.replace("\\", "/"))

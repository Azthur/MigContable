import os
if os.path.exists(".env"):
    with open(".env", "r") as f:
        print(f.read())
else:
    print(".env not found")

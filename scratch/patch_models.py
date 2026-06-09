import os

def patch_models():
    file_path = r"c:\SistemaMigConta\backend\app\models\models.py"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    target = '    estado = Column(String(20), default="PENDIENTE", index=True)  # PENDIENTE, MIGRADO, ERROR\n    created_at = Column(DateTime(timezone=True), server_default=func.now())'
    replacement = '    estado = Column(String(20), default="PENDIENTE", index=True)  # PENDIENTE, MIGRADO, ERROR\n    idcontrol = Column(String(200), nullable=True, index=True)\n    created_at = Column(DateTime(timezone=True), server_default=func.now())'
    
    if target in content:
        content = content.replace(target, replacement)
        print("Patcher found target and replaced it.")
    else:
        # try with \r\n
        target_rn = target.replace("\n", "\r\n")
        replacement_rn = replacement.replace("\n", "\r\n")
        if target_rn in content:
            content = content.replace(target_rn, replacement_rn)
            print("Patcher found target with CRLF and replaced it.")
        else:
            print("Patcher could NOT find target!")
            return

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patcher finished writing to models.py")

if __name__ == "__main__":
    patch_models()

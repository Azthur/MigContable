import sys

filepath = r"c:\SistemaMigConta\backend\app\templates\company_detail.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_block = """                    window._validationErrors = errors;
                    window._validationByTable = byTable;

                    _renderValidationErrors(errors, byTable);"""

fixed_block = """                    window._validationErrors = errors;
                    window._validationByTable = byTable;
                    
                    document.getElementById('cfDiariolPanel').style.display = 'block';
                    const valPanel = document.getElementById('validationResultPanel');
                    if (valPanel) valPanel.style.display = 'block';

                    _renderValidationErrors(errors, byTable, 'validationResultPanel');"""

if target_block in content:
    content = content.replace(target_block, fixed_block)
    print("Replaced Frontend successfully!")
else:
    # Try with single spacing or variance
    print("Frontend Block not found!")
    sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

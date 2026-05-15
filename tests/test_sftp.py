import os
import sys
from ftplib import FTP

NEEDED_FILES = {
    "AllProducts.csv", "ApplicationArea.csv", "ApplicationComment.csv",
    "Code.csv", "IndicationCulture.csv", "IndicationCultureForm.csv",
    "IndicationMeasure.csv", "IndicationObligation.csv", "IndicationPest.csv",
    "IndicationTimeMeasure.csv", "ProductCodeR.csv", "ProductCodeS.csv",
    "ProductDangerSymbol.csv", "ProductFormulationCode.csv", "ProductIngredient.csv",
    "ProductPermissionHolder.csv", "ProductProductCategory.csv",
    "ProductSignalWords.csv", "PsmvPermissionholder.csv",
}

try:
    with FTP(os.environ["SFTP_HOST"]) as ftp:
        ftp.login(user=os.environ["SFTP_USERNAME"], passwd=os.environ["SFTP_PASSWORD"])
        ftp.cwd("PSM_Verzeichnis")
        remote_files = set(ftp.nlst())

    found = NEEDED_FILES & remote_files
    missing = NEEDED_FILES - remote_files

    for filename in sorted(found):
        print(f"OK: {filename}")

    if missing:
        for filename in sorted(missing):
            print(f"MISSING: {filename}", file=sys.stderr)
        sys.exit(1)

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)

import os
from ftplib import FTP
from pathlib import Path

NEEDED_FILES = {
    "AllProducts.csv", "ApplicationArea.csv", "ApplicationComment.csv",
    "Code.csv", "IndicationCulture.csv", "IndicationCultureForm.csv",
    "IndicationMeasure.csv", "IndicationObligation.csv", "IndicationPest.csv",
    "IndicationTimeMeasure.csv", "ProductCodeR.csv", "ProductCodeS.csv",
    "ProductDangerSymbol.csv", "ProductFormulationCode.csv", "ProductIngredient.csv",
    "ProductPermissionHolder.csv", "ProductProductCategory.csv",
    "ProductSignalWords.csv", "PsmvPermissionholder.csv", "ProductIndication.csv"
}

DEST = Path("data/raw")
DEST.mkdir(parents=True, exist_ok=True)

with FTP(os.environ["SFTP_HOST"]) as ftp:
    ftp.login(user=os.environ["SFTP_USERNAME"], passwd=os.environ["SFTP_PASSWORD"])
    ftp.cwd("PSM_Verzeichnis")
    for filename in NEEDED_FILES & set(ftp.nlst()):
        with open(DEST / filename, "wb") as f:
            ftp.retrbinary(f"RETR {filename}", f.write)
        print(f"Downloaded: {filename}")

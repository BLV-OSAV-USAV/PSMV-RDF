import os
import gzip
import shutil
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
        raw_path = DEST / filename
        gz_path = DEST / (filename + ".gz")

        with open(raw_path, "wb") as f:
            ftp.retrbinary(f"RETR {filename}", f.write)

        with open(raw_path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

        raw_path.unlink()  # remove uncompressed file
        print(f"Downloaded and compressed: {gz_path}")

import os
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

with FTP(os.environ["SFTP_HOST"]) as ftp:
    ftp.login(user=os.environ["SFTP_USERNAME"], passwd=os.environ["SFTP_PASSWORD"])
    print("Root contents:", ftp.nlst())
    ftp.cwd("PSM_Verzeichnis")
    print("Folder contents:", ftp.nlst())

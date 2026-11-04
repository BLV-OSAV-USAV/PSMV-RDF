import os
from ftplib import FTP

import pytest

pytestmark = pytest.mark.network

NEEDED_FILES = {
    "AllProducts.csv", "ApplicationArea.csv", "ApplicationComment.csv",
    "Code.csv", "IndicationCulture.csv", "IndicationCultureForm.csv",
    "IndicationMeasure.csv", "IndicationObligation.csv", "IndicationPest.csv",
    "IndicationTimeMeasure.csv", "ProductCodeR.csv", "ProductCodeS.csv",
    "ProductDangerSymbol.csv", "ProductFormulationCode.csv", "ProductIngredient.csv",
    "ProductPermissionHolder.csv", "ProductProductCategory.csv",
    "ProductSignalWords.csv", "PsmvPermissionholder.csv", "ProductIndication.csv",
}


@pytest.fixture(scope="module")
def remote_files():
    """Connect once, log in, return the file names in PSM_Verzeichnis."""
    with FTP(os.environ["SFTP_HOST"], timeout=30) as ftp:
        ftp.login(user=os.environ["SFTP_USERNAME"], passwd=os.environ["SFTP_PASSWORD"])
        ftp.cwd("PSM_Verzeichnis")
        return set(ftp.nlst())


def test_directory_is_not_empty(remote_files):
    assert remote_files, "PSM_Verzeichnis is empty"


def test_all_needed_files_present(remote_files):
    missing = NEEDED_FILES - remote_files
    assert not missing, f"missing on server: {sorted(missing)}"
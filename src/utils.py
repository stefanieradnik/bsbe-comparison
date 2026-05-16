import zipfile


def extract_xml_from_zip(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        xml_name = next(n for n in zf.namelist() if n.lower().endswith(".xml"))
        xml_bytes = zf.read(xml_name)

    return xml_bytes

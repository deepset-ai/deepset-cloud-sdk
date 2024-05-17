# Can use this file to test e2e uploads manually
import httpx

from deepset_cloud_sdk.workflows.sync_client.files import (
    DeepsetCloudFileBytes,
    WriteMode,
    upload,
    upload_bytes,
)

api_key = "api key goes here"

menu = httpx.get("https://www.beefeater.co.uk/en-gb/main-menu/beefeater_main_menu_band3.pdf")
md = httpx.get("https://raw.githubusercontent.com/facebook/react/main/SECURITY.md")
html = httpx.get("https://github.com/facebook/react")
jsn = httpx.get("https://raw.githubusercontent.com/minimaxir/big-list-of-naughty-strings/master/blns.json")
docx = httpx.get("https://www.lehman.edu/faculty/john/classroomrespolicy1.docx")
pptx = httpx.get("https://scholar.harvard.edu/files/torman_personal/files/samplepptx.pptx")
xlsx = httpx.get(
    "http://gwagner.med.harvard.edu/intranet/PNAS_Manuscript_2014/File%20S1-Mass%20spectrometry%20data.xlsx"
)
xml = httpx.get("http://niem.github.io/community/biometrics/sample-xml/NIEM5.1_DNA_Crime_Scene_Mixture.xml")

[".csv", ".docx", ".html", ".json", ".md", ".txt", ".pdf", ".pptx", ".xlsx", ".xml"]

files = [
    DeepsetCloudFileBytes(file_bytes=menu.content, name="1.pdf", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"a,b,c\n1,2,3", name="1.csv", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"hello", name="1.txt", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=md.content, name="1.md", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=html.content, name="1.html", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=jsn.content, name="1.json", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=docx.content, name="1.docx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=pptx.content, name="1.pptx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xlsx.content, name="1.xlsx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xml.content, name="1.xml", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=menu.content, name="2.pdf", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"a,b,c\n1,2,3", name="2.csv", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"hello", name="2.txt", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=md.content, name="2.md", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=html.content, name="2.html", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=jsn.content, name="2.json", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=docx.content, name="2.docx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=pptx.content, name="2.pptx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xlsx.content, name="2.xlsx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xml.content, name="2.xml", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=menu.content, name="3.pdf", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"a,b,c\n1,2,3", name="3.csv", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"hello", name="3.txt", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=md.content, name="3.md", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=html.content, name="3.html", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=jsn.content, name="3.json", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=docx.content, name="3.docx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=pptx.content, name="3.pptx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xlsx.content, name="3.xlsx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xml.content, name="3.xml", meta={"thing": "menu"}),
]

summary = upload_bytes(
    workspace_name="default",  # optional, by default the environment variable "DEFAULT_WORKSPACE_NAME" is used
    files=files,
    # by default blocking=True - by setting to False it will mean that you can immediately
    # continue uploading another batch of files
    # You can still validate they are uploaded via the get_upload_session function in the SDK if required, but it may take a
    # few minutes.
    blocking=False,
    timeout_s=300,  # optional, by default 300
    show_progress=True,  # optional, by default True
    api_url="https://api.dev.cloud.dpst.dev/api/v1",
    api_key=api_key,
    write_mode=WriteMode.KEEP,
)

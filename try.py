import httpx

from deepset_cloud_sdk.workflows.sync_client.files import (
    DeepsetCloudFileBytes,
    WriteMode,
    upload,
    upload_bytes,
)

api_key = "api_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwYjYwYzE2YS00NjJlLTRkNmMtYjg2ZS1mYTI3M2RhNGU2Nzh8NjI5NzY4NWVmMzdiNTIwMDY4NDU3ODMxIiwiZXhwIjoxNzE2NTA1MjAwLCJhdWQiOlsiaHR0cHM6Ly9hcGkuZGV2LmNsb3VkLmRwc3QuZGV2Il19.MjfWK8JtrkVpSLwb-wJ06vxkw2sQM3sB6Okd47PX3Cw"

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
    DeepsetCloudFileBytes(file_bytes=menu.content, name="menu.pdf", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"a,b,c\n1,2,3", name="1.csv", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"hello", name="1.txt", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=md.content, name="1.md", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=html.content, name="1.html", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=jsn.content, name="1.json", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=docx.content, name="1.docx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=pptx.content, name="1.pptx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xlsx.content, name="1.xlsx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xml.content, name="1.xml", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=menu.content, name="menu1.pdf", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"a,b,c\n1,2,3", name="11.csv", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"hello", name="11.txt", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=md.content, name="11.md", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=html.content, name="11.html", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=jsn.content, name="11.json", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=docx.content, name="11.docx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=pptx.content, name="11.pptx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xlsx.content, name="11.xlsx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xml.content, name="11.xml", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=menu.content, name="menu11.pdf", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"a,b,c\n1,2,3", name="111.csv", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=b"hello", name="111.txt", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=md.content, name="111.md", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=html.content, name="111.html", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=jsn.content, name="111.json", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=docx.content, name="111.docx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=pptx.content, name="111.pptx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xlsx.content, name="111.xlsx", meta={"thing": "menu"}),
    DeepsetCloudFileBytes(file_bytes=xml.content, name="111.xml", meta={"thing": "menu"}),
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

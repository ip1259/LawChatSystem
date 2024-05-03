import requests, zipfile, io


r = requests.get("https://law.moj.gov.tw/api/Ch/Law/JSON")

print(zipfile.ZipFile(io.BytesIO(r.content)).infolist())


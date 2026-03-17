if re.search(r"\b(principal|staff|architect|lead|senior|sr\.?)\b", text, re.I):
    score += 20
elif re.search(r"\b(manager|director)\b", text, re.I):
    score += 10
else:
    score += 0

if re.search(r"\b(remote|work\s*from\s*home)\b", text, re.I):
    score += 20
elif re.search(r"\b(hybrid|onsite|on-site|in office)\b", text, re.I):
    score -= 50   # auto‑reject territory

if re.search(r"\b(\$165|170|180|190|200|220|240|250)k\b", text, re.I):
    score += 15
elif re.search(r"\bsalary\b", text, re.I):
    score += 5
elif re.search(r"\b(competitive pay|DOE|market rate)\b", text, re.I):
    score -= 10

modern = r"\b(fabric|onelake|medallion|delta lake|synapse|data factory|pyspark|dataops|ci/cd)\b"
hits = len(re.findall(modern, text, re.I))
score += min(hits * 3, 15)

if re.search(r"\b(architect|platform|ownership|strategy|governance|standards)\b", text, re.I):
    score += 10

if re.search(r"\b(roadmap|mature|enterprise|governance|data team|modernization)\b", text, re.I):
    score += 10
elif re.search(r"\b(greenfield|starting|exploring|learning fabric)\b", text, re.I):
    score -= 10

redflags = r"\b(relocation|relocate|onsite|hybrid|wear many hats|limited resources|solo data engineer)\b"
if re.search(redflags, text, re.I):
    score -= 20
else:
    score += 10

score = max(0, min(score, 100))

import json
from collections import Counter
from app.providers.demo import DemoProvider
rows=[json.loads(line) for line in open("backend/evals/intents.pt-BR.jsonl",encoding="utf-8")]
provider=DemoProvider(); correct=0; matrix=Counter()
for row in rows:
    predicted=provider.classify(row["text"]).value.intent
    correct += predicted == row["intent"]; matrix[(row["intent"],predicted)] += 1
print(json.dumps({"accuracy":correct/len(rows),"cases":len(rows),"confusion":{f"{a}->{b}":n for (a,b),n in matrix.items()}},ensure_ascii=False,indent=2))

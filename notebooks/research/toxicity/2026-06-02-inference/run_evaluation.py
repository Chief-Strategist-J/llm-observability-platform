import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath("../../../../packages/python/toxicity-worker/src"))

from infra.adapters.detoxify_onnx_adapter import DetoxifyOnnxAdapter
from core.domain.types import ToxicityInput
from core.domain.service import score_toxicity

adapter = DetoxifyOnnxAdapter()

lengths = [200, 600, 1200, 2000, 4000]
positions = ["prefix", "middle", "suffix", "clean"]

clean_word = "apple "
toxic_text = "I hate you, you are a stupid idiot."

results = []

for length in lengths:
    for pos in positions:
        if pos == "clean":
            text = clean_word * length
            label = 0
        else:
            label = 1
            toxic_tokens = adapter.tokenize(toxic_text)
            num_toxic = len(toxic_tokens)
            num_clean = max(0, length - num_toxic)
            if pos == "prefix":
                text = toxic_text + " " + (clean_word * num_clean)
            elif pos == "suffix":
                text = (clean_word * num_clean) + " " + toxic_text
            elif pos == "middle":
                half_clean = num_clean // 2
                text = (clean_word * half_clean) + " " + toxic_text + " " + (clean_word * (num_clean - half_clean))
        
        actual_tokens = len(adapter.tokenize(text))
        
        res = score_toxicity(input=ToxicityInput(text=text), scorer=adapter, trace_id=None, span_id=None)
        score = res.scores.toxicity
        
        prediction = 1 if score >= 0.5 else 0
        is_correct = 1 if prediction == label else 0
        
        results.append({
            "TargetLength": length,
            "ActualLength": actual_tokens,
            "Position": pos,
            "Label": label,
            "ToxicityScore": score,
            "Prediction": prediction,
            "IsCorrect": is_correct
        })

df = pd.DataFrame(results)
print(df)

script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, "outputs")
os.makedirs(output_dir, exist_ok=True)

df.to_csv(os.path.join(output_dir, "evaluation_results.csv"), index=False)

plt.figure(figsize=(10, 6))
colors = {"prefix": "forestgreen", "middle": "crimson", "suffix": "darkorange", "clean": "royalblue"}
markers = {"prefix": "o", "middle": "x", "suffix": "^", "clean": "s"}

for pos in positions:
    sub = df[df["Position"] == pos]
    plt.plot(sub["TargetLength"], sub["ToxicityScore"], marker=markers[pos], color=colors[pos], label=pos, linewidth=2)

plt.axvline(x=510, color="gray", linestyle="--")
plt.axvline(x=1020, color="gray", linestyle=":")
plt.title("Detected Toxicity Score vs Document Length")
plt.xlabel("Document Length (tokens)")
plt.ylabel("Toxicity Score")
plt.ylim(-0.05, 1.05)
plt.grid(True)
plt.legend()
plt.savefig(os.path.join(output_dir, "evaluation_scores_by_position.png"), dpi=150, bbox_inches="tight")
plt.close()

plt.figure(figsize=(10, 6))
for pos in positions:
    sub = df[df["Position"] == pos]
    plt.plot(sub["TargetLength"], sub["IsCorrect"], marker=markers[pos], color=colors[pos], label=pos, linewidth=2)

plt.axvline(x=510, color="gray", linestyle="--")
plt.axvline(x=1020, color="gray", linestyle=":")
plt.title("Classification Accuracy vs Document Length")
plt.xlabel("Document Length (tokens)")
plt.ylabel("Accuracy (1 = Correct, 0 = Incorrect)")
plt.ylim(-0.05, 1.05)
plt.grid(True)
plt.legend()
plt.savefig(os.path.join(output_dir, "evaluation_accuracy_by_position.png"), dpi=150, bbox_inches="tight")
plt.close()

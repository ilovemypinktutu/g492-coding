TITLE = "LLMs Inside Your Analysis"
SLUG = "llm_classification"

CELLS = [
("md", """
**Scenario.** Limestone Outfitters has thousands of free-text product reviews. The VP of Customer Experience asks: *"What are customers actually complaining about, and is it getting better?"* Nobody is going to read 50,000 reviews.

Today you'll use an LLM as a **component inside your code**: a classifier you call thousands of times. Then you'll do the part most people skip, which is **measuring how often it's right**.

You have 114 reviews that a human already labeled (`human_topic`, `human_sentiment`). That is your *test set*.
"""),
("code", """
import pandas as pd, json, os
reviews = pd.read_csv(DATA + "reviews.csv")
print(reviews.shape)
reviews.sample(8, random_state=1)[["review_id", "stars", "review_text", "human_topic", "human_sentiment"]]
"""),
("md", """
## Part 1: The labeling guide is the spec (10 min)
An LLM classifier is only as good as its instructions. It's the same lesson as Lab 1. Read the guide below, then **improve it**: add at least two rules for cases you think are ambiguous (sarcasm? two topics in one review? non-English? "ok"?).
"""),
("code", """
GUIDE = \"\"\"You label customer reviews for an outdoor-gear retailer.

topic: the ONE main issue the review is about:
  - Quality: how the product performs or holds up
  - Fit/Sizing: size, length, how it fits the body
  - Shipping: delivery speed, damage in transit, wrong item sent
  - Customer Service: interactions with support, returns/warranty handling
  - Value: price relative to what you get

sentiment: Positive, Negative, or Mixed (clearly both good and bad points).

Rules:
- (add your rules here)
\"\"\"
"""),
("md", """
## Part 2: Run the classifier (15 min)
Choose **one** path.

**Path A: API (if you have an Anthropic API key).** In Colab, click the 🔑 *Secrets* icon on the left, add `ANTHROPIC_API_KEY`, and toggle notebook access on. Never paste a key into a cell. Keys in notebooks end up on GitHub.
Classifying all 114 reviews costs well under $1.

**Path B: no key (chat assistant).** Run the Path-B cell to print the prompt in batches of 20, paste each batch into your chat assistant, and paste its CSV answers back into `pasted_csv`.
"""),
("code", """
# ---------- Path A: API ----------
# %pip install -q anthropic
import anthropic
try:
    from google.colab import userdata
    os.environ["ANTHROPIC_API_KEY"] = userdata.get("ANTHROPIC_API_KEY")
except Exception:
    pass   # not in Colab: the SDK reads ANTHROPIC_API_KEY from your environment

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"
SCHEMA = {
    "type": "object",
    "properties": {
        "reason": {"type": "string", "description": "one short sentence explaining the labels"},
        "topic": {"type": "string", "enum": ["Quality", "Fit/Sizing", "Shipping", "Customer Service", "Value"]},
        "sentiment": {"type": "string", "enum": ["Positive", "Negative", "Mixed"]},
    },
    "required": ["reason", "topic", "sentiment"],
    "additionalProperties": False,
}

def classify(text, guide):
    \"\"\"Label one review. Returns a dict with reason, topic, sentiment (plus token counts for cost).\"\"\"
    resp = client.beta.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=guide,
        messages=[{"role": "user", "content": f"Review:\\n{text}"}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",      # if the model declines, the API retries on a fallback model
    )
    if resp.stop_reason == "refusal":
        return {"reason": "refused", "topic": None, "sentiment": None}
    out = json.loads(next(b.text for b in resp.content if b.type == "text"))
    out["input_tokens"], out["output_tokens"] = resp.usage.input_tokens, resp.usage.output_tokens
    return out

print(classify("Great boots but they took three weeks to arrive.", GUIDE))
"""),
("code", """
# Run on all reviews (about 1-2 minutes)
results = []
for r in reviews.itertuples():
    results.append({"review_id": r.review_id, **classify(r.review_text, GUIDE)})
preds = pd.DataFrame(results)
preds.head()
""", """
# INSTRUCTOR: set MOCK=True to test the evaluation cells without an API key.
MOCK = os.environ.get("MOCK_LLM") == "1"
if MOCK:
    import numpy as np
    rng = np.random.default_rng(0)
    hard = pd.read_csv("../reviews_hard_flags.csv") if os.path.exists("../reviews_hard_flags.csv") else None
    preds = reviews[["review_id"]].copy()
    flip = rng.random(len(reviews)) < 0.15
    topics = ["Quality", "Fit/Sizing", "Shipping", "Customer Service", "Value"]
    preds["topic"] = [rng.choice(topics) if f else t for f, t in zip(flip, reviews.human_topic)]
    preds["sentiment"] = [rng.choice(["Positive", "Negative", "Mixed"]) if f else s
                          for f, s in zip(rng.random(len(reviews)) < 0.12, reviews.human_sentiment)]
    preds["reason"] = "mock"; preds["input_tokens"] = 260; preds["output_tokens"] = 45
else:
    results = [{"review_id": r.review_id, **classify(r.review_text, GUIDE)} for r in reviews.itertuples()]
    preds = pd.DataFrame(results)
preds.head()
"""),
("code", """
# ---------- Path B: no API key ----------
def print_batches(guide, size=20):
    for start in range(0, len(reviews), size):
        batch = reviews.iloc[start:start + size]
        body = "\\n".join(f"{r.review_id}: {r.review_text}" for r in batch.itertuples())
        print(f"===== BATCH {start // size + 1} (copy everything below) =====")
        print(guide + "\\nLabel each review below. Answer ONLY with CSV lines: review_id,topic,sentiment\\n\\n" + body + "\\n")
# print_batches(GUIDE)

pasted_csv = \"\"\"review_id,topic,sentiment
\"\"\"
# preds = pd.read_csv(io.StringIO(pasted_csv))   # uncomment after pasting (and `import io`)
"""),
("md", """
## Part 3: Is it any good? (20 min)
**3a. Accuracy.** What share of topic labels and sentiment labels match the human labels?
"""),
("code", """
ev = reviews.merge(preds, on="review_id", validate="one_to_one")
print("topic accuracy:    ", f"{(ev.topic == ev.human_topic).mean():.1%}")
print("sentiment accuracy:", f"{(ev.sentiment == ev.human_sentiment).mean():.1%}")
"""),
("md", "**3b. Where does it go wrong?** A *confusion matrix* shows which labels get mistaken for which. Rows are the human labels, columns are the model labels."),
("code", """
pd.crosstab(ev.human_topic, ev.topic, margins=True)
"""),
("code", """
pd.crosstab(ev.human_sentiment, ev.sentiment, margins=True)
"""),
("md", """
**3c. Read the disagreements.** For at least 8 disagreements, decide who's right: the model, the human, or "genuinely ambiguous". Human labels are not perfect truth.
"""),
("code", """
disagree = ev[(ev.topic != ev.human_topic) | (ev.sentiment != ev.human_sentiment)]
pd.set_option("display.max_colwidth", 120)
disagree[["review_id", "review_text", "human_topic", "topic", "human_sentiment", "sentiment", "reason"]]
"""),
("code", """
verdicts = {
    # review_id: "model" / "human" / "ambiguous"
}
"""),
("md", """
**3d. Why not just use the star rating?** Compare star ratings with human sentiment. Stars are free and instant. How close do they get? Then answer: **what can stars *not* tell the VP?** (Hint: look at the topic column.) This is the "is the fancy tool worth it?" question you should ask of every AI project.
"""),
("code", """
star_guess = pd.cut(reviews.stars, [0, 2, 3, 5], labels=["Negative", "Mixed", "Positive"]).astype(str)
print("stars-only sentiment accuracy:", f"{(star_guess == reviews.human_sentiment).mean():.1%}")
reviews[star_guess != reviews.human_sentiment][["stars", "review_text", "human_sentiment"]].head(8)
"""),
("md", """
## Part 4: Improve once, and don't fool yourself (10 min)
Edit `GUIDE` based on what you saw in 3c and re-run **Part 2 and 3a**.

⚠️ **The trap:** if you tune the guide until it gets *these 114* right, your accuracy number stops meaning anything. It's like studying with the answer key. In a real project you keep a **held-out** set you never look at while tuning. Write down: how would you set that up for the 50,000 real reviews?

## Part 5: Cost and governance (5 min)
"""),
("code", """
if "input_tokens" in preds:
    tin, tout = preds.input_tokens.mean(), preds.output_tokens.mean()
    price_in, price_out = 4.00, 20.00        # USD per million tokens for claude-opus-5-5 (check current pricing)
    per_review = (tin * price_in + tout * price_out) / 1e6
    print(f"avg tokens in/out: {tin:.0f}/{tout:.0f}  ->  ${per_review:.5f} per review, "
          f"${per_review * 50_000:,.0f} for 50,000 reviews")
"""),
("md", """
**Discuss:** (1) Before sending customer reviews to an outside AI provider, which questions must your company answer? (Think: personal data, contracts, data retention, the order number in review 98.) (2) At what accuracy would you trust this enough to put the numbers in front of the VP, and what would you say about the error rate?

### Submit
Your final `GUIDE`, your accuracy before and after one revision, your `verdicts` for 8 disagreements, and a 3-sentence answer to "should the VP trust this?"
"""),
]

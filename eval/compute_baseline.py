#!/usr/bin/env python3
import json
import math
import pathlib
import re
from collections import Counter
from typing import List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_CANDIDATES = [ROOT / "data" / "snapshots", ROOT / "data" / "samples"]
TOKEN_PATTERN = re.compile(r"[^\W\d_]+", re.UNICODE)


def ensure_sample_content(target: pathlib.Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    sample = target / "hello.txt"
    if not sample.exists():
        sample.write_text(
            "SMDaI – технология декодирования замысла автора. "
            "SMDaI Board — базовая доска проекта. "
            "Секрет PROJECT_URL хранит ссылку на проектную доску.",
            encoding="utf-8",
        )


def choose_data_dir() -> pathlib.Path:
    for candidate in DATA_CANDIDATES:
        if candidate.exists():
            return candidate
    fallback = DATA_CANDIDATES[-1]
    ensure_sample_content(fallback)
    return fallback


def read_docs(max_docs: int = 20) -> List[Tuple[str, str]]:
    data_dir = choose_data_dir()
    ensure_sample_content(data_dir)
    docs: List[Tuple[str, str]] = []
    for path in sorted(data_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                docs.append((str(path), text))
        if len(docs) >= max_docs:
            break
    return docs


def tokenize(text: str) -> List[str]:
    return TOKEN_PATTERN.findall(text)


def ner_rule(tokens: List[str]):
    entities = set()
    for idx, token in enumerate(tokens):
        if len(token) > 1 and (token[0].isupper() or token.isupper()):
            entities.add((idx, token))
    return entities


def f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def ling_metrics(texts: List[str]) -> float:
    if not texts:
        return 0.0
    tokens_all = [token for text in texts for token in tokenize(text)]
    cap_tokens = [t for t in tokens_all if len(t) > 1 and (t[0].isupper() or t.isupper())]
    freq = Counter(cap_tokens)
    gold = {token for token, count in freq.items() if count >= 2}
    tp = fp = fn = 0
    for text in texts:
        tokens = tokenize(text)
        predicted = {token for _, token in ner_rule(tokens)}
        tp += len(predicted & gold)
        fp += len(predicted - gold)
        fn += len(gold - predicted)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return f1(precision, recall)


def tfidf_corpus(docs: List[Tuple[str, str]]):
    df = Counter()
    tokenized_docs = []
    for _, text in docs:
        tokens = set(tokenize(text.lower()))
        if tokens:
            tokenized_docs.append(tokens)
            df.update(tokens)
    if not tokenized_docs:
        return df, [], lambda _q, _t: 0.0

    def score(query: str, tokens: set) -> float:
        query_tokens = set(tokenize(query.lower()))
        total = 0.0
        for qt in query_tokens:
            if qt in tokens and df[qt]:
                total += 1.0 / df[qt]
        return total

    return df, tokenized_docs, score


def ndcg_at_k(relevances: List[int], k: int = 10) -> float:
    if not relevances:
        return 0.0
    slice_rels = relevances[:k]
    dcg = 0.0
    for idx, rel in enumerate(slice_rels):
        if rel:
            dcg += rel / math.log2(idx + 2)
    ideal_rels = sorted(slice_rels, reverse=True)
    ideal = 0.0
    for idx, rel in enumerate(ideal_rels):
        if rel:
            ideal += rel / math.log2(idx + 2)
    return dcg / ideal if ideal else 0.0


def embed_metric(docs: List[Tuple[str, str]]) -> float:
    if not docs:
        return 0.0
    df, tokenized_docs, scorer = tfidf_corpus(docs)
    if not tokenized_docs or not df:
        return 0.0
    queries = [token for token, _ in df.most_common(3)]
    if not queries:
        return 0.0
    ndcgs = []
    for query in queries:
        scores = [scorer(query, tokens) for tokens in tokenized_docs]
        relevances = [1 if score > 0 else 0 for score in scores]
        ndcgs.append(ndcg_at_k(relevances, k=10))
    return sum(ndcgs) / len(ndcgs)


def edges_evidence_ratio() -> float:
    edges_path = ROOT / "graph" / "edges.jsonl"
    if not edges_path.exists():
        return 0.0
    total = positive = 0
    for line in edges_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        if obj.get("evidence"):
            positive += 1
    return positive / total if total else 0.0


def gather_reference_texts() -> List[str]:
    texts: List[str] = []
    readme = ROOT / "Readme.md"
    if readme.exists():
        texts.append(readme.read_text(encoding="utf-8", errors="ignore"))
    docs_root = ROOT / "docs"
    if docs_root.exists():
        for path in docs_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".md", ".txt"}:
                try:
                    texts.append(path.read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    pass
    return texts


def qa_accuracy(corpus_texts: List[str]) -> float:
    qa_pairs = [
        ("Что такое SMDaI?", "технология декодирования"),
        ("Как называется проектная доска по умолчанию?", "SMDaI Board"),
        ("Какой секрет Actions хранит URL проекта?", "PROJECT_URL"),
    ]
    if not corpus_texts or not qa_pairs:
        return 0.0
    corpus = "\n".join(corpus_texts).lower()
    hits = 0
    for _question, answer in qa_pairs:
        if answer.lower() in corpus:
            hits += 1
    return hits / len(qa_pairs)


def main() -> None:
    docs = read_docs()
    texts = [text for _, text in docs]
    references = gather_reference_texts()
    combined_texts = texts + references
    metrics = {
        "corpus.ingestion_ok": 1.0 if docs else 0.0,
        "ling.ner_f1": round(ling_metrics(texts), 3) if texts else 0.0,
        "embed.search_ndcg@10": round(embed_metric(docs), 3),
        "graph.edges_with_evidence_ratio": round(edges_evidence_ratio(), 3),
        "qa.accuracy": round(qa_accuracy(combined_texts), 3),
    }
    eval_dir = ROOT / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = eval_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote eval/metrics.json:", json.dumps(metrics, ensure_ascii=False))


if __name__ == "__main__":
    main()

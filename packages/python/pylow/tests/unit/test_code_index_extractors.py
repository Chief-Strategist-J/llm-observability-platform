from pytrace_features.code_index.extractors import extract_symbols, lang_for_file, rank_matches


def test_lang_for_file():
    assert lang_for_file("a/b/service.py") == "python"
    assert lang_for_file("main.go") == "go"
    assert lang_for_file("lib.rs") == "rust"
    assert lang_for_file("App.java") == "java"
    assert lang_for_file("app.tsx") == "ts"
    assert lang_for_file("notes.md") is None


def test_extract_python_symbols():
    src = "class PaymentService:\n    async def charge(self, amount):\n        pass\n\ndef helper():\n    pass\n"
    syms = {(s.name, s.kind, s.line) for s in extract_symbols(src, "python")}
    assert ("PaymentService", "class", 1) in syms
    assert ("charge", "function", 2) in syms
    assert ("helper", "function", 5) in syms


def test_extract_go_symbols():
    src = ("type Worker struct {}\n"
           "type Store interface {}\n"
           "func (w *Worker) Consume() {}\n"
           "func HandlePayment(id string) error {}\n")
    syms = {(s.name, s.kind) for s in extract_symbols(src, "go")}
    assert {("Worker", "struct"), ("Store", "interface"),
            ("Consume", "method"), ("HandlePayment", "function")} <= syms


def test_extract_rust_symbols():
    src = ("pub struct Order {}\n"
           "enum Status { Open }\n"
           "pub trait Repo {}\n"
           "pub async fn fetch_orders() {}\n"
           "const MAX_RETRIES: u32 = 3;\n")
    syms = {(s.name, s.kind) for s in extract_symbols(src, "rust")}
    assert {("Order", "struct"), ("Status", "enum"), ("Repo", "trait"),
            ("fetch_orders", "function"), ("MAX_RETRIES", "const")} <= syms


def test_extract_java_symbols():
    src = ("public class OrderService {\n"
           "    private List<Order> findAll(String filter) throws IOException {\n"
           "}\n")
    syms = {(s.name, s.kind) for s in extract_symbols(src, "java")}
    assert ("OrderService", "class") in syms
    assert ("findAll", "method") in syms


def test_extract_ts_symbols():
    src = ("export interface Span {}\n"
           "export type TraceId = string\n"
           "export class Tracer {}\n"
           "export async function startSpan(name: string) {}\n"
           "export const stopSpan = async (id: TraceId): Promise<void> => {}\n"
           "enum Level { Info }\n")
    syms = {(s.name, s.kind) for s in extract_symbols(src, "ts")}
    assert {("Span", "interface"), ("TraceId", "type"), ("Tracer", "class"),
            ("startSpan", "function"), ("stopSpan", "function"), ("Level", "enum")} <= syms


def test_extract_unknown_lang_returns_empty():
    assert extract_symbols("anything", "cobol") == []


def test_rank_matches_orders_exact_prefix_substring():
    names = ["charge_card", "charge", "recharge", "refund"]
    order = rank_matches("charge", names)
    assert [names[i] for i in order] == ["charge", "charge_card", "recharge"]


def test_rank_matches_case_insensitive_and_no_match():
    assert rank_matches("CHARGE", ["Charge"]) == [0]
    assert rank_matches("zzz", ["charge"]) == []

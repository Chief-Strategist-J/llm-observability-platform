import asyncio
from typing import List, Dict, Callable
from temporalio import activity

class FileTailManager:
    def __init__(self, paths: List[str], on_line: Callable[[str, str], None]):
        self.paths = paths
        self.on_line = on_line
        self.tasks = []

    async def tail_file(self, path: str):
        f = open(path, "r")
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                await asyncio.sleep(0.2)
                continue
            self.on_line(path, line.rstrip("\n"))

    async def run(self):
        for p in self.paths:
            self.tasks.append(asyncio.create_task(self.tail_file(p)))
        await asyncio.gather(*self.tasks)

class LabelEnrichmentManager:
    def __init__(self, labels: Dict[str, str]):
        self.labels = labels

    def apply(self, records: List[Dict[str, str]]) -> List[Dict[str, str]]:
        out = []
        for r in records:
            x = dict(r)
            x["labels"] = dict(self.labels)
            out.append(x)
        return out

class BatchManager:
    def __init__(self, size: int):
        self.size = size
        self.buffer = []

    def add(self, rec: Dict[str, str]) -> List[List[Dict[str, str]]]:
        batches = []
        self.buffer.append(rec)
        if len(self.buffer) >= self.size:
            batches.append(self.buffer)
            self.buffer = []
        return batches

class OtlpFormatManager:
    def convert(self, batch: List[Dict[str, str]]) -> List[Dict]:
        out = []
        for r in batch:
            out.append({
                "resource": {"file.path": r["path"]},
                "attributes": r["labels"],
                "body": r["line"]
            })
        return out

@activity.defn
async def tail_label_batch_otlp_activity(paths: List[str], labels: Dict[str, str], batch_size: int) -> None:
    queue = asyncio.Queue()
    def handle(path: str, line: str):
        queue.put_nowait({"path": path, "line": line})
    tail = FileTailManager(paths, handle)
    enrich = LabelEnrichmentManager(labels)
    batcher = BatchManager(batch_size)
    otlp = OtlpFormatManager()
    async def consumer():
        while True:
            rec = await queue.get()
            batches = batcher.add(rec)
            for b in batches:
                enriched = enrich.apply(b)
                formatted = otlp.convert(enriched)
                for item in formatted:
                    print(item)
    await asyncio.gather(tail.run(), consumer())

if __name__ == "__main__":
    async def main():
        q = asyncio.Queue()
        def h(p,l):
            q.put_nowait({"path": p, "line": l})
        tail = FileTailManager(["./logs/app.log"], h)
        enrich = LabelEnrichmentManager({"env": "dev", "app": "demo"})
        batcher = BatchManager(3)
        otlp = OtlpFormatManager()
        async def c():
            while True:
                r = await q.get()
                bs = batcher.add(r)
                for b in bs:
                    e = enrich.apply(b)
                    f = otlp.convert(e)
                    for item in f:
                        print(item)
        await asyncio.gather(tail.run(), c())
    asyncio.run(main())

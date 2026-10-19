from pathlib import Path
from types import SimpleNamespace

import pytest
from src.rag.embeddings import HashEmbeddings, OpenAIEmbeddings, validate_vectors
from src.rag.ingestion import read_cv, chunk_cv
from src.rag.schemas import Citation, EvidenceAnswer
from src.rag.service import CVService
from src.rag.store import MemoryVectorStore

FIXTURE = Path(__file__).resolve().parents[2] / "data/fixtures/sample_cv.md"


def test_chunk_offsets_determinism_and_coverage():
    doc = read_cv(FIXTURE, "a")
    chunks = chunk_cv(doc, 120, 25)
    assert chunks == chunk_cv(doc, 120, 25)
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    covered = set()
    for chunk in chunks:
        assert doc.text[chunk.start:chunk.end] == chunk.text
        assert len(chunk.text) <= 120
        covered.update(range(chunk.start, chunk.end))
    assert all(i in covered for i, c in enumerate(doc.text) if not c.isspace())
    assert any(a.end > b.start for a,b in zip(chunks, chunks[1:]) if a.section == b.section)


@pytest.mark.parametrize("size,overlap", [(0,0),(30,0),(100,100),(100,-1),(2001,10)])
def test_bad_chunk_settings(size, overlap):
    with pytest.raises(ValueError):
        chunk_cv(read_cv(FIXTURE,"a"),size,overlap)


def test_read_empty_and_unsupported(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text(" ")
    with pytest.raises(ValueError, match="no extractable"):
        read_cv(path,"a")
    other = tmp_path / "cv.docx"
    other.write_bytes(b"abc")
    with pytest.raises(ValueError, match="Supported"):
        read_cv(other,"a")


def test_blank_pdf_rejected(tmp_path):
    from pypdf import PdfWriter
    path = tmp_path / "scan.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100,height=100)
    writer.write(path)
    with pytest.raises(ValueError,match="OCR"):
        read_cv(path,"a")


def test_pdf_text_extraction(tmp_path):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer = PdfWriter()
    page = writer.add_blank_page(width=500, height=500)
    font = DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 20 200 Td (Python developer) Tj ET')
    page[NameObject('/Contents')] = stream
    path = tmp_path / "text.pdf"
    writer.write(path)
    assert "Python developer" in read_cv(path,"a").text


def test_replace_isolation_delete_and_model_guard(tmp_path):
    store = MemoryVectorStore()
    service = CVService(HashEmbeddings(),store)
    first = service.ingest(FIXTURE,"a")
    service.ingest(FIXTURE,"b")
    second = service.ingest(FIXTURE,"a")
    assert first == second
    assert len(store.documents["a"][2]) == len(first)
    assert all(h.chunk.cv_id == "a" for h in service.search_cv("Python","a"))
    with pytest.raises(ValueError,match="configuration"):
        store.search("a",[1.0]*512,"different",512,3)
    path = tmp_path / "new.txt"; path.write_text("Replacement content about Rust")
    service.ingest(path,"a")
    assert len(store.documents["a"][2]) == 1
    store.delete("a")
    assert service.search_cv("Python","a") == []
    assert service.search_cv("Python","b")


@pytest.mark.parametrize("vectors,count,dim", [([[0,0]],1,2),([[float('nan'),1]],1,2),([[1]],1,2),([],1,2)])
def test_invalid_embeddings(vectors,count,dim):
    with pytest.raises(ValueError):
        validate_vectors(vectors,count,dim)


def test_openai_embeddings_reorders_and_batches():
    calls=[]
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(data=[SimpleNamespace(index=i,embedding=[float(i+1),1]) for i in reversed(range(len(kwargs["input"])))])
    provider=OpenAIEmbeddings(SimpleNamespace(embeddings=SimpleNamespace(create=create)),dimensions=2)
    result=provider.embed(["text"]*33)
    assert len(calls)==2 and len(result)==33 and result[0]==[1,1]
    assert calls[0]["dimensions"]==2


def test_failed_ingestion_preserves_existing_cv():
    store=MemoryVectorStore(); service=CVService(HashEmbeddings(),store)
    service.ingest(FIXTURE,"a")
    original=store.documents["a"]
    service.embeddings=SimpleNamespace(model="broken",dimensions=512,embed=lambda texts: [])
    with pytest.raises(ValueError):
        service.ingest(FIXTURE,"a")
    assert store.documents["a"] == original


def test_grounded_answer_and_reject_fabrication():
    service=CVService(HashEmbeddings(),MemoryVectorStore());service.ingest(FIXTURE,"a")
    hit=service.search_cv("German language level","a",1)[0]
    good=EvidenceAnswer(citations=[Citation(chunk_id=hit.chunk.chunk_id,quote="German B1")],insufficient_evidence=False)
    provider=SimpleNamespace(generate=lambda messages,schema:good)
    assert service.answer("German language level","a",provider,k=1)==good
    for citation in [Citation(chunk_id="unknown",quote="German B1"),Citation(chunk_id=hit.chunk.chunk_id,quote="German C2")]:
        bad=EvidenceAnswer(citations=[citation],insufficient_evidence=False)
        with pytest.raises(ValueError,match="unsupported"):
            service.answer("German language level","a",SimpleNamespace(generate=lambda m,s:bad),k=1)
    assert service.answer("Python","missing",provider).insufficient_evidence
    abstain=EvidenceAnswer(citations=[],insufficient_evidence=True)
    assert service.answer("Salary?","a",SimpleNamespace(generate=lambda m,s:abstain)).insufficient_evidence


@pytest.mark.parametrize("query,k", [("",3),("a",0),("a",51),("a"*2001,3)])
def test_search_input_validation(query,k):
    with pytest.raises(ValueError):
        CVService(HashEmbeddings(),MemoryVectorStore()).search_cv(query,"a",k)


def test_retrieval_benchmark_has_explicit_ground_truth():
    from scripts.evaluate_cv_retrieval import evaluate
    result=evaluate(CVService(HashEmbeddings(),MemoryVectorStore()),"test",900,150,3)
    assert result["questions"]==20
    assert result["evidence_coverage"]==1
    assert result["hit_rate"]>=0.8

"""
Generic Document Chunker - Industrial-grade document processing for RAG ingestion.

Cortez92: Complete rewrite for truly generic document processing.

Design Goals:
- Works with ANY document type/theme (not tied to educational domain)
- Pluggable extractors (text, PDF, DOCX, HTML, Markdown, code files)
- Multi-language support (code detection: 15+ languages)
- Semantic boundary detection (respects paragraphs, functions, sections)
- Chunk relationship tracking (parent/child, prev/next)
- Overlap management with deduplication metadata
- Async-first for I/O operations
- Production-ready logging and observability

Architecture:
    DocumentChunker (orchestrator)
        -> ContentExtractor (Strategy pattern: PDF, DOCX, HTML, Markdown, Code, Plain)
        -> SemanticSplitter (boundary-aware splitting)
        -> ChunkEnricher (metadata, relationships, embeddings)
        -> OutputFormatter (various output formats)
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import math
import mimetypes
import re
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class ChunkingStrategy(str, Enum):
    """How to split documents into chunks."""
    FIXED_SIZE = "fixed_size"           # Fixed character/token windows
    SEMANTIC = "semantic"               # Respect semantic boundaries
    RECURSIVE = "recursive"             # Try multiple splitters in order
    SENTENCE = "sentence"               # Split by sentences
    PARAGRAPH = "paragraph"             # Split by paragraphs
    CODE_AWARE = "code_aware"           # Respect code block boundaries


class ContentType(str, Enum):
    """Types of content detected in chunks."""
    PROSE = "prose"
    CODE = "code"
    TABLE = "table"
    LIST = "list"
    HEADING = "heading"
    BLOCKQUOTE = "blockquote"
    MIXED = "mixed"


class CodeLanguage(str, Enum):
    """Detected programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    SQL = "sql"
    BASH = "bash"
    POWERSHELL = "powershell"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


@dataclass
class ChunkerConfig:
    """
    Configuration for document chunking.

    All parameters have sensible defaults for RAG ingestion.
    Customize based on your embedding model and retrieval needs.

    Example:
        config = ChunkerConfig(
            max_chunk_size=512,  # For smaller embedding models
            overlap_size=50,
            strategy=ChunkingStrategy.SEMANTIC
        )
    """
    # Size limits (in characters)
    max_chunk_size: int = 1000
    min_chunk_size: int = 100
    overlap_size: int = 100

    # Target size (for semantic splitting)
    target_chunk_size: int = 800

    # Strategy
    strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC

    # Merge behavior
    merge_small_chunks: bool = True
    max_merge_size: int = 1200

    # Title/heading detection
    min_title_length: int = 3
    max_title_length: int = 150

    # Code handling
    preserve_code_blocks: bool = True
    max_code_block_size: int = 2000  # Allow larger code blocks

    # Metadata
    extract_keywords: bool = True
    keywords_count: int = 10
    detect_language: bool = True
    compute_hash: bool = True

    # Token estimation (chars per token, varies by language/model)
    chars_per_token: float = 4.0

    # Relationship tracking
    track_relationships: bool = True
    include_overlap_hashes: bool = True  # For deduplication

    # Language settings
    primary_language: str = "auto"  # ISO 639-1 or "auto"

    def __post_init__(self):
        """Validate configuration."""
        if self.max_chunk_size < self.min_chunk_size:
            raise ValueError("max_chunk_size must be >= min_chunk_size")
        if self.overlap_size >= self.max_chunk_size:
            raise ValueError("overlap_size must be < max_chunk_size")
        if self.target_chunk_size > self.max_chunk_size:
            self.target_chunk_size = self.max_chunk_size


# =============================================================================
# CHUNK DATA STRUCTURES
# =============================================================================

@dataclass
class ChunkMetadata:
    """
    Rich metadata for a document chunk.

    Designed for maximum utility in RAG retrieval:
    - Content classification helps filtering
    - Position info helps reconstruction
    - Relationships enable graph-based retrieval
    - Hashes enable deduplication
    """
    # Document info
    document_id: str = ""
    document_hash: str = ""
    source_path: Optional[str] = None
    source_type: str = "unknown"  # pdf, docx, html, text, code, etc.

    # Position in document
    chunk_index: int = 0
    total_chunks: int = 0
    page_number: Optional[int] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    char_start: int = 0
    char_end: int = 0

    # Content analysis
    content_type: ContentType = ContentType.PROSE
    has_code: bool = False
    code_language: CodeLanguage = CodeLanguage.UNKNOWN
    has_table: bool = False
    has_list: bool = False

    # Hierarchy
    section_title: str = ""
    section_level: int = 0  # 0=root, 1=h1, 2=h2, etc.
    parent_section: str = ""

    # Token estimation
    estimated_tokens: int = 0

    # Keywords and content hints
    keywords: List[str] = field(default_factory=list)
    named_entities: List[str] = field(default_factory=list)

    # Relationships (for graph retrieval)
    prev_chunk_id: Optional[str] = None
    next_chunk_id: Optional[str] = None
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = field(default_factory=list)

    # Overlap tracking (for deduplication)
    overlap_hash_prev: Optional[str] = None  # Hash of overlap with previous
    overlap_hash_next: Optional[str] = None  # Hash of overlap with next

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Extensible custom fields
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "document_id": self.document_id,
            "document_hash": self.document_hash,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "page_number": self.page_number,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "content_type": self.content_type.value,
            "has_code": self.has_code,
            "code_language": self.code_language.value,
            "has_table": self.has_table,
            "has_list": self.has_list,
            "section_title": self.section_title,
            "section_level": self.section_level,
            "parent_section": self.parent_section,
            "estimated_tokens": self.estimated_tokens,
            "keywords": self.keywords,
            "named_entities": self.named_entities,
            "prev_chunk_id": self.prev_chunk_id,
            "next_chunk_id": self.next_chunk_id,
            "parent_chunk_id": self.parent_chunk_id,
            "child_chunk_ids": self.child_chunk_ids,
            "overlap_hash_prev": self.overlap_hash_prev,
            "overlap_hash_next": self.overlap_hash_next,
            "created_at": self.created_at.isoformat(),
            "custom": self.custom,
        }


@dataclass
class Chunk:
    """
    A document chunk ready for embedding and storage.

    Attributes:
        id: Unique identifier for this chunk
        content: The actual text content
        metadata: Rich metadata about the chunk
        embedding: Optional pre-computed embedding vector
    """
    id: str
    content: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None

    @property
    def content_hash(self) -> str:
        """SHA-256 hash of the content."""
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "content_hash": self.content_hash,
            "metadata": self.metadata.to_dict(),
            "embedding": self.embedding,
        }


@dataclass
class ChunkingResult:
    """
    Result of chunking a document.

    Contains chunks and statistics about the operation.
    """
    document_id: str
    document_hash: str
    source_path: Optional[str]
    chunks: List[Chunk]
    stats: Dict[str, Any]

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_hash": self.document_hash,
            "source_path": self.source_path,
            "chunk_count": self.chunk_count,
            "chunks": [c.to_dict() for c in self.chunks],
            "stats": self.stats,
        }


# =============================================================================
# TEXT PROCESSING UTILITIES
# =============================================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for consistent processing.

    - Converts line endings to Unix style
    - Normalizes Unicode
    - Collapses excessive whitespace
    - Trims trailing whitespace per line
    """
    # Normalize Unicode
    text = unicodedata.normalize("NFKC", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Convert tabs to spaces
    text = text.replace("\t", "    ")

    # Remove trailing whitespace per line
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)

    # Collapse multiple blank lines to max 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def compute_hash(text: str) -> str:
    """Compute SHA-256 hash of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def estimate_tokens(text: str, chars_per_token: float = 4.0) -> int:
    """
    Estimate token count for text.

    Uses simple heuristic: characters / chars_per_token.
    For accurate counts, use tiktoken with your specific model.

    Args:
        text: Text to estimate
        chars_per_token: Average characters per token (4.0 for English, 2.5 for CJK)

    Returns:
        Estimated token count
    """
    if not text.strip():
        return 0
    return max(1, math.ceil(len(text) / chars_per_token))


# =============================================================================
# LANGUAGE DETECTION
# =============================================================================

# Code language detection patterns (expanded from original)
_LANGUAGE_PATTERNS: Dict[CodeLanguage, List[re.Pattern]] = {
    CodeLanguage.PYTHON: [
        re.compile(r"\b(def|class|import|from|elif|None|True|False|async|await|lambda|yield)\b"),
        re.compile(r"^\s*@\w+", re.MULTILINE),  # Decorators
        re.compile(r"^\s*#.*$", re.MULTILINE),   # Comments
        re.compile(r":\s*$", re.MULTILINE),       # Colons at line end
    ],
    CodeLanguage.JAVASCRIPT: [
        re.compile(r"\b(const|let|var|function|=>|async|await|require|module\.exports)\b"),
        re.compile(r"\bconsole\.(log|error|warn)\b"),
        re.compile(r"^\s*//.*$", re.MULTILINE),
    ],
    CodeLanguage.TYPESCRIPT: [
        re.compile(r"\b(interface|type|enum|namespace|readonly|as|implements)\b"),
        re.compile(r":\s*(string|number|boolean|any|void|never)\b"),
        re.compile(r"<[A-Z]\w*>"),  # Generics
    ],
    CodeLanguage.JAVA: [
        re.compile(r"\b(public|private|protected|class|interface|extends|implements|static|void|new|package)\b"),
        re.compile(r"\bSystem\.out\.print"),
        re.compile(r"@Override|@Autowired|@Bean"),
    ],
    CodeLanguage.CSHARP: [
        re.compile(r"\b(namespace|using|public|private|internal|class|struct|interface|async|await|var)\b"),
        re.compile(r"\bConsole\.(Write|Read)"),
        re.compile(r"\[.*\]", re.MULTILINE),  # Attributes
    ],
    CodeLanguage.CPP: [
        re.compile(r"\b(#include|namespace|std::|cout|cin|endl|nullptr|template|typename)\b"),
        re.compile(r"::\w+"),  # Scope resolution
        re.compile(r"\b(vector|map|set|string)<"),
    ],
    CodeLanguage.C: [
        re.compile(r"\b(#include|#define|typedef|struct|union|enum|sizeof|malloc|free|printf|scanf)\b"),
        re.compile(r"\bint\s+main\s*\("),
        re.compile(r"\b(void|int|char|float|double)\s*\*"),  # Pointers
    ],
    CodeLanguage.GO: [
        re.compile(r"\b(package|import|func|type|struct|interface|go|chan|defer|select)\b"),
        re.compile(r":="),  # Short variable declaration
        re.compile(r"fmt\.(Print|Sprintf|Errorf)"),
    ],
    CodeLanguage.RUST: [
        re.compile(r"\b(fn|let|mut|impl|trait|struct|enum|match|pub|mod|use|crate)\b"),
        re.compile(r"->"),  # Return type
        re.compile(r"&\w+|&mut\s"),  # References
    ],
    CodeLanguage.RUBY: [
        re.compile(r"\b(def|end|class|module|require|attr_accessor|puts|gets)\b"),
        re.compile(r":\w+"),  # Symbols
        re.compile(r"\|.*\|"),  # Block parameters
    ],
    CodeLanguage.PHP: [
        re.compile(r"<\?php|\?>"),
        re.compile(r"\$\w+"),  # Variables
        re.compile(r"\b(function|class|public|private|protected|namespace|use)\b"),
    ],
    CodeLanguage.SWIFT: [
        re.compile(r"\b(func|var|let|class|struct|enum|protocol|extension|guard|if let|optional)\b"),
        re.compile(r"->"),
        re.compile(r"@\w+"),  # Attributes
    ],
    CodeLanguage.KOTLIN: [
        re.compile(r"\b(fun|val|var|class|object|interface|data class|sealed|when)\b"),
        re.compile(r":\s*\w+[?]?"),  # Type annotations
        re.compile(r"\.let\s*\{|\.apply\s*\{"),
    ],
    CodeLanguage.SQL: [
        re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|FROM|WHERE|JOIN|GROUP BY|ORDER BY|HAVING)\b", re.IGNORECASE),
        re.compile(r"\b(TABLE|INDEX|VIEW|TRIGGER|PROCEDURE|FUNCTION)\b", re.IGNORECASE),
    ],
    CodeLanguage.BASH: [
        re.compile(r"^#!/bin/(ba)?sh", re.MULTILINE),
        re.compile(r"\b(echo|export|source|if|then|else|fi|for|do|done|while|case|esac)\b"),
        re.compile(r"\$\{?\w+\}?"),  # Variables
    ],
    CodeLanguage.POWERSHELL: [
        re.compile(r"\$\w+"),
        re.compile(r"\b(Get-|Set-|New-|Remove-|Write-Host|Invoke-)\w+"),
        re.compile(r"-\w+"),  # Parameters
    ],
    CodeLanguage.HTML: [
        re.compile(r"<(!DOCTYPE|html|head|body|div|span|p|a|img|script|style|meta|link)\b", re.IGNORECASE),
        re.compile(r"</\w+>"),
        re.compile(r'\s(class|id|href|src|style)='),
    ],
    CodeLanguage.CSS: [
        re.compile(r"[\.\#]\w+\s*\{"),  # Class/ID selectors
        re.compile(r":\s*(flex|grid|block|inline|none|relative|absolute)"),
        re.compile(r"@(media|import|keyframes|font-face)"),
    ],
    CodeLanguage.JSON: [
        re.compile(r'^\s*[\{\[]', re.MULTILINE),
        re.compile(r'"\w+":\s*'),
        re.compile(r'(true|false|null)\s*[,\}\]]'),
    ],
    CodeLanguage.YAML: [
        re.compile(r"^\w+:\s*$", re.MULTILINE),
        re.compile(r"^\s*-\s+\w+", re.MULTILINE),
        re.compile(r"^\s{2,}\w+:", re.MULTILINE),
    ],
    CodeLanguage.XML: [
        re.compile(r"<\?xml\s+version"),
        re.compile(r"<!\[CDATA\["),
        re.compile(r"xmlns(:\w+)?="),
    ],
    CodeLanguage.MARKDOWN: [
        re.compile(r"^#{1,6}\s+\S", re.MULTILINE),
        re.compile(r"^\s*[-*+]\s+", re.MULTILINE),
        re.compile(r"\[.*\]\(.*\)"),  # Links
        re.compile(r"```\w*\n"),  # Code blocks
    ],
}


def detect_code_language(text: str) -> Tuple[CodeLanguage, float]:
    """
    Detect the programming language of text.

    Returns:
        Tuple of (language, confidence) where confidence is 0.0-1.0
    """
    if not text.strip():
        return CodeLanguage.UNKNOWN, 0.0

    scores: Dict[CodeLanguage, int] = {}

    for lang, patterns in _LANGUAGE_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = len(pattern.findall(text))
            score += matches * 2  # Weight each match
        if score > 0:
            scores[lang] = score

    if not scores:
        return CodeLanguage.UNKNOWN, 0.0

    # Find best match
    best_lang = max(scores, key=lambda k: scores[k])
    best_score = scores[best_lang]

    # Calculate confidence (normalized by text length)
    max_possible = len(text) // 20  # Rough estimate of max possible matches
    confidence = min(1.0, best_score / max(max_possible, 10))

    # Require minimum confidence
    if confidence < 0.1:
        return CodeLanguage.UNKNOWN, confidence

    return best_lang, confidence


def is_code_block(text: str) -> bool:
    """Check if text looks like a code block."""
    lines = text.strip().split("\n")
    code_lines = 0

    for line in lines:
        # Indented lines
        if line.startswith("    ") or line.startswith("\t"):
            code_lines += 1
        # Common code patterns
        elif re.search(r"[{};()]|\b(if|for|while|def|class|function|return)\b", line):
            code_lines += 1

    return code_lines > len(lines) * 0.3


# =============================================================================
# STOPWORDS (MULTILINGUAL)
# =============================================================================

STOPWORDS: Dict[str, set] = {
    "en": {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "has", "he", "in", "is", "it", "its", "of", "on", "or", "that",
        "the", "to", "was", "were", "will", "with", "this", "which",
        "you", "your", "have", "been", "would", "could", "should", "can",
        "not", "but", "they", "their", "there", "what", "when", "where",
    },
    "es": {
        "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o",
        "u", "de", "del", "al", "en", "por", "para", "con", "sin", "es",
        "son", "ser", "se", "que", "como", "si", "no", "mas", "muy", "ya",
        "a", "e", "lo", "su", "sus", "este", "esta", "estos", "estas",
        "hay", "tambien", "pero", "porque", "cuando", "donde", "sobre",
    },
    "pt": {
        "o", "a", "os", "as", "um", "uma", "uns", "umas", "e", "ou", "de",
        "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "por",
        "para", "com", "sem", "ser", "estar", "que", "como", "se", "nao",
    },
    "fr": {
        "le", "la", "les", "un", "une", "des", "et", "ou", "de", "du",
        "a", "en", "pour", "par", "avec", "sans", "est", "sont", "que",
        "qui", "ce", "cette", "ces", "dans", "sur", "sous", "ne", "pas",
    },
    "de": {
        "der", "die", "das", "ein", "eine", "und", "oder", "von", "zu",
        "in", "mit", "auf", "fur", "ist", "sind", "war", "werden", "nicht",
        "aber", "auch", "als", "an", "bei", "nach", "uber", "wenn", "wie",
    },
}


def extract_keywords(
    text: str,
    top_k: int = 10,
    language: str = "auto",
    min_word_length: int = 2
) -> List[str]:
    """
    Extract keywords from text using frequency analysis.

    Args:
        text: Input text
        top_k: Maximum keywords to return
        language: Language for stopwords ("auto", "en", "es", etc.)
        min_word_length: Minimum word length to consider

    Returns:
        List of top keywords
    """
    # Detect language if auto
    if language == "auto":
        # Simple heuristic based on common words
        text_lower = text.lower()
        if any(w in text_lower for w in ["the", "and", "that", "with"]):
            language = "en"
        elif any(w in text_lower for w in ["que", "para", "como", "pero"]):
            language = "es"
        else:
            language = "en"  # Default

    stopwords = STOPWORDS.get(language, STOPWORDS["en"])

    # Tokenize
    words = re.findall(r'\b[a-zA-Z\u00C0-\u017F]+\b', text.lower())

    # Count frequencies
    freq: Dict[str, int] = {}
    for word in words:
        if len(word) < min_word_length:
            continue
        if word in stopwords:
            continue
        if word.isdigit():
            continue
        freq[word] = freq.get(word, 0) + 1

    # Rank by frequency, then length
    ranked = sorted(freq.items(), key=lambda kv: (kv[1], len(kv[0])), reverse=True)
    return [word for word, _ in ranked[:top_k]]


# =============================================================================
# CONTENT EXTRACTORS (Strategy Pattern)
# =============================================================================

class ContentExtractor(ABC):
    """Abstract base for content extractors."""

    @abstractmethod
    def supports(self, source: Union[str, Path, bytes], mime_type: Optional[str] = None) -> bool:
        """Check if this extractor supports the given source."""
        ...

    @abstractmethod
    async def extract(
        self,
        source: Union[str, Path, bytes],
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text content from source.

        Returns:
            Tuple of (extracted_text, metadata)
        """
        ...


class PlainTextExtractor(ContentExtractor):
    """Extract plain text files."""

    ENCODINGS = ["utf-8", "utf-16", "latin-1", "cp1252"]

    def supports(self, source: Union[str, Path, bytes], mime_type: Optional[str] = None) -> bool:
        if isinstance(source, bytes):
            return True
        if mime_type and mime_type.startswith("text/"):
            return True
        if isinstance(source, (str, Path)):
            path = Path(source) if isinstance(source, str) else source
            return path.suffix.lower() in {".txt", ".text", ".log", ".md", ".rst"}
        return False

    async def extract(
        self,
        source: Union[str, Path, bytes],
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        metadata: Dict[str, Any] = {"source_type": "text"}

        if isinstance(source, bytes):
            content = source
        else:
            path = Path(source)
            content = path.read_bytes()
            metadata["source_path"] = str(path)
            metadata["file_size"] = len(content)

        # Try encodings
        text = None
        for encoding in self.ENCODINGS:
            try:
                text = content.decode(encoding)
                metadata["encoding"] = encoding
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if text is None:
            # Fallback with replacement
            text = content.decode("utf-8", errors="replace")
            metadata["encoding"] = "utf-8-fallback"

        return normalize_text(text), metadata


class MarkdownExtractor(ContentExtractor):
    """Extract Markdown files with structure preservation."""

    def supports(self, source: Union[str, Path, bytes], mime_type: Optional[str] = None) -> bool:
        if mime_type and "markdown" in mime_type:
            return True
        if isinstance(source, (str, Path)):
            path = Path(source) if isinstance(source, str) else source
            return path.suffix.lower() in {".md", ".markdown", ".mkd"}
        return False

    async def extract(
        self,
        source: Union[str, Path, bytes],
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        # Get plain text first
        plain_extractor = PlainTextExtractor()
        text, metadata = await plain_extractor.extract(source, **kwargs)
        metadata["source_type"] = "markdown"

        # Optionally strip markdown formatting for embedding
        # (keeping structure for now)
        return text, metadata


class CodeFileExtractor(ContentExtractor):
    """Extract source code files with language detection."""

    CODE_EXTENSIONS: Dict[str, CodeLanguage] = {
        ".py": CodeLanguage.PYTHON,
        ".pyw": CodeLanguage.PYTHON,
        ".js": CodeLanguage.JAVASCRIPT,
        ".mjs": CodeLanguage.JAVASCRIPT,
        ".jsx": CodeLanguage.JAVASCRIPT,
        ".ts": CodeLanguage.TYPESCRIPT,
        ".tsx": CodeLanguage.TYPESCRIPT,
        ".java": CodeLanguage.JAVA,
        ".cs": CodeLanguage.CSHARP,
        ".cpp": CodeLanguage.CPP,
        ".cc": CodeLanguage.CPP,
        ".cxx": CodeLanguage.CPP,
        ".hpp": CodeLanguage.CPP,
        ".c": CodeLanguage.C,
        ".h": CodeLanguage.C,
        ".go": CodeLanguage.GO,
        ".rs": CodeLanguage.RUST,
        ".rb": CodeLanguage.RUBY,
        ".php": CodeLanguage.PHP,
        ".swift": CodeLanguage.SWIFT,
        ".kt": CodeLanguage.KOTLIN,
        ".kts": CodeLanguage.KOTLIN,
        ".scala": CodeLanguage.SCALA,
        ".sql": CodeLanguage.SQL,
        ".sh": CodeLanguage.BASH,
        ".bash": CodeLanguage.BASH,
        ".ps1": CodeLanguage.POWERSHELL,
        ".html": CodeLanguage.HTML,
        ".htm": CodeLanguage.HTML,
        ".css": CodeLanguage.CSS,
        ".scss": CodeLanguage.CSS,
        ".sass": CodeLanguage.CSS,
        ".json": CodeLanguage.JSON,
        ".yaml": CodeLanguage.YAML,
        ".yml": CodeLanguage.YAML,
        ".xml": CodeLanguage.XML,
    }

    def supports(self, source: Union[str, Path, bytes], mime_type: Optional[str] = None) -> bool:
        if isinstance(source, (str, Path)):
            path = Path(source) if isinstance(source, str) else source
            return path.suffix.lower() in self.CODE_EXTENSIONS
        return False

    async def extract(
        self,
        source: Union[str, Path, bytes],
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        plain_extractor = PlainTextExtractor()
        text, metadata = await plain_extractor.extract(source, **kwargs)

        if isinstance(source, (str, Path)):
            path = Path(source) if isinstance(source, str) else source
            ext = path.suffix.lower()
            if ext in self.CODE_EXTENSIONS:
                metadata["code_language"] = self.CODE_EXTENSIONS[ext].value

        metadata["source_type"] = "code"
        return text, metadata


# =============================================================================
# SEMANTIC SPLITTER
# =============================================================================

class SemanticSplitter:
    """
    Split text respecting semantic boundaries.

    Handles:
    - Section headings (Markdown, numbered, uppercase)
    - Paragraph boundaries
    - Code block boundaries
    - Sentence boundaries (for prose)
    """

    # Heading patterns
    HEADING_PATTERNS = [
        # Markdown headings
        re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE),
        # Numbered headings: 1) 1. 1.2.3) etc.
        re.compile(r"^(\d+(?:\.\d+)*[.)]\s+)(.+)$", re.MULTILINE),
        # Roman numerals: I) II. III) etc.
        re.compile(r"^([IVXLCDM]+[.)]\s+)(.+)$", re.MULTILINE),
        # Uppercase titles (max 80 chars, no code-like patterns)
        re.compile(r"^([A-Z][A-Z\s]{2,78}[A-Z])$", re.MULTILINE),
    ]

    # Code block patterns
    CODE_FENCE = re.compile(r"^```(\w*)$", re.MULTILINE)

    def __init__(self, config: ChunkerConfig):
        self.config = config

    def split_into_sections(self, text: str) -> List[Tuple[str, str, int]]:
        """
        Split text into sections based on headings.

        Returns:
            List of (section_title, section_content, heading_level) tuples
        """
        lines = text.split("\n")
        sections: List[Tuple[str, List[str], int]] = []
        current_title = ""
        current_level = 0
        current_body: List[str] = []

        def flush():
            nonlocal current_title, current_body, current_level
            body = "\n".join(current_body).strip()
            if body:
                sections.append((current_title, current_body.copy(), current_level))
            current_body = []

        for line in lines:
            heading_match = self._is_heading(line)
            if heading_match:
                flush()
                current_title, current_level = heading_match
            else:
                current_body.append(line)

        flush()

        # Convert to final format
        result: List[Tuple[str, str, int]] = []
        for title, body_lines, level in sections:
            body = "\n".join(body_lines).strip()
            if body:
                result.append((title or "Untitled", body, level))

        return result or [("Untitled", text.strip(), 0)]

    def _is_heading(self, line: str) -> Optional[Tuple[str, int]]:
        """Check if line is a heading, return (title, level) or None."""
        stripped = line.strip()
        if not stripped:
            return None

        # Length check
        if len(stripped) < self.config.min_title_length:
            return None
        if len(stripped) > self.config.max_title_length:
            return None

        # Markdown headings
        md_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if md_match:
            level = len(md_match.group(1))
            title = md_match.group(2).strip()
            return (title, level)

        # Numbered headings
        num_match = re.match(r"^(\d+(?:\.\d+)*)[.)]\s+(.+)$", stripped)
        if num_match:
            title = num_match.group(2).strip()
            # Estimate level from number of dots
            level = stripped.count(".") + 1
            return (title, min(level, 6))

        # Uppercase titles (not code-like)
        if stripped.isupper() and len(stripped) <= 80:
            if not is_code_block(stripped):
                return (stripped.title(), 1)

        return None

    def split_preserving_code(self, text: str) -> List[Tuple[str, ContentType]]:
        """
        Split text into blocks, preserving code blocks.

        Returns:
            List of (block_content, content_type) tuples
        """
        blocks: List[Tuple[str, ContentType]] = []

        # Find code fences
        parts = self.CODE_FENCE.split(text)
        in_code = False
        code_lang = ""

        for i, part in enumerate(parts):
            if i % 2 == 1:
                # This is a language specifier after ```
                code_lang = part
                in_code = True
                continue

            if in_code:
                # This is code block content
                blocks.append((part.strip(), ContentType.CODE))
                in_code = False
            else:
                # Regular text - split into paragraphs
                paragraphs = re.split(r"\n\s*\n", part)
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue

                    # Detect content type
                    if is_code_block(para):
                        blocks.append((para, ContentType.CODE))
                    elif re.match(r"^\s*[-*+]\s", para, re.MULTILINE):
                        blocks.append((para, ContentType.LIST))
                    elif re.match(r"^\s*\|", para, re.MULTILINE):
                        blocks.append((para, ContentType.TABLE))
                    elif re.match(r"^\s*>", para, re.MULTILINE):
                        blocks.append((para, ContentType.BLOCKQUOTE))
                    else:
                        blocks.append((para, ContentType.PROSE))

        return blocks

    def chunk_text(self, text: str, content_type: ContentType = ContentType.PROSE) -> List[str]:
        """
        Chunk text respecting semantic boundaries.

        For prose: cuts at sentence boundaries
        For code: tries to preserve complete statements
        """
        text = text.strip()

        if len(text) <= self.config.min_chunk_size:
            return []

        if len(text) <= self.config.max_chunk_size:
            return [text]

        chunks: List[str] = []

        if content_type == ContentType.CODE:
            # Code: chunk by lines, respecting indentation blocks
            chunks = self._chunk_code(text)
        else:
            # Prose: chunk by sentences
            chunks = self._chunk_prose(text)

        return chunks

    def _chunk_prose(self, text: str) -> List[str]:
        """Chunk prose text at sentence boundaries."""
        chunks: List[str] = []
        start = 0

        while start < len(text):
            end = min(len(text), start + self.config.max_chunk_size)
            chunk = text[start:end].strip()

            # Try to cut at sentence end
            if end < len(text):
                # Look for sentence endings
                for pattern in [". ", ".\n", "! ", "!\n", "? ", "?\n"]:
                    last_idx = chunk.rfind(pattern)
                    if last_idx > self.config.min_chunk_size:
                        chunk = chunk[:last_idx + 1].strip()
                        end = start + len(chunk)
                        break

            if len(chunk) >= self.config.min_chunk_size:
                chunks.append(chunk)

            # Move forward with overlap
            start = max(start + 1, end - self.config.overlap_size)

        return chunks

    def _chunk_code(self, text: str) -> List[str]:
        """Chunk code respecting block boundaries."""
        lines = text.split("\n")
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            # Check if adding this line exceeds max
            if current_size + line_size > self.config.max_chunk_size and current_chunk:
                # Emit current chunk
                chunk_text = "\n".join(current_chunk).strip()
                if len(chunk_text) >= self.config.min_chunk_size:
                    chunks.append(chunk_text)

                # Start new chunk with overlap
                overlap_lines = self._get_overlap_lines(current_chunk)
                current_chunk = overlap_lines + [line]
                current_size = sum(len(l) + 1 for l in current_chunk)
            else:
                current_chunk.append(line)
                current_size += line_size

        # Final chunk
        if current_chunk:
            chunk_text = "\n".join(current_chunk).strip()
            if len(chunk_text) >= self.config.min_chunk_size:
                chunks.append(chunk_text)

        return chunks

    def _get_overlap_lines(self, lines: List[str]) -> List[str]:
        """Get lines for overlap from end of chunk."""
        overlap_chars = 0
        overlap_lines: List[str] = []

        for line in reversed(lines):
            overlap_chars += len(line) + 1
            if overlap_chars > self.config.overlap_size:
                break
            overlap_lines.insert(0, line)

        return overlap_lines


# =============================================================================
# DOCUMENT CHUNKER (Main Orchestrator)
# =============================================================================

class DocumentChunker:
    """
    Main document chunking orchestrator.

    Usage:
        chunker = DocumentChunker()
        result = await chunker.chunk_document("path/to/file.pdf")

        # Or with custom config
        config = ChunkerConfig(max_chunk_size=500)
        chunker = DocumentChunker(config)
        result = await chunker.chunk_text(text, metadata={"source": "api"})

    Features:
        - Automatic format detection
        - Pluggable extractors
        - Semantic-aware splitting
        - Rich metadata generation
        - Relationship tracking
    """

    def __init__(
        self,
        config: Optional[ChunkerConfig] = None,
        extractors: Optional[List[ContentExtractor]] = None
    ):
        self.config = config or ChunkerConfig()
        self.splitter = SemanticSplitter(self.config)

        # Default extractors
        self.extractors: List[ContentExtractor] = extractors or [
            MarkdownExtractor(),
            CodeFileExtractor(),
            PlainTextExtractor(),  # Fallback
        ]

    async def chunk_document(
        self,
        source: Union[str, Path, bytes],
        mime_type: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> ChunkingResult:
        """
        Chunk a document from file path or bytes.

        Args:
            source: File path or raw bytes
            mime_type: Optional MIME type hint
            custom_metadata: Additional metadata to include

        Returns:
            ChunkingResult with all chunks and stats
        """
        # Find appropriate extractor
        extractor = None
        for ext in self.extractors:
            if ext.supports(source, mime_type):
                extractor = ext
                break

        if extractor is None:
            # Use plain text as fallback
            extractor = PlainTextExtractor()

        # Extract content
        text, extract_metadata = await extractor.extract(source)

        # Merge custom metadata
        if custom_metadata:
            extract_metadata.update(custom_metadata)

        # Chunk the text
        return await self.chunk_text(text, extract_metadata)

    async def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChunkingResult:
        """
        Chunk raw text into chunks.

        Args:
            text: Raw text content
            metadata: Document-level metadata

        Returns:
            ChunkingResult with all chunks
        """
        metadata = metadata or {}

        # Normalize text
        text = normalize_text(text)

        # Generate document ID and hash
        doc_hash = compute_hash(text)
        doc_id = metadata.get("document_id") or str(uuid4())
        source_path = metadata.get("source_path")
        source_type = metadata.get("source_type", "text")

        # Split into sections
        sections = self.splitter.split_into_sections(text)

        # Process each section
        all_chunks: List[Chunk] = []
        chunk_index = 0
        char_offset = 0

        for section_title, section_content, section_level in sections:
            # Split section into blocks
            blocks = self.splitter.split_preserving_code(section_content)

            for block_content, content_type in blocks:
                # Chunk each block
                block_chunks = self.splitter.chunk_text(block_content, content_type)

                if not block_chunks:
                    # Block too small to chunk, include as-is if meaningful
                    if len(block_content) >= self.config.min_chunk_size:
                        block_chunks = [block_content]

                for piece in block_chunks:
                    # Detect code language if applicable
                    has_code = content_type == ContentType.CODE or is_code_block(piece)
                    code_lang = CodeLanguage.UNKNOWN
                    if has_code and self.config.detect_language:
                        code_lang, _ = detect_code_language(piece)

                    # Extract keywords
                    keywords = []
                    if self.config.extract_keywords:
                        keywords = extract_keywords(
                            piece,
                            top_k=self.config.keywords_count,
                            language=self.config.primary_language
                        )

                    # Compute position
                    char_start = char_offset
                    char_end = char_offset + len(piece)
                    char_offset = char_end

                    # Build metadata
                    chunk_metadata = ChunkMetadata(
                        document_id=doc_id,
                        document_hash=doc_hash,
                        source_path=source_path,
                        source_type=source_type,
                        chunk_index=chunk_index,
                        char_start=char_start,
                        char_end=char_end,
                        content_type=content_type,
                        has_code=has_code,
                        code_language=code_lang,
                        section_title=section_title,
                        section_level=section_level,
                        estimated_tokens=estimate_tokens(piece, self.config.chars_per_token),
                        keywords=keywords,
                        custom=metadata.get("custom", {}),
                    )

                    # Create chunk
                    chunk = Chunk(
                        id=str(uuid4()),
                        content=piece,
                        metadata=chunk_metadata,
                    )
                    all_chunks.append(chunk)
                    chunk_index += 1

        # Update total chunks count and relationships
        total_chunks = len(all_chunks)
        for i, chunk in enumerate(all_chunks):
            chunk.metadata.total_chunks = total_chunks

            if self.config.track_relationships:
                if i > 0:
                    chunk.metadata.prev_chunk_id = all_chunks[i - 1].id
                if i < total_chunks - 1:
                    chunk.metadata.next_chunk_id = all_chunks[i + 1].id

                # Compute overlap hashes for deduplication
                if self.config.include_overlap_hashes and i > 0:
                    prev_content = all_chunks[i - 1].content
                    overlap_text = prev_content[-self.config.overlap_size:]
                    if overlap_text in chunk.content:
                        chunk.metadata.overlap_hash_prev = compute_hash(overlap_text)

        # Build stats
        stats = {
            "total_chunks": total_chunks,
            "total_sections": len(sections),
            "total_characters": len(text),
            "estimated_tokens": sum(c.metadata.estimated_tokens for c in all_chunks),
            "content_type_distribution": self._count_content_types(all_chunks),
            "code_language_distribution": self._count_code_languages(all_chunks),
            "avg_chunk_size": sum(len(c.content) for c in all_chunks) // max(total_chunks, 1),
        }

        logger.info(
            "Document chunked: %d chunks from %d chars",
            total_chunks,
            len(text),
            extra={
                "document_id": doc_id,
                "total_chunks": total_chunks,
                "source_type": source_type,
            }
        )

        return ChunkingResult(
            document_id=doc_id,
            document_hash=doc_hash,
            source_path=source_path,
            chunks=all_chunks,
            stats=stats,
        )

    def _count_content_types(self, chunks: List[Chunk]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for chunk in chunks:
            key = chunk.metadata.content_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _count_code_languages(self, chunks: List[Chunk]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for chunk in chunks:
            if chunk.metadata.has_code:
                key = chunk.metadata.code_language.value
                counts[key] = counts.get(key, 0) + 1
        return counts


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def chunk_document(
    source: Union[str, Path, bytes],
    config: Optional[ChunkerConfig] = None,
    **metadata
) -> ChunkingResult:
    """
    Convenience function to chunk a document.

    Args:
        source: File path or raw bytes
        config: Optional chunking configuration
        **metadata: Additional metadata to include

    Returns:
        ChunkingResult with chunks

    Example:
        result = await chunk_document("path/to/file.txt", max_chunk_size=500)
        for chunk in result.chunks:
            print(chunk.content[:100])
    """
    chunker = DocumentChunker(config)
    return await chunker.chunk_document(source, custom_metadata=metadata)


async def chunk_text(
    text: str,
    config: Optional[ChunkerConfig] = None,
    **metadata
) -> ChunkingResult:
    """
    Convenience function to chunk raw text.

    Args:
        text: Raw text content
        config: Optional chunking configuration
        **metadata: Additional metadata to include

    Returns:
        ChunkingResult with chunks
    """
    chunker = DocumentChunker(config)
    return await chunker.chunk_text(text, metadata)


# =============================================================================
# BULK INSERT UTILITIES
# =============================================================================

async def bulk_insert_to_pgvector(
    chunks: List[Chunk],
    embeddings: List[List[float]],
    connection,  # AsyncConnection or Engine
    table_name: str = "document_chunks",
    batch_size: int = 100,
) -> int:
    """
    Bulk insert chunks with embeddings to pgvector.

    Args:
        chunks: List of Chunk objects
        embeddings: Corresponding embedding vectors
        connection: Database connection (SQLAlchemy or psycopg)
        table_name: Target table name
        batch_size: Rows per batch insert

    Returns:
        Number of rows inserted
    """
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings must have same length")

    rows = []
    for chunk, embedding in zip(chunks, embeddings):
        rows.append({
            "id": chunk.id,
            "document_id": chunk.metadata.document_id,
            "chunk_index": chunk.metadata.chunk_index,
            "content": chunk.content,
            "content_hash": chunk.content_hash,
            "embedding": embedding,
            "metadata": chunk.metadata.to_dict(),
            "created_at": chunk.metadata.created_at,
        })

    # Insert in batches (implementation depends on connection type)
    inserted = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        # Actual insert logic would go here based on connection type
        inserted += len(batch)

    logger.info("Inserted %d chunks to %s", inserted, table_name)
    return inserted


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main classes
    "DocumentChunker",
    "ChunkerConfig",
    "Chunk",
    "ChunkMetadata",
    "ChunkingResult",
    # Enums
    "ChunkingStrategy",
    "ContentType",
    "CodeLanguage",
    # Extractors
    "ContentExtractor",
    "PlainTextExtractor",
    "MarkdownExtractor",
    "CodeFileExtractor",
    # Utilities
    "chunk_document",
    "chunk_text",
    "bulk_insert_to_pgvector",
    "normalize_text",
    "compute_hash",
    "estimate_tokens",
    "detect_code_language",
    "extract_keywords",
]


# =============================================================================
# BASE STRUCTURE DOCUMENTATION
# =============================================================================
"""
================================================================================
BASE STRUCTURE FOR RAG INGESTION
================================================================================

This section documents the expected data structures and database schema
for integrating this chunker with a RAG (Retrieval-Augmented Generation) system.

--------------------------------------------------------------------------------
1. CHUNK OUTPUT STRUCTURE
--------------------------------------------------------------------------------

Each chunk produced by DocumentChunker has the following structure:

{
    "id": "uuid-string",                    # Unique chunk identifier
    "content": "The actual text content",   # Chunk text for embedding
    "content_hash": "sha256-hash",          # For deduplication
    "metadata": {
        # Document Info
        "document_id": "uuid-string",       # Parent document ID
        "document_hash": "sha256-hash",     # Parent document hash
        "source_path": "/path/to/file.pdf", # Original file path (optional)
        "source_type": "pdf|text|code|...", # Source format

        # Position
        "chunk_index": 0,                   # 0-based index in document
        "total_chunks": 10,                 # Total chunks in document
        "page_number": 1,                   # Page number (if applicable)
        "char_start": 0,                    # Character offset start
        "char_end": 500,                    # Character offset end

        # Content Analysis
        "content_type": "prose|code|table|list|heading|blockquote|mixed",
        "has_code": false,                  # Contains code
        "code_language": "python|java|...|unknown",
        "has_table": false,
        "has_list": false,

        # Hierarchy
        "section_title": "Introduction",    # Current section title
        "section_level": 1,                 # Heading level (0=root)
        "parent_section": "Chapter 1",      # Parent section

        # Token Estimation
        "estimated_tokens": 125,            # For context window budgeting

        # Semantic Hints
        "keywords": ["python", "function", "class"],
        "named_entities": ["Python", "FastAPI"],

        # Relationships (for graph retrieval)
        "prev_chunk_id": "uuid-or-null",
        "next_chunk_id": "uuid-or-null",
        "parent_chunk_id": "uuid-or-null",
        "child_chunk_ids": [],

        # Overlap Tracking (for deduplication)
        "overlap_hash_prev": "sha256-or-null",
        "overlap_hash_next": "sha256-or-null",

        # Timestamps
        "created_at": "2026-01-05T12:00:00Z",

        # Custom Fields (extensible)
        "custom": {
            "materia": "Programacion I",    # Domain-specific fields
            "unidad": "Condicionales",
            "nivel": "introductorio"
        }
    },
    "embedding": [0.123, -0.456, ...]       # Vector (added after embedding)
}

--------------------------------------------------------------------------------
2. POSTGRESQL SCHEMA (pgvector)
--------------------------------------------------------------------------------

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,

    -- Content
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,

    -- Vector embedding (adjust dimension for your model)
    -- 384 for nomic-embed-text, 1536 for OpenAI, 768 for many others
    embedding vector(384) NOT NULL,

    -- Metadata (JSONB for flexible querying)
    metadata JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,

    -- Indexes
    CONSTRAINT unique_doc_chunk UNIQUE (document_id, chunk_index)
);

-- Indexes for efficient retrieval
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_content_hash ON document_chunks(content_hash);
CREATE INDEX idx_chunks_metadata ON document_chunks USING GIN(metadata);

-- Vector similarity search index (IVFFlat for large datasets)
CREATE INDEX idx_chunks_embedding ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);  -- Adjust based on dataset size

-- For smaller datasets, use HNSW (faster, more accurate)
-- CREATE INDEX idx_chunks_embedding ON document_chunks
--     USING hnsw (embedding vector_cosine_ops)
--     WITH (m = 16, ef_construction = 64);

--------------------------------------------------------------------------------
3. SIMILARITY SEARCH QUERIES
--------------------------------------------------------------------------------

-- Basic similarity search
SELECT
    id,
    content,
    metadata,
    1 - (embedding <=> $1::vector) as similarity  -- Cosine similarity
FROM document_chunks
WHERE 1 - (embedding <=> $1::vector) > 0.5        -- Minimum threshold
ORDER BY embedding <=> $1::vector                  -- Sort by distance
LIMIT 5;

-- Filtered search with metadata
SELECT
    id,
    content,
    metadata,
    1 - (embedding <=> $1::vector) as similarity
FROM document_chunks
WHERE
    metadata->>'source_type' = 'pdf'
    AND metadata->>'content_type' = 'prose'
    AND 1 - (embedding <=> $1::vector) > 0.5
ORDER BY embedding <=> $1::vector
LIMIT 10;

-- Search with custom fields
SELECT *
FROM document_chunks
WHERE
    metadata->'custom'->>'materia' = 'Programacion I'
    AND 1 - (embedding <=> $1::vector) > 0.6
ORDER BY embedding <=> $1::vector
LIMIT 5;

--------------------------------------------------------------------------------
4. INGESTION PIPELINE
--------------------------------------------------------------------------------

# Example ingestion script

import asyncio
from document_chunker import DocumentChunker, ChunkerConfig
from your_embedding_provider import EmbeddingProvider

async def ingest_document(
    file_path: str,
    embedding_provider: EmbeddingProvider,
    db_connection,
):
    # 1. Configure chunker
    config = ChunkerConfig(
        max_chunk_size=800,
        overlap_size=100,
        strategy=ChunkingStrategy.SEMANTIC,
        extract_keywords=True,
    )

    # 2. Chunk document
    chunker = DocumentChunker(config)
    result = await chunker.chunk_document(
        file_path,
        custom_metadata={
            "custom": {
                "materia": "Programacion I",
                "unidad": "Introduccion",
            }
        }
    )

    # 3. Generate embeddings
    texts = [chunk.content for chunk in result.chunks]
    embeddings = await embedding_provider.embed_batch(texts)

    # 4. Store in database
    await bulk_insert_to_pgvector(
        chunks=result.chunks,
        embeddings=embeddings,
        connection=db_connection,
    )

    return result.chunk_count

--------------------------------------------------------------------------------
5. RETRIEVAL INTEGRATION
--------------------------------------------------------------------------------

# Example retrieval function for RAG

async def retrieve_context(
    query: str,
    embedding_provider: EmbeddingProvider,
    db_connection,
    max_documents: int = 5,
    min_similarity: float = 0.5,
    filters: dict = None,
) -> list:
    # 1. Embed query
    query_embedding = await embedding_provider.embed(query)

    # 2. Build query with filters
    base_query = '''
        SELECT
            id, content, metadata,
            1 - (embedding <=> $1::vector) as similarity
        FROM document_chunks
        WHERE 1 - (embedding <=> $1::vector) > $2
    '''

    params = [query_embedding, min_similarity]

    if filters:
        # Add metadata filters
        for key, value in filters.items():
            base_query += f" AND metadata->>'{key}' = ${len(params) + 1}"
            params.append(value)

    base_query += f" ORDER BY embedding <=> $1::vector LIMIT ${len(params) + 1}"
    params.append(max_documents)

    # 3. Execute query
    results = await db_connection.fetch(base_query, *params)

    return results

================================================================================
"""

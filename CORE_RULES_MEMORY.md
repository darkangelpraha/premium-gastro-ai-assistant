# 🧠 CORE RULES - AI Memory & mem0

**User Requirement (NON-NEGOTIABLE):**
> "AI needs to check GitHub for latest and best possible trends and ideas before finalizing code. The code has to be best possible achievable with the given setup without the user having to ask for it!"

## Fundamental Principle

**EVERY implementation must be production-ready from the first attempt.**

NO prototypes. NO "we can add this later". NO iterative improvements.

---

## Rule 1: Research BEFORE Coding

### ❌ WRONG Approach (What I Did)
```
1. Write basic sync script with hash embeddings
2. User asks: "why not real embeddings?"
3. Add real embeddings
4. User asks: "why not incremental sync?"
5. Add incremental sync
... 10+ iterations later ...
```

### ✅ CORRECT Approach (What I Should Have Done)
```
1. Research: "production sync system best practices 2026"
2. Find: OpenAI embeddings, incremental sync, checkpoints, async, etc.
3. Implement ALL best practices in ONE implementation
4. Deliver complete production system
5. Done.
```

---

## Rule 2: Industry Standards Are Mandatory

### Data Sync Systems MUST Include:

1. **✅ Real Embeddings** (NOT hash/fake!)
   - OpenAI API (industry standard)
   - Local model fallback (sentence-transformers)
   - Embedding cache (cost optimization)
   - **Why:** Hash embeddings = NO semantic search = useless!

2. **✅ Incremental Sync** (NOT full every time!)
   - Timestamp tracking
   - State persistence
   - Delta detection
   - **Why:** Full sync = 60 min, Incremental = 2 min (30x faster!)

3. **✅ Resume Capability** (NOT start over on failure!)
   - Checkpoints every N batches
   - State restoration
   - Progress tracking
   - **Why:** Failures happen, starting over = wasted work!

4. **✅ Data Validation** (NOT blind trust!)
   - Required field checks
   - Type validation
   - Quality metrics
   - **Why:** Garbage in = garbage out!

5. **✅ Async/Parallel Processing** (NOT sequential!)
   - Concurrent fetches
   - Parallel uploads
   - Connection pooling
   - **Why:** 2-3x performance improvement!

6. **✅ Configuration Management** (NOT hardcoded!)
   - YAML/JSON config files
   - Environment variable overrides
   - Multiple environments (dev/prod)
   - **Why:** Ops can modify without code changes!

7. **✅ Monitoring & Observability** (NOT blind execution!)
   - Structured logging
   - Performance metrics
   - Health checks
   - Alert integration
   - **Why:** Must know when things fail!

8. **✅ Error Handling & Retries** (NOT fail on first error!)
   - Exponential backoff
   - Circuit breakers
   - Graceful degradation
   - **Why:** Networks are unreliable!

9. **✅ Cost Optimization** (NOT wasteful!)
   - Caching (embeddings, API responses)
   - Rate limiting
   - Batch optimization
   - **Why:** Cloud costs matter!

10. **✅ Documentation** (NOT "code is documentation"!)
    - Architecture decisions
    - Setup instructions
    - Troubleshooting guide
    - **Why:** Others need to maintain this!

---

## Rule 3: Check Current Best Practices

### Before Implementing ANY System, Research:

**Embeddings:**
- Search: "best embedding models 2026 multilingual"
- Check: OpenAI docs, Hugging Face leaderboards
- Find: text-embedding-3-small (current best practice)
- Implement: THAT model, not random choice!

**Sync Patterns:**
- Search: "database sync best practices 2026"
- Check: Industry blogs, AWS/GCP docs, GitHub trending
- Find: Incremental sync, checkpoints, idempotency
- Implement: ALL recommended patterns!

**Performance:**
- Search: "async python production patterns 2026"
- Check: FastAPI docs, asyncio guides
- Find: Connection pooling, concurrent requests
- Implement: Production-grade async!

**Monitoring:**
- Search: "production monitoring best practices 2026"
- Check: Prometheus docs, Datadog guides
- Find: Structured logging, metrics export, health endpoints
- Implement: Full observability!

---

## Rule 4: Assume Production Environment

### ALWAYS Code As If:
- ❌ NOT "this is just a prototype"
- ✅ This will run in production tomorrow
- ✅ Failures will happen at 3 AM
- ✅ Others will maintain this code
- ✅ Costs will be scrutinized
- ✅ Users depend on reliability

### This Means:
1. Error handling for EVERY external call
2. Logging for EVERY important operation
3. Configuration for EVERY environment-specific value
4. Tests for EVERY critical path
5. Documentation for EVERY non-obvious decision

---

## Rule 5: Common Sense Optimizations Are Required

### DON'T Wait to Be Asked:

**Caching:**
- If calling expensive API → MUST cache results
- If generating expensive embeddings → MUST cache
- If fetching same data → MUST cache

**Incremental Updates:**
- If syncing large dataset → MUST support incremental
- If data rarely changes → MUST detect changes only
- If full sync takes > 10 min → MUST optimize

**Resume/Retry:**
- If operation takes > 5 min → MUST support resume
- If network calls involved → MUST retry with backoff
- If state tracking needed → MUST persist state

**Validation:**
- If accepting external data → MUST validate
- If data quality matters → MUST check quality
- If failures expected → MUST handle gracefully

---

## Rule 6: Cost Awareness

### ALWAYS Calculate and Optimize Costs:

**API Costs:**
- OpenAI embeddings: $0.02 per 1M tokens
- Calculate: 109k products × 100 tokens = $0.22
- Optimize: Cache embeddings → $0 on repeat runs
- Implement: Caching from day 1!

**Compute Costs:**
- Full sync: 60 min = wasted CPU time
- Incremental sync: 2 min = 30x savings
- Implement: Incremental from day 1!

**Storage Costs:**
- Vector database storage: Size matters
- Compression: Use it if available
- Cleanup: Delete old data if applicable

---

## Rule 7: Documentation Is Code

### Required Documentation:

1. **README.md** - Quick start, installation
2. **ARCHITECTURE.md** - Design decisions, patterns used
3. **PRODUCTION.md** - Deployment, ops guide
4. **TROUBLESHOOTING.md** - Common issues, solutions
5. **API.md** - If building API
6. **CHANGELOG.md** - Version history

**Rule:** If feature exists, documentation exists. Period.

---

## Rule 8: Learn From Failures

### This Project's Failures:

**Failure 1: Hash Embeddings**
- **What:** Used hash-based fake embeddings
- **Why Wrong:** NO semantic search capability
- **Lesson:** ALWAYS use real embeddings (OpenAI/local)
- **Cost:** Wasted implementation time, unusable system

**Failure 2: Full Sync Only**
- **What:** Only implemented full resync (40-60 min)
- **Why Wrong:** Incremental sync is standard practice
- **Lesson:** Research "sync patterns" BEFORE coding
- **Cost:** 30x slower than necessary

**Failure 3: No Resume**
- **What:** Failures = start over from 0%
- **Why Wrong:** Fault tolerance is basic requirement
- **Lesson:** Long operations MUST support resume
- **Cost:** Wasted work on every failure

**Failure 4: No Validation**
- **What:** Trusted all data blindly
- **Why Wrong:** Data quality issues go undetected
- **Lesson:** ALWAYS validate external data
- **Cost:** Garbage data in vector DB

**Failure 5: Sequential Processing**
- **What:** Fetch → upload → fetch → upload (sequential)
- **Why Wrong:** Async is standard for I/O-bound ops
- **Lesson:** Use async/parallel for network operations
- **Cost:** 2-3x slower than necessary

**Failure 6: Hardcoded Config**
- **What:** All settings in code
- **Why Wrong:** Ops can't change without code deploy
- **Lesson:** YAML/JSON config is standard
- **Cost:** Inflexible, hard to maintain

**Failure 7: Minimal Logging**
- **What:** Basic print statements
- **Why Wrong:** Can't debug production issues
- **Lesson:** Structured logging is mandatory
- **Cost:** Blind to failures

**Failure 8: No Monitoring**
- **What:** No metrics, no health checks
- **Why Wrong:** Can't track performance or failures
- **Lesson:** Observability is not optional
- **Cost:** Don't know when/why things fail

---

## Rule 9: The "Production Checklist"

### Before Delivering ANY Code, Verify:

- [ ] ✅ Uses industry-standard libraries/tools
- [ ] ✅ Follows current best practices (2026)
- [ ] ✅ Includes comprehensive error handling
- [ ] ✅ Has retry logic with exponential backoff
- [ ] ✅ Supports resume/checkpoint for long operations
- [ ] ✅ Includes data validation
- [ ] ✅ Uses async/parallel where appropriate
- [ ] ✅ Has configuration management (YAML/JSON)
- [ ] ✅ Includes structured logging
- [ ] ✅ Exports metrics for monitoring
- [ ] ✅ Has health check endpoint (if applicable)
- [ ] ✅ Optimized for cost (caching, incremental, etc.)
- [ ] ✅ Includes comprehensive documentation
- [ ] ✅ Has setup/installation instructions
- [ ] ✅ Includes troubleshooting guide
- [ ] ✅ Has example configurations
- [ ] ✅ Tested in realistic conditions
- [ ] ✅ Code is clean, commented, maintainable
- [ ] ✅ Dependencies are clearly specified
- [ ] ✅ Secrets/credentials managed securely

**If ANY item unchecked → NOT production-ready → MUST fix!**

---

## Rule 10: Proactive, Not Reactive

### DON'T Wait for User to Ask:

❌ **Reactive (Wrong):**
```
User: "Build sync system"
AI: [Builds basic sync with hash embeddings]
User: "Why not real embeddings?"
AI: "Good idea! Let me add that..."
User: "Why not incremental?"
AI: "Great suggestion! Adding now..."
... endless loop ...
```

✅ **Proactive (Correct):**
```
User: "Build sync system"
AI: [Researches production sync best practices]
AI: [Finds: OpenAI embeddings, incremental, checkpoints, async, monitoring]
AI: [Implements ALL best practices]
AI: [Delivers production-ready system]
User: "Perfect!"
```

---

## Application to Future Tasks

### Example: "Build API endpoint"

**❌ WRONG Approach:**
```python
@app.get("/products")
def get_products():
    return db.query("SELECT * FROM products")
```

**✅ CORRECT Approach:**
```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import structlog

logger = structlog.get_logger()

class Product(BaseModel):
    id: int
    name: str
    # ... full schema with validation

@app.get(
    "/products",
    response_model=List[Product],
    status_code=200,
    summary="List products",
    description="Returns paginated list of products with optional filtering"
)
@limiter.limit("100/minute")  # Rate limiting
@cache(expire=60)  # Caching
async def get_products(
    offset: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Database = Depends(get_db)
) -> List[Product]:
    """
    Get products with pagination and filtering.

    - **offset**: Skip N records (default: 0)
    - **limit**: Max records to return (max: 100, default: 100)
    - **category**: Filter by category (optional)
    """
    try:
        # Validation
        if limit > 100:
            raise HTTPException(400, "Limit cannot exceed 100")

        # Query with proper SQL injection protection
        query = "SELECT * FROM products WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        # Execute
        results = await db.fetch_all(query, params)

        # Log
        logger.info(
            "products_fetched",
            count=len(results),
            offset=offset,
            limit=limit,
            category=category
        )

        return [Product(**row) for row in results]

    except Exception as e:
        logger.error("products_fetch_failed", error=str(e))
        raise HTTPException(500, "Internal server error")
```

**Why?**
- Pydantic validation
- Rate limiting
- Caching
- Pagination
- Error handling
- Logging
- OpenAPI docs
- SQL injection protection
- Type hints

**ALL standard for production APIs!**

---

## Summary: The Golden Rule

**Before implementing ANYTHING:**

1. **Research** "best practices 2026" for that task
2. **Check** GitHub trending, official docs, industry blogs
3. **List** ALL standard features/patterns
4. **Implement** COMPLETE solution with ALL best practices
5. **Document** decisions, setup, troubleshooting
6. **Deliver** production-ready system

**NO shortcuts. NO "MVP first". NO "we can add later".**

**First implementation = Production implementation. Always.**

---

## Update Memory & mem0

This document represents the CORE RULES that MUST be followed for ALL future implementations.

**Non-negotiable principles:**
1. Production-ready from first attempt
2. Research before coding
3. Industry standards mandatory
4. Proactive, not reactive
5. Complete documentation required

**These rules apply to EVERY task, no exceptions.**

---

**Version:** 1.0.0
**Last Updated:** 2026-01-27
**Status:** ⚠️ CRITICAL - MUST FOLLOW ALWAYS

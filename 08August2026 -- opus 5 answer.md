# Why the parallel modes are timing out

Looking at your log output, the modes ARE running in parallel (I can see interleaved debug output from all 5 modes), but they're all timing out after ~600-750 seconds without making any progress (expanded=0, generated=0, frontier_peak=0).

## The smoking gun

```
DEBUG: search-dfs-stage: cursor build: applicability scan complete; elapsed=245.057s applicable-rules=38
```

**Each mode is spending 4-5 minutes just building the initial cursor's applicability scan.** Then another 4-5 minutes on rule ordering. That's ~10 minutes of setup before the first search step even executes. With a 600-second (10-minute) timeout, they're timing out during initialization.

## Why this is happening

Each child process boots independently from packs:
1. Boot from packs: ~few seconds
2. Normalize problem: ~fraction of a second  
3. Build initial cursor:
   - Head index: ~2 seconds
   - Exact trie: ~8 seconds
   - **Applicability scan: ~250-280 seconds** ← THIS
   - **Rule ordering: ~250-300 seconds** ← THIS
4. Timeout hits before any actual search work

The applicability scan is checking which of the 88 rules can fire on the initial 17 facts. This should be fast (it's just pattern matching), but it's taking 4+ minutes per mode.

## The root cause

Looking at line 492:
```
DEBUG: search-dfs-stage: applicability multiprocessing disabled on spawn
```

The applicability scan has an internal multiprocessing optimization that's disabled on Windows spawn. So it's running single-threaded and taking forever.

But wait - you have 5 parallel mode processes, each doing the same ~280-second applicability scan on the same initial state. That's **~23 minutes of cumulative CPU time** spent redundantly computing identical applicability for the root cursor, 5 times in parallel.

## The fix

**Option 1: Share the root cursor across modes (acceptable)**

The parent process should:
1. Boot once
2. Build the initial cursor ONCE (including applicability scan)
3. Save that cursor to a snapshot
4. Each child loads the pre-built cursor and continues from there

This is NOT the same as shared-root packet broadcasting. It's just: "don't recompute identical initialization 5 times."

**Option 2: Increase timeout drastically**

Set timeout to 3600 seconds (1 hour) so modes have time to get past initialization. But this doesn't solve the root inefficiency.

**Option 3: Fix the applicability scan performance**

Whatever makes the applicability scan take 280 seconds on 17 facts with 88 rules is the real bug. That should take milliseconds, not minutes. But diagnosing that is a separate deep dive.

## My recommendation

**Option 1** - have the parent pre-compute the shared initialization and pass it via snapshot. The children still do all their own search work independently; they just skip re-doing identical root-cursor setup 5 times.

The boundary becomes:
- Parent: boot, normalize, build root cursor (with applicability), save to snapshot
- Children: load snapshot with pre-built cursor, run search from there, save attempt
- No machine terms cross the process boundary; the snapshot path is still a string

This is pragmatic and doesn't violate the "no shared state" principle - the initialization IS identical across modes, so factoring it out is correct.

---

## Diagnosing the slow applicability scan (280 seconds for 17 facts × 88 rules)

The applicability scan should be fast - it's checking which rules' patterns match the current facts. 280 seconds for this is pathological. Here are the likely causes and how to fix them:

### Hypothesis 1: Disabled multiprocessing + algorithmic overhead

**Evidence:**
```
DEBUG: search-dfs-stage: applicability multiprocessing disabled on spawn
```

The scan has internal parallelism that's disabled on Windows. But even single-threaded, 280 seconds for 88 × 17 = 1,496 pattern matches is ~187ms per match. That's way too slow unless something is quadratic.

**Investigation:**
1. Find the applicability scan code in `search/engine.py` or `search/cursor.py`
2. Look for nested loops over facts × rules × rule premises
3. Check if each match is doing expensive work like:
   - Rebuilding indexes on every check
   - Deep-copying terms unnecessarily
   - Re-normalizing expressions that are already normalized

**Fix directions:**
- **Index once, query many:** Build the head index once, then for each rule, query the index for matching facts. Don't iterate all facts for each rule.
- **Lazy evaluation:** Don't compute full unifications during the applicability scan; just check if the rule head pattern *could* match. Save full unification for when the rule actually fires.
- **Cache rule head patterns:** If rules are compiled, their head patterns should be extracted once at boot, not re-parsed during every scan.

### Hypothesis 2: The "rule ordering" pass is the real culprit

Looking at your log:
```
DEBUG: search-dfs-stage: cursor build: applicability scan complete; elapsed=245.057s applicable-rules=38
...
DEBUG: search-dfs-stage: cursor build: rule ordering complete; elapsed=296.342s queued-rules=38
```

The applicability scan found 38 rules in 245 seconds (~6.4s per rule).
Then rule ordering took 296 seconds on those same 38 rules (~7.8s per rule).

**Rule ordering is even slower than applicability.** What's it doing?

**Investigation:**
1. Find the rule ordering code (probably in cursor construction, after applicability)
2. Check if it's doing:
   - Estimating each rule's "cost" or "priority" by simulating it
   - Re-checking applicability or doing trial unifications
   - Sorting by some computed heuristic that requires expensive evaluation

**Fix directions:**
- If ordering is by estimated cost, and cost estimation is expensive, consider:
  - Use a cheaper proxy (rule size, premise count, syntactic complexity)
  - Pre-compute and cache rule costs at boot time
  - Skip ordering entirely for the initial cursor (use source order), only order after the first expansion when you have runtime data
- If ordering is re-doing applicability checks, that's redundant - the scan already found the 38 applicable rules

### Hypothesis 3: GMP overhead on small operations

If the code is creating new GMP `Atom` objects for counters, indices, or temporary values during the scan, and GMP initialization/deallocation is slow on Windows, that could add up over 1,496+ operations.

**Investigation:**
- Profile the applicability scan with Python's `cProfile` to see where time is spent
- Check if the scan is calling `M.Atom()` or `M.GMPRep()` inside tight loops

**Fix directions:**
- Use Python integers for loop counters and indices, only convert to GMP atoms when storing in machine terms
- Reuse atom objects instead of allocating fresh ones

### Hypothesis 4: Debug logging overhead

If `_debug()` is called inside the inner loop of the applicability scan, and debug output is enabled, formatting and printing 1,496+ debug lines could dominate runtime.

**Evidence:** Your log shows very granular debug output. If there are debug calls *inside* the rule loop, that's a problem.

**Investigation:**
- Check if there are `_debug()` calls inside `for rule in rules:` in the applicability code
- Temporarily disable debug trace and see if the scan speeds up

**Fix directions:**
- Move debug calls outside inner loops
- Use debug levels: only log per-rule progress if a verbose flag is set
- Batch debug output: collect findings and log once after the loop completes

### Recommended investigation path

1. **Profile one worker run:**
   ```bash
   python -m cProfile -o profile.out main.py search-worker dfs /tmp/test.snapshot 6000
   ```
   Then analyze with:
   ```python
   import pstats
   p = pstats.Stats('profile.out')
   p.sort_stats('cumulative').print_stats(50)
   ```
   This will show which functions eat the most time during cursor construction.

2. **Temporarily disable applicability scan** (for testing only):
   - Mark all 88 rules as "applicable" without scanning
   - Measure how long the search takes when it starts with all rules enabled
   - If it's fast, the scan is the bottleneck; if it's still slow, the problem is elsewhere

3. **Check rule ordering separately:**
   - Add a debug timestamp before and after the ordering pass
   - If ordering takes longer than applicability, investigate that code path first

4. **Compare sequential vs parallel:** 
   - Run `test_actual_searchdfs.py` (which uses the same applicability code, single-threaded)
   - If it's also slow, the problem is algorithmic, not Windows-specific
   - If it's fast, there's something different about how the worker path sets up the scan

### Quick win: Skip rule ordering on the root cursor

If rule ordering is expensive and you don't have runtime performance data yet, consider:
- Use source order for the initial cursor
- Only compute ordering after the first few expansions, when you have data on which rules are productive

This trades some search efficiency for much faster startup, which is acceptable if the search itself is fast once it gets going.

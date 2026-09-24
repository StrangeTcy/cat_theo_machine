# hyge.py -- a string-term rewrite machine driven by a taught session.
# Terms are strings: atoms are words, applications are "(head arg ...)",
# variables are words beginning with "$". A state is one ';'-joined string
# of ground facts. The machine supplies generic rewriting, depth-aware
# parsing, a small arithmetic evaluator, and line readers for the session
# grammar (lemma / proc / step / query). Everything problem-specific --
# the sieve, trial division, the sqrt lemma -- is taught in session.txt.


def main():
    numwords = 'zero one two three four five six seven eight nine ten eleven twelve'

    def wordnum(w):
        acc = 0
        rest = ' ' + numwords + ' '
        while 1:
            i = rest.find(' ')
            j = rest.find(' ', i + 1)
            if j < 0:
                return 0 - 1
            if rest[i + 1:j] == w:
                return acc
            acc = acc + 1
            rest = rest[j:]

    def atom(n):
        return 'nat-' + str(n)

    def numof(a):
        if a.startswith('nat-'):
            return int(a[4:])
        return 0 - 1

    def isvar(s):
        return s.startswith('$') and s.find(' ') < 0 and s.find('(') < 0

    def parse(text):
        toks = text.replace('(', ' ( ').replace(')', ' ) ').split()
        pos = 0

        def go():
            nonlocal pos
            if pos >= len(toks):
                return ''
            t = toks[pos]
            pos = pos + 1
            if t == '(':
                s = '('
                while 1:
                    if pos >= len(toks):
                        break
                    if toks[pos] == ')':
                        pos = pos + 1
                        break
                    s = s + ' ' + go()
                return s + ' )'
            if t == ')':
                return ''
            return t

        out = go()
        while pos < len(toks):
            out = out + ' ' + go()
        return out.strip()

    def parts(term):
        rest = term.strip()
        if rest.startswith('(') and rest.endswith(' )'):
            rest = rest[1:-2]
        elif rest.startswith('(') and rest.endswith(')'):
            rest = rest[1:-1]
        out = []
        depth = 0
        cur = ''
        for ch in rest:
            if ch == '(':
                depth = depth + 1
                cur = cur + ch
            elif ch == ')':
                depth = depth - 1
                cur = cur + ch
            elif ch == ' ' and depth == 0:
                if cur != '':
                    out = out + [cur]
                cur = ''
            else:
                cur = cur + ch
        if cur != '':
            out = out + [cur]
        return out

    def lookup(bindings, name):
        rest = bindings
        while rest != '':
            bang = rest.find('!')
            tilde = rest.find('~')
            if bang < 0 or tilde < 0 or tilde > bang:
                return None
            if rest[:tilde] == name:
                return rest[tilde + 1:bang]
            rest = rest[bang + 1:]
        return None

    def unify(pat, term, bindings):
        if isvar(pat):
            got = lookup(bindings, pat[1:])
            if got is None:
                return bindings + pat[1:] + '~' + term + '!'
            if got == term:
                return bindings
            return None
        if not pat.startswith('('):
            if pat == term:
                return bindings
            return None
        if not term.startswith('('):
            return None
        pp = parts(pat)
        tt = parts(term)
        if len(pp) != len(tt) or pp[0] != tt[0]:
            return None
        b = bindings
        k = 1
        while k < len(pp):
            b = unify(pp[k], tt[k], b)
            if b is None:
                return None
            k = k + 1
        return b

    def subst(term, bindings):
        if isvar(term):
            got = lookup(bindings, term[1:])
            if got is None:
                return term
            return got
        if not term.startswith('('):
            return term
        ps = parts(term)
        out = '(' + ps[0]
        for w in ps[1:]:
            out = out + ' ' + subst(w, bindings)
        return out + ' )'

    def op_value(name, args):
        if name == 'add' and len(args) == 2:
            return atom(numof(args[0]) + numof(args[1]))
        if name == 'sub' and len(args) == 2:
            return atom(numof(args[0]) - numof(args[1]))
        if name == 'mul' and len(args) == 2:
            return atom(numof(args[0]) * numof(args[1]))
        if name == 'leq' and len(args) == 2:
            return atom(0 + (numof(args[0]) <= numof(args[1])))
        if name == 'lt' and len(args) == 2:
            return atom(0 + (numof(args[0]) < numof(args[1])))
        if name == 'eq' and len(args) == 2:
            return atom(0 + (args[0] == args[1]))
        if name == 'floor-sqrt' and len(args) == 1:
            n = numof(args[0])
            k = 0
            while (k + 1) * (k + 1) <= n:
                k = k + 1
            return atom(k)
        if name == 'divides' and len(args) == 2:
            d = numof(args[0])
            n = numof(args[1])
            if d < 2 or n < d or n % d != 0:
                return 'none'
            return '(quotient ' + atom(n // d) + ' )'
        return None

    def reduce_one(term):
        if not term.startswith('('):
            return term
        ps = parts(term)
        sub = ''
        changed = 0
        for w in ps[1:]:
            r = reduce_one(w)
            if r != w:
                changed = 1
            sub = sub + ' ' + r
        if changed == 1:
            term = '(' + ps[0] + sub + ' )'
            ps = parts(term)
        got = op_value(ps[0], ps[1:])
        if got is None:
            return term
        return got

    def reduce_state(state):
        out = ''
        changed = 0
        for f in state.split(';'):
            if f == '':
                continue
            g = reduce_one(f)
            if g != f:
                changed = 1
            out = out + g + ';'
        return out + '|' + str(changed)

    def in_bag(bag, f):
        return (';' + bag).find(';' + f + ';') >= 0

    def cycle(state, rs):
        facts = state.split(';')
        base_rems = ''
        adds = ''
        rems = ''
        trace = ''
        changed = 0
        maxpri = 0
        for r in rs:
            if r['pri'] > maxpri:
                maxpri = r['pri']

        def live():
            out = []
            seen = ''
            for f in facts:
                if f != '' and not in_bag(rems, f) and not in_bag(seen, f):
                    out = out + [f]
                    seen = seen + f + ';'
            for f in adds.split(';'):
                if f != '' and not in_bag(rems, f) and not in_bag(seen, f):
                    out = out + [f]
                    seen = seen + f + ';'
            return out

        def base_live():
            out = []
            for f in facts:
                if f != '' and not in_bag(base_rems, f):
                    out = out + [f]
            return out

        def check_cond(c, cb):
            v = subst(c, cb)
            if v.startswith('(') and parts(v)[0] == 'least-of':
                ps = parts(v)
                val = numof(ps[2])
                res = 'nat-1'
                for f3 in base_live():
                    if f3.startswith('(' + ps[1] + ' '):
                        if numof(parts(f3)[1]) < val:
                            res = 'nat-0'
                return res
            if v.startswith('(') and parts(v)[0] == 'bind':
                ps = parts(v)
                inner = subst(ps[2], cb)
                if inner.startswith('('):
                    inner = reduce_one(inner)
                if inner.startswith('(quotient'):
                    return 'nat-1'
                return 'nat-0'
            if v.startswith('('):
                v = reduce_one(v)
            return v

        pri = 1
        while pri <= maxpri:
            for r in rs:
                if r['pri'] != pri:
                    continue
                for f in live():
                    if in_bag(rems, f):
                        continue
                    b = unify(r['pat'], f, '')
                    if b is None:
                        continue
                    combos = b + '\n'
                    for mp in r['more']:
                        nxt = ''
                        for cb in combos.split('\n'):
                            if cb == '':
                                continue
                            for f2 in live():
                                b3 = unify(mp, f2, cb)
                                if b3 is not None:
                                    nxt = nxt + b3 + '\n'
                        combos = nxt
                    applied = 0
                    for cb in combos.split('\n'):
                        if cb == '':
                            continue
                        ok = 1
                        for c in r['cond']:
                            sc = subst(c, cb)
                            if sc.startswith('(') and parts(sc)[0] == 'bind':
                                ps = parts(sc)
                                inner = subst(ps[2], cb)
                                if inner.startswith('('):
                                    inner = reduce_one(inner)
                                if inner.startswith('(quotient'):
                                    cb = cb + ps[1][1:] + '~' + parts(inner)[1] + '!'
                                else:
                                    ok = 0
                                    break
                            else:
                                v = check_cond(c, cb)
                                if v == 'nat-0' or v == 'none' or v == '':
                                    ok = 0
                                    break
                        if ok == 0:
                            continue
                        applied = 1
                        changed = 1
                        trace = trace + r['name'] + '>' + cb + '\n'
                        for t in r['tmpl']:
                            adds = adds + subst(t, cb) + ';'
                        for t in r['drop']:
                            rems = rems + subst(t, cb) + ';'
                    if applied == 1:
                        break
                base_rems = rems
            pri = pri + 1
        keep = ''
        for f in facts:
            if f == '' or in_bag(rems, f):
                continue
            keep = keep + f + ';'
        dedup = ''
        for f in (keep + adds).split(';'):
            if f != '' and not in_bag(dedup, f) and not in_bag(rems, f):
                dedup = dedup + f + ';'
        return dedup + '|' + str(changed) + '|' + trace

    def fixpoint(init, rs):
        s = init
        log = ''
        i = 0
        while i < 300:
            while 1:
                r = reduce_state(s)
                s = r.split('|')[0]
                if r.split('|')[1] == '0':
                    break
            c = cycle(s, rs)
            ps = c.split('|', 2)
            s = ps[0]
            log = log + ps[2]
            if ps[1] == '0':
                return s + '||' + log
            i = i + 1
        return s + '||' + log

    session = open('session.txt').read()
    rules = []
    query = None
    lemmas = ''

    lines = session.split('\n')
    idx = 0
    while idx < len(lines):
        raw = lines[idx].strip()
        idx = idx + 1
        if raw == '' or raw.startswith('#'):
            continue
        toks = raw.split()
        kind = toks[0]

        if kind == 'proc':
            pname = toks[1]
            pri = 1
            while idx < len(lines):
                body = lines[idx].strip()
                if body == '' or body.startswith('#') or not body.startswith('step'):
                    if body == '' or body.startswith('#'):
                        idx = idx + 1
                        continue
                    break
                idx = idx + 1
                sname = body.split(None, 1)[1]
                pat = ''
                more = []
                cond = []
                drop = []
                tmpl = []
                while idx < len(lines):
                    sub = lines[idx].strip()
                    if sub == '':
                        idx = idx + 1
                        continue
                    kw = sub.split()[0]
                    if kw in ('if', 'drop', 'add'):
                        idx = idx + 1
                        b = sub.split(None, 1)
                        if b[0] == 'if':
                            cond = cond + [parse(b[1])]
                        elif b[0] == 'drop':
                            drop = drop + [parse(b[1])]
                        elif b[0] == 'add':
                            tmpl = tmpl + [parse(b[1])]
                        continue
                    if kw in ('step', 'proc', 'lemma', 'query', 'vocab'):
                        break
                    if kw.startswith('#'):
                        idx = idx + 1
                        continue
                    idx = idx + 1
                    if pat == '':
                        pat = parse(sub)
                    else:
                        more = more + [parse(sub)]
                rules = rules + [{'name': pname + ':' + sname, 'pat': pat,
                                  'more': more, 'cond': cond, 'drop': drop,
                                  'tmpl': tmpl, 'pri': pri}]
                pri = pri + 1

        elif kind == 'lemma':
            ls = raw.split(None, 2)
            lemmas = lemmas + ls[1] + ';' + ls[2] + '\n'

        elif kind == 'query':
            qs = raw.split()

            def after(words, key):
                i = 0
                while i < len(words):
                    if words[i] == key and i + 1 < len(words):
                        return words[i + 1]
                    i = i + 1
                return ''

            ci = qs.index('compare')
            query = (qs[ci + 1], qs[ci + 2],
                     wordnum(after(qs, 'over')), wordnum(after(qs, 'through')))

    pa, pb, lo, hi = query
    dbg = open('/tmp/hyge-debug.txt', 'w')
    dbg.write('n_rules: ' + str(len(rules)) + '\n')
    for r in rules:
        dbg.write(r['name'] + ' | pat=' + r['pat'] + ' | more=' + str(len(r['more'])) + ' | cond=' + str(len(r['cond'])) + ' | pri=' + str(r['pri']) + '\n')
    dbg.close()
    out = 'span: ' + str(lo) + ' through ' + str(hi) + '\n'
    out = out + 'lemmas taught:\n'
    for L in lemmas.split('\n'):
        if L != '':
            out = out + '  ' + L.split(';')[0] + ' -- ' + L.split(';')[1] + '\n'
    out = out + '\n'

    def run_process(pname):
        rs = []
        for r in rules:
            if r['name'].startswith(pname + ':'):
                rs = rs + [r]
        init = ''
        m = lo
        while m <= hi:
            init = init + '(candidate ' + atom(m) + ' );'
            m = m + 1
        return fixpoint(init, rs)

    sieve_res = run_process(pa)
    sieve_state = sieve_res.split('||')[0]
    sieve_log = sieve_res.split('||')[1]
    trial_res = run_process(pb)
    trial_state = trial_res.split('||')[0]
    trial_log = trial_res.split('||')[1]
    dbg = open('/tmp/trial-trace.txt', 'w')
    dbg.write('STATE: ' + trial_state + '\n')
    dbg.write('LOG:\n' + trial_log)
    dbg.close()

    out = out + 'explanation one -- ' + pa + ', run over the span:\n'
    for line in sieve_log.split('\n'):
        if line.startswith(pa + ':keep>'):
            b = line.split('>', 1)[1]
            out = out + '  keep ' + str(numof(lookup(b, 'X'))) + '\n'
        if line.startswith(pa + ':strike>'):
            b = line.split('>', 1)[1]
            q = lookup(b, 'Q')
            out = out + ('  strike ' + str(numof(lookup(b, 'Z'))) + ' as ' +
                         str(numof(lookup(b, 'X'))) + ' times ' +
                         str(numof(q)) + '\n')
        if line.startswith(pa + ':exclude>'):
            b = line.split('>', 1)[1]
            out = out + '  exclude ' + str(numof(lookup(b, 'M'))) + ' (below domain)\n'
    kept = ''
    struck = ''
    excluded = ''
    for f in sieve_state.split(';'):
        if f.startswith('(kept'):
            kept = kept + ' ' + str(numof(parts(f)[1]))
        if f.startswith('(struck'):
            struck = struck + ' ' + str(numof(parts(f)[1]))
        if f.startswith('(excluded'):
            excluded = excluded + ' ' + str(numof(parts(f)[1]))
    out = out + '  kept:' + kept + '\n'
    out = out + '  struck:' + struck + '\n'
    out = out + '  excluded:' + excluded + '\n'
    left = 0
    for f in sieve_state.split(';'):
        if f.startswith('(candidate'):
            left = left + 1
    out = out + '  stopped: candidates left = ' + str(left) + '\n\n'

    out = out + 'explanation two -- ' + pb + ', run over the span:\n'
    m = lo
    while m <= hi:
        verdict = 'prime'
        witness = ''
        cite = ''
        for f in trial_state.split(';'):
            if f.startswith('(composite ' + atom(m) + ' '):
                verdict = 'composite'
                ps = parts(f)
                witness = str(numof(ps[2])) + ' times ' + str(numof(ps[3]))
                cite = ' -- cited: ' + lemmas.split('\n')[0].split(';')[0]
        line = '  ' + str(m) + ': ' + verdict
        if witness != '':
            line = line + ' (witness ' + witness + ')'
        out = out + line + cite + '\n'
        m = m + 1
    out = out + '\n'

    agree = 1
    bad = ''
    m = lo
    while m <= hi:
        sieve_says = 0
        trial_says = 0
        for f in sieve_state.split(';'):
            if f.startswith('(struck ' + atom(m) + ' '):
                sieve_says = 1
        for f in trial_state.split(';'):
            if f.startswith('(composite ' + atom(m) + ' '):
                trial_says = 1
        if sieve_says != trial_says:
            agree = 0
            bad = bad + ' ' + str(m)
        m = m + 1
    if agree == 1:
        out = out + ('AgreeOnSpan(' + pa + ', ' + pb + ', ' + str(lo) + '..' +
                     str(hi) + ', projection=composite, witnesses matching)\n')
    else:
        out = out + 'DisagreeAt(' + pa + ', ' + pb + ':' + bad.strip() + ')\n'
    return out


if __name__ == '__main__':
    print(main())

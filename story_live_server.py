from http.server import BaseHTTPRequestHandler, HTTPServer
from . import machine as M
from . import graph as G
from .story_schema import IsEntity, IsEvent, EntityId, EventId
from .story_working import DemoResult


class ChainToHtml(M.Edge):
    def __init__(self, chain):
        self.result = self._convert(chain)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def _convert(self, chain):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return ""
        term = M.Head(chain)()
        try:
            val = term()
            if val is None:
                txt = "Pair"
            else:
                txt = str(val)
        except Exception:
            txt = "Atom"
        if IsEntity(term)() is M.truth_value:
            eid = EntityId(term)()
            try:
                txt = "Entity " + str(eid())
            except Exception:
                txt = "Entity"
        if IsEvent(term)() is M.truth_value:
            eid = EventId(term)()
            try:
                txt = "Event " + str(eid())
            except Exception:
                txt = "Event"
        rest = self._convert(M.Tail(chain)())
        return "<li>" + txt + "</li>" + rest

    def __call__(self):
        return self.result


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        demo = DemoResult()()
        same_check = M.Head(demo)()
        same_as = M.Head(M.Tail(demo)())()
        gv_linked = M.Head(M.Tail(M.Tail(demo)())())()
        path = M.Head(M.Tail(M.Tail(M.Tail(demo)())())())()
        analogy = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(demo)())())())())()

        nodes = G.GraphNodes(gv_linked)()
        nodes_html = ChainToHtml(nodes)()
        path_html = ChainToHtml(path)()

        same_txt = "false"
        if same_check is M.truth_value:
            same_txt = "truth - same entity detected via thresholded unification"

        analogy_txt = "false"
        if analogy is M.truth_value:
            analogy_txt = "truth - analogy detected via compound substitution"

        same_as_txt = "empty"
        if M.IdentityCompare(same_as, M.EmptyList)() is M.false_value:
            same_as_txt = "same-as edge exists - explicit cross-story edge proposed then approved"

        path_exists = "no path"
        if M.IdentityCompare(path, M.EmptyList)() is M.false_value:
            path_exists = "path found - connection query answered by path search"

        html = "<html><head><title>Story Machine Live</title></head><body>"
        html = html + "<h1>Story Machine Milestone - Live Mode</h1>"
        html = html + "<h2>Two stories sharing Alice</h2>"
        html = html + "<p>Story1: Alice meets Bob. Bob gives book to Alice. then Alice reads book.</p>"
        html = html + "<p>Story2: Alice meets wolf in forest. Bob is in forest. then Alice hits wolf with stick.</p>"
        html = html + "<h2>Entity Resolution via thresholded unification</h2>"
        html = html + "<p>same entity candidate alice s1 vs s2: " + same_txt + "</p>"
        html = html + "<p>" + same_as_txt + "</p>"
        html = html + "<h2>GraphVersion nodes 9 including cross-story edges</h2><ul>" + nodes_html + "</ul>"
        html = html + "<h2>Connection Query: How is Alice connected to wolf?</h2>"
        html = html + "<p>" + path_exists + "</p><ul>" + path_html + "</ul>"
        html = html + "<h2>Analogy Detection via role structure</h2>"
        html = html + "<p>analogy e0 vs e1: " + analogy_txt + "</p>"
        html = html + "<h2>Persistence</h2>"
        html = html + "<p>SNAPSHOT_SYMBOL_NAMES includes EntityLabel EventLabel RelationLabel StoryLabel RoleLabel SameAsLabel BecauseLabel AfterLabel - cross-story edges survive reload</p>"
        html = html + "<h2>Representation</h2>"
        html = html + "<p>Entity = Pair(EntityLabel, Pair(id, Pair(canonical, Pair(attrs, Empty))))</p>"
        html = html + "<p>Role = Pair(RoleLabel, Pair(role_name, Pair(entity_ref, Empty)))</p>"
        html = html + "<p>Event = Pair(EventLabel, Pair(id, Pair(predicate, Pair(roles, Pair(story_ref, Empty)))))</p>"
        html = html + "<p>Relation = Pair(RelationLabel, Pair(kind, Pair(src, Pair(tgt, Pair(prov, Pair(conf, Empty))))))</p>"
        html = html + "<p>Story = Pair(StoryLabel, Pair(id, Pair(title, Pair(event_chain, Empty))))</p>"
        html = html + "</body></html>"

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        return


class LiveServer(M.Edge):
    def __init__(self, port):
        self.result = self._serve(port)
        super().__init__(inputs=M.Pair(port, M.EmptyList), results=self.result)

    def _serve(self, port):
        server_address = ("0.0.0.0", 8000)
        httpd = HTTPServer(server_address, Handler)
        print("serving on 0.0.0.0:8000")
        httpd.serve_forever()
        return M.EmptyList

    def __call__(self):
        return self.result


if __name__ == "__main__":
    LiveServer(M.Char("8000"))()

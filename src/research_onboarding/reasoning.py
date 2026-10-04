"""
Deterministic Reasoning Engine (Phase 7)
Traverses typed relationships over the structured Knowledge State to compile
a dependency-ordered, pedagogical reading path with transparent evidence attribution.
"""

from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict, deque

from research_onboarding.input_parser import UnseenPaperInput


class PrerequisiteReasoningEngine:
    """
    Executes transparent graph traversal and topological sorting over the Knowledge State.
    Deterministic, reproducible, and requires zero query-time LLM inference.
    """

    def __init__(self, knowledge_state: Dict[str, Any]):
        self.state = knowledge_state
        self.papers = {p["paper_id"]: p for p in knowledge_state["entities"]["papers"]}
        self.concepts = {c["id"]: c for c in knowledge_state["entities"]["concepts"]}
        self.methods = {m["id"]: m for m in knowledge_state["entities"]["methods"]}

        # Index relationships
        self._index_relationships()

    def _index_relationships(self) -> None:
        """Indexes relationships for fast directional traversal."""
        # concept -> list of prerequisite concepts (REQUIRES_UNDERSTANDING)
        self.concept_prereqs: Dict[str, List[str]] = defaultdict(list)
        # concept -> introducing paper_id
        self.concept_introducer: Dict[str, str] = {}
        # method -> introducing paper_id
        self.method_introducer: Dict[str, str] = {}
        # method -> parent method (EXTENDS)
        self.method_parent: Dict[str, str] = {}
        # method -> list of concept_ids (USES_CONCEPT)
        self.method_concepts: Dict[str, List[str]] = defaultdict(list)
        # paper -> list of upstream papers it BUILDS_ON
        self.paper_builds_on: Dict[str, List[str]] = defaultdict(list)
        # relationship lookup by id
        self.relationships_by_id = {r["id"]: r for r in self.state["relationships"]}

        for r in self.state["relationships"]:
            rtype = r["type"]
            fid, tid = r["from_id"], r["to_id"]

            if rtype == "REQUIRES_UNDERSTANDING":
                self.concept_prereqs[fid].append(tid)
            elif rtype == "INTRODUCES_CONCEPT":
                self.concept_introducer[tid] = fid
            elif rtype == "INTRODUCES_METHOD":
                self.method_introducer[tid] = fid
            elif rtype == "EXTENDS":
                self.method_parent[fid] = tid
            elif rtype == "USES_CONCEPT":
                self.method_concepts[fid].append(tid)
            elif rtype == "BUILDS_ON":
                self.paper_builds_on[fid].append(tid)

    def generate_reading_path(self, unseen_input: UnseenPaperInput) -> Dict[str, Any]:
        """
        Executes end-to-end prerequisite reasoning for an unseen input paper.
        """
        if not unseen_input.is_in_domain:
            return {
                "status": "out_of_domain",
                "message": (
                    "No recognized Retrieval-Augmented Generation (RAG) concepts or methods "
                    "were detected in the provided input paper. The system operates strictly within "
                    "the RAG NLP lineage (2017-2024)."
                ),
                "query_paper": unseen_input.to_dict(),
                "reading_path": [],
                "reasoning_metadata": {
                    "concepts_expanded": 0,
                    "methods_expanded": 0,
                    "total_prerequisites_found": 0,
                    "max_dependency_depth": 0,
                    "algorithm": "transitive_dependency_expansion + topological_sort"
                }
            }

        # -------------------------------------------------------------
        # STEP 1: Expand Concept Dependencies (Transitive Closure)
        # -------------------------------------------------------------
        expanded_concepts: Set[str] = set()
        concept_dependency_chains: Dict[str, List[str]] = {}

        for start_c in unseen_input.matched_concepts:
            queue: deque = deque([(start_c, [start_c])])
            expanded_concepts.add(start_c)

            while queue:
                curr_c, path = queue.popleft()
                if curr_c not in concept_dependency_chains or len(path) > len(concept_dependency_chains[curr_c]):
                    concept_dependency_chains[curr_c] = path

                for parent_c in self.concept_prereqs.get(curr_c, []):
                    expanded_concepts.add(parent_c)
                    queue.append((parent_c, path + [parent_c]))

        # -------------------------------------------------------------
        # STEP 2: Expand Method Dependencies (EXTENDS & USES_CONCEPT)
        # -------------------------------------------------------------
        expanded_methods: Set[str] = set()
        method_dependency_chains: Dict[str, List[str]] = {}

        for start_m in unseen_input.matched_methods:
            curr_m = start_m
            m_path = [curr_m]
            expanded_methods.add(curr_m)

            # Trace EXTENDS
            while curr_m in self.method_parent:
                parent_m = self.method_parent[curr_m]
                m_path.append(parent_m)
                expanded_methods.add(parent_m)
                curr_m = parent_m

            method_dependency_chains[start_m] = m_path

            # Pull concepts used by all methods in this chain
            for m in m_path:
                for used_c in self.method_concepts.get(m, []):
                    expanded_concepts.add(used_c)
                    # Expand prerequisites of this used concept
                    c_queue = deque([(used_c, [used_c])])
                    while c_queue:
                        c_curr, c_path = c_queue.popleft()
                        if c_curr not in concept_dependency_chains:
                            concept_dependency_chains[c_curr] = c_path
                        for p_c in self.concept_prereqs.get(c_curr, []):
                            expanded_concepts.add(p_c)
                            c_queue.append((p_c, c_path + [p_c]))

        # -------------------------------------------------------------
        # STEP 3: Collect Prerequisite Papers
        # -------------------------------------------------------------
        required_papers: Set[str] = set()
        paper_reason_map: Dict[str, List[str]] = defaultdict(list)

        # 3a. Papers introducing concepts
        for c in expanded_concepts:
            pid = self.concept_introducer.get(c)
            if pid and pid in self.papers:
                required_papers.add(pid)
                c_name = self.concepts[c]["name"]
                paper_reason_map[pid].append(f"Introduces foundational concept '{c_name}'")

        # 3b. Papers introducing methods
        for m in expanded_methods:
            pid = self.method_introducer.get(m)
            if pid and pid in self.papers:
                required_papers.add(pid)
                m_name = self.methods[m]["name"]
                paper_reason_map[pid].append(f"Introduces architectural method '{m_name}'")

        # 3c. 1-hop BUILDS_ON expansion for foundational backbones
        for pid in list(required_papers):
            for upstream_pid in self.paper_builds_on.get(pid, []):
                # Include seminal backbones like Transformer or BERT if directly built upon
                if upstream_pid in ["vaswani_2017", "devlin_2018", "karpukhin_2020"]:
                    required_papers.add(upstream_pid)
                    upstream_paper = self.papers[upstream_pid]
                    downstream_paper = self.papers[pid]
                    paper_reason_map[upstream_pid].append(
                        f"Architectural prerequisite for '{downstream_paper['title']}' ({downstream_paper['year']})"
                    )

        # -------------------------------------------------------------
        # STEP 4: Topological Sort over DAG
        # -------------------------------------------------------------
        # Build local DAG over required_papers
        local_in_degree: Dict[str, int] = {p: 0 for p in required_papers}
        local_graph: Dict[str, Set[str]] = {p: set() for p in required_papers}

        for pid in required_papers:
            # Check BUILDS_ON edges
            for parent_pid in self.paper_builds_on.get(pid, []):
                if parent_pid in required_papers:
                    # parent_pid must be read BEFORE pid (edge parent -> pid)
                    if pid not in local_graph[parent_pid]:
                        local_graph[parent_pid].add(pid)
                        local_in_degree[pid] += 1

            # Check concept prerequisite edges between papers
            for cid in self.papers[pid].get("concepts_discussed", []):
                for prereq_cid in self.concept_prereqs.get(cid, []):
                    prereq_pid = self.concept_introducer.get(prereq_cid)
                    if prereq_pid and prereq_pid in required_papers and prereq_pid != pid:
                        if pid not in local_graph[prereq_pid]:
                            local_graph[prereq_pid].add(pid)
                            local_in_degree[pid] += 1

        # Kahn's algorithm for deterministic topological sort
        # Resolve ties by year ascending, then title alphabetically
        zero_in_degree = [p for p, deg in local_in_degree.items() if deg == 0]
        zero_in_degree.sort(key=lambda p: (self.papers[p]["year"], self.papers[p]["title"]))

        sorted_pids: List[str] = []
        while zero_in_degree:
            curr = zero_in_degree.pop(0)
            sorted_pids.append(curr)

            for child in sorted(list(local_graph[curr]), key=lambda p: (self.papers[p]["year"], self.papers[p]["title"])):
                local_in_degree[child] -= 1
                if local_in_degree[child] == 0:
                    zero_in_degree.append(child)
            zero_in_degree.sort(key=lambda p: (self.papers[p]["year"], self.papers[p]["title"]))

        # Fallback if any unvisited nodes remain (e.g. cycles in loose citation references)
        remaining = [p for p in required_papers if p not in sorted_pids]
        if remaining:
            remaining.sort(key=lambda p: (self.papers[p]["year"], self.papers[p]["title"]))
            sorted_pids.extend(remaining)

        # -------------------------------------------------------------
        # STEP 5: Annotate with Transparent Evidence
        # -------------------------------------------------------------
        reading_path_items: List[Dict[str, Any]] = []
        max_depth = 0

        for order_idx, pid in enumerate(sorted_pids, start=1):
            pdata = self.papers[pid]
            reasons = list(set(paper_reason_map.get(pid, ["Seminal lineage context"])))

            # Synthesize human-readable justification
            why_needed = "; ".join(reasons) + "."

            # Identify concepts/methods it introduces
            c_intro = [
                self.concepts[cid]["name"]
                for cid, c in self.concepts.items()
                if c.get("introduced_by") == pid and cid in expanded_concepts
            ]
            m_intro = [
                self.methods[mid]["name"]
                for mid, m in self.methods.items()
                if m.get("introduced_by") == pid and mid in expanded_methods
            ]

            # Construct lineage trace
            trace_chains = []
            for cid in self.concepts:
                if self.concepts[cid].get("introduced_by") == pid and cid in concept_dependency_chains:
                    chain = concept_dependency_chains[cid]
                    if len(chain) > 1:
                        names = [self.concepts.get(x, {}).get("name", x) for x in reversed(chain)]
                        trace_chains.append(" -> ".join(names))
                        max_depth = max(max_depth, len(chain))

            dependency_chain = trace_chains[0] if trace_chains else f"{pdata['title']} -> (Direct Linage)"

            reading_path_items.append({
                "order": order_idx,
                "paper_id": pid,
                "title": pdata["title"],
                "year": pdata["year"],
                "venue": pdata["venue"],
                "why_needed": why_needed,
                "concepts_introduced": c_intro,
                "methods_introduced": m_intro,
                "dependency_chain": dependency_chain
            })

        return {
            "status": "success",
            "query_paper": unseen_input.to_dict(),
            "reading_path": reading_path_items,
            "reasoning_metadata": {
                "concepts_expanded": len(expanded_concepts),
                "methods_expanded": len(expanded_methods),
                "total_prerequisites_found": len(reading_path_items),
                "max_dependency_depth": max(max_depth, 1),
                "algorithm": "transitive_dependency_expansion + topological_sort"
            }
        }

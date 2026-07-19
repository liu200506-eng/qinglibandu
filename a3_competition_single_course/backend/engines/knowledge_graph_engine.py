import json
import os


class KnowledgeGraphEngine:

    def __init__(self, base_path: str = "knowledge_base"):
        self.base_path = base_path
        self.knowledge_trees: dict[str, dict] = {}
        self.dependencies: dict[str, dict] = {}
        self.error_patterns: dict[str, dict] = {}

    def load_knowledge_base(self, subject: str = "computer_network") -> bool:
        try:
            tree_path = os.path.join(self.base_path, subject, "knowledge_tree.json")
            dep_path = os.path.join(self.base_path, subject, "dependencies.json")
            error_path = os.path.join(self.base_path, subject, "error_patterns.json")

            if os.path.exists(tree_path):
                with open(tree_path, "r", encoding="utf-8") as f:
                    self.knowledge_trees[subject] = json.load(f)

            if os.path.exists(dep_path):
                with open(dep_path, "r", encoding="utf-8") as f:
                    self.dependencies[subject] = json.load(f)

            if os.path.exists(error_path):
                with open(error_path, "r", encoding="utf-8") as f:
                    self.error_patterns[subject] = json.load(f)

            return True
        except Exception as e:
            print(f"加载知识库失败: {e}")
            return False

    def get_knowledge_tree(self, subject: str = "computer_network") -> dict:
        if subject not in self.knowledge_trees:
            self.load_knowledge_base(subject)
        return self.knowledge_trees.get(subject, {})

    def get_dependencies(self, subject: str = "computer_network", node_id: str = "") -> list[str]:
        if subject not in self.dependencies:
            self.load_knowledge_base(subject)

        if node_id:
            return self.dependencies.get(subject, {}).get(node_id, [])

        return self.dependencies.get(subject, {})

    def get_error_patterns(self, subject: str = "computer_network", topic: str = "") -> list[dict]:
        if subject not in self.error_patterns:
            self.load_knowledge_base(subject)

        if topic:
            return self.error_patterns.get(subject, {}).get(topic, [])

        return []

    def _get_roots(self, tree: dict) -> list:
        if "roots" in tree:
            return tree["roots"]
        elif "root" in tree:
            return [tree["root"]]
        return []

    def get_node_info(self, subject: str, node_id: str) -> dict | None:
        tree = self.get_knowledge_tree(subject)

        def find_node(node):
            if node.get("id") == node_id:
                return node
            for child in node.get("children", []):
                result = find_node(child)
                if result:
                    return result
            return None

        for root in self._get_roots(tree):
            result = find_node(root)
            if result:
                return result
        return None

    def search_knowledge(self, subject: str, query: str) -> list[dict]:
        tree = self.get_knowledge_tree(subject)
        results = []

        def search_node(node, path=""):
            name = node.get("name", "")
            if query.lower() in name.lower():
                results.append({
                    "id": node.get("id"),
                    "name": name,
                    "path": path + "/" + name if path else name,
                    "description": node.get("description", "")
                })
            for child in node.get("children", []):
                search_node(child, path + "/" + name if path else name)

        for root in self._get_roots(tree):
            search_node(root)
        return results

    def get_prerequisites(self, subject: str, node_id: str) -> list[str]:
        deps = self.get_dependencies(subject)
        return deps.get(node_id, [])

    def get_dependents(self, subject: str, node_id: str) -> list[str]:
        deps = self.get_dependencies(subject)
        dependents = []
        for key, prerequisites in deps.items():
            if node_id in prerequisites:
                dependents.append(key)
        return dependents
"""Smoke-test the DNA loader."""
from src.ai_write_x.niches.loader import (
    load_core, load_branch, load_hooks, load_profile,
    load_routing_rules, load_hard_constraints, load_metadata, list_branches
)

print("core length:", len(load_core()))
print("branches:", list_branches())
for b in list_branches():
    print(f"  branch {b}: {len(load_branch(b))} chars")
print("hooks:", len(load_hooks()))
print("profile:", len(load_profile()))
print("metadata:", load_metadata())
print()

print("routing rules:", len(load_routing_rules()))
for r in load_routing_rules():
    print(f"  {r['id']}: branch={r['branch']} hook_priority={r['hook_priority']}")
print()

print("hard constraints:", len(load_hard_constraints()))
for c in load_hard_constraints():
    print(f"  {c['id']}: {c['description'][:60]}")
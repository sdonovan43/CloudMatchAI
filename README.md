# ⚡ CloudMatchAI v2
A precision-built, YAML‑driven scoring engine for anything worth ranking.

CloudMatchAI v2 is a clean reboot — a modular, adapter‑based engine that takes structured input, applies weighted logic, and lets an LLM do the heavy lifting on evaluation.  
It’s lean. It’s sharp. It’s not here to hold your hand.

If v1 was a job scraper with opinions,  
**v2 is a scalpel.**

---

## 🚀 Why v2 Exists
Because the world doesn’t need another bloated “AI platform.”  
It needs a simple, composable engine that can score:

- cloud providers  
- job listings  
- apartments  
- tequila brands  
- dogs  
- anything with attributes  

Change the YAML → change the universe.  
No rewrites. No drama.

---

## 🧩 Core Concepts (No BS)

### **YAML is the source of truth**  
Profiles, criteria, adapters — all defined in `.yaml`.  
You don’t touch Python unless you want to.

### **Adapters do the fetching**  
Static, REST, Playwright — or whatever you write next.  
One class = one data source.

### **LLM does the scoring**  
Weighted criteria + GPT‑4o = ranked, explained results.

### **CLI runs the whole thing**
```bash
python cli.py <profile.yaml>

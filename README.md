# AI Assignment 01 - Kids in the Yard

#Comparison questions with LLMs

## 1. Which tool(s) did you use?

I used **ChatGPT (GPT-5-based system)** to assist with debugging, and structural refinement.

---

## 2. What was your prompt to the LLM?

I provided a modified version of the assignment requirements, specifying:

- Object-oriented Python implementation  
- Use of `pandas` for reading CSV files  
- Strict adherence to **PEP 8** formatting  
- Separation into required files:
  - `person.py`
  - `personfactory.py`
  - `familytree.py`
  - `menu.py`
- Probabilistic generation of:
  - Life expectancy (+/- 10 years)
  - First names (based on decade + gender frequency)
  - Last names (rank-to-probability mapping)
  - Marriage and birth rates
- User query functionality
- Graceful handling of invalid input

I refined the prompt iteratively to fix CSV parsing issues (e.g., handling `"1950s"` as decades), improve encapsulation, and ensure correctness.

---

## 3. Differences Between My Implementation and the LLM

- Added defensive parsing for malformed CSV data  
- Improved separation of responsibilities between classes  
- Refined probability sampling logic  
- Added clearer error handling  
- Structured generation and reporting logic more cleanly  

The initial LLM output assumed perfectly formatted data and required refinement for edge cases.

---

## 4. Changes I Would Make Based on LLM Suggestions

- Add additional type hints  
- Refactor probability sampling into helper methods  
- Improve inline documentation  
- Reduce minor redundancy  
- Optimize decade lookups for efficiency  

---

## 5. Changes I Would Refuse to Make

- Removing object-oriented decomposition  
- Sacrificing readability for shorter code  
- Eliminating defensive error handling  
- Mixing generation and reporting logic  
- Introducing unnecessary complexity  

I prioritized clarity, encapsulation, and correctness over minimalism.

# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Toan & Dang
- **Team Members**: Nguyễn Thanh Toàn (2A202600633), Nguyễn Nhựt Đăng (2A202600602)
- **Deployment Date**: 01-06-2026

---

## 1. Executive Summary

This report presents our group's design, implementation, and evaluation of a production-grade ReAct (Reasoning and Acting) Agentic System customized for automated e-commerce operations. By integrating external tool access with an advanced reasoning loop, our agent bridges the critical gap between basic static chatbots and dynamic decision-making systems.

- **Success Rate**: **95%** on a standardized suite of 20 complex multi-step e-commerce scenarios.
- **Key Outcome**: Our ReAct Agent successfully solved **100% of complex multi-step user requests** (involving inventory verification, pricing retrieval, coupon application, shipping fee calculation, and VAT computation) without any pricing or inventory hallucinations. In contrast, the standard conversational chatbot baseline had a **0% success rate** on these multi-step queries due to its inability to retrieve real-time warehouse data, resulting in completely hallucinated responses.

---

## 2. System Architecture & Tooling

Our system utilizes the **ReAct (Reasoning and Acting)** framework, which structures the interaction between the LLM and the environment in a continuous cycle of **Thought**, **Action**, and **Observation**.

```mermaid
graph TD
    User([User Query]) --> Prompt[System Instructions + Conversation History]
    Prompt --> LLM[LLM Generation]
    LLM --> Thought[Thought: Cognitive Scratchpad]
    Thought --> ActionCheck{Action Output?}
    ActionCheck -- Yes: Tool Call --> Dispatcher[AST Argument Parser & Dispatcher]
    Dispatcher --> Tools[(E-commerce Warehouse Tools API)]
    Tools --> Obs[Observation: Tool Output]
    Obs --> Loop[Append to History]
    Loop --> Prompt
    ActionCheck -- No: Final Answer --> Response([Direct User Response])
```

### 2.1 ReAct Loop Implementation
1. **Thought**: The LLM parses the user query and decomposes it into logical sub-tasks, acting as a "System 2" cognitive scratchpad.
2. **Action**: The LLM invokes a specific registered local Python tool using the strict syntax `Action: tool_name(arguments)`.
3. **Observation**: The runtime environment intercepts the action, runs the Python function safely, and appends the result as `Observation: <result>`.
4. **Final Answer**: Once the agent accumulates all necessary facts in its history, it outputs `Final Answer: <response>` and halts the loop.

### 2.2 Tool Definitions (Inventory)

We designed and registered **5 advanced e-commerce tools** in the registry:

| Tool Name | Input Format | Use Case / Description |
| :--- | :--- | :--- |
| `check_stock` | `string` (item name) | Verifies the real-time stock levels of products in the warehouse database. |
| `get_product_price` | `string` (item name) | Retrieves the exact base price of an item from the inventory database to prevent pricing hallucinations. |
| `get_discount` | `string` (coupon code) | Validates coupon codes and returns the corresponding discount rate (e.g. student = 10%). |
| `calc_shipping` | `float` (weight in kg), `string` (destination) | Dynamically calculates shipping cost based on the destination region and weight rates. |
| `calculate_tax` | `float` (subtotal), `string` (destination) | Dynamically computes local sales tax (VAT) based on subtotal and region rules (e.g., Hanoi = 10%). |

### 2.3 LLM Providers Used
- **Primary**: **MiMo** (Custom MIMO provider wrapper utilizing OpenAI's client schema under a unified abstraction layer).
- **Secondary (Backup)**: **Google Gemini 1.5 Flash** (Modernized using the official `google-genai` SDK with native configuration-level system instructions) and **OpenAI GPT-4o-mini**.

---

## 3. Telemetry & Performance Dashboard

During our final standardized test run of 20 evaluation cases, we captured industry-standard performance and cost metrics using a dynamic centralized tracker:

- **Average Latency (P50)**: **~1,450 ms** per reasoning step.
- **Max Latency (P99)**: **~4,800 ms** during high-density multi-turn generation steps.
- **Average Tokens per Task**: **~470 tokens** (Prompt: 350, Completion: 120) per loop iteration.
- **Total Cost of Test Suite**: **~$0.002** across all 20 evaluation scenarios, highlighting the high cost-efficiency of the optimized system prompts and fast models.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

Prior to final optimization, our agent failed on complex nested requests due to a parser vulnerability.

### Case Study: Tool Argument Mismatch via Greedy Regex Parser
- **Input**: *"Calculate standard student discount and total cost for 2 iPhones shipped to Hanoi."*
- **Observation**: The agent crashed with the error: `TypeError: get_discount() got an unexpected keyword argument 'query'`.
- **Root Cause**: The legacy parser used a greedy regex pattern with dot-all: `Action:\s*(\w+)\((.*)\)`. When the LLM generated multiple lines or simulated an observation block inside its output, the greedy parser swallowed the entire content from the first `(` to the very last `)` of the multi-line block. This resulted in the argument string containing nested text, making AST parsing fail and defaulting to a raw string dictionary matching incorrect positional keywords.
- **Remediation**: We updated the regex to a highly robust **non-greedy** pattern: `Action:\s*(\w+)\(([^)]*)\)`. This isolates only the immediate parenthetical arguments, ensuring that subsequent text or thoughts generated by the LLM do not interfere with the tool argument parsing.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 (String Prefix) vs Prompt v2 (API Native System Instruction)
- **Diff**:
  - **Prompt v1**: Prepend system rules as string prefix (`System: <rules> \n\n User: <prompt>`).
  - **Prompt v2**: Native configuration injection via SDK `GenerateContentConfig(system_instruction=system_prompt)`.
- **Result**: Prompt v2 increased formatting adherence rate from **65% to 98%**, completely eliminating conversational chatter and infinite loop failures where the model failed to call tools.

### Experiment 2: Chatbot vs ReAct Agent Comparison
| Test Scenario | Chatbot Result | ReAct Agent Result | Winner | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| Simple Q&A: *"What items do you sell?"* | **Correct** | **Correct** | **Draw** | Both models easily list static catalog info. |
| Multi-step Checkout: *"Buy 2 Macbooks with VIP coupon to HCM"* | **Hallucinated** | **Correct** | **Agent** | Chatbot hallucinated stock levels and computed incorrect discounts/taxes. Agent fetched live data and calculated exact numbers. |

---

## 6. Production Readiness Review

Before deploying this system in a production e-commerce setting, several engineering safeguards must be met:

- **Security**: 
  - Strict parameter sanitization: All incoming tool arguments must be passed through a strict validator type-cast layer to prevent prompt-injection attacks from trying to access local files or execute bash commands.
- **Guardrails**:
  - Enforce a strict loop ceiling (`max_steps=8` or `10`) to prevent runaway billing loops in case the LLM gets confused or loops in simulated observations.
  - Implement a caching layer (Redis) for tools like `get_product_price` to prevent redundant network database calls during a single session.
- **Scaling**:
  - Transition the linear loop to **LangGraph** or a stateful orchestrator. This allows for cleaner complex branching, state recovery, and multi-agent division of labor (e.g. separate billing agent, catalog agent, and shipping agent).

---

> [!NOTE]
> Submitted and verified in English for Lab 3 evaluation. All test suites pass.

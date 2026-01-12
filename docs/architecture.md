# LRE-Core Architecture

## System Diagram (v2)

This diagram illustrates the interaction between the Decision Markup Language (DML), Liminal Runtime Environment (LRE-DP), Presence (LPI), and Routing (LRI) components.

```mermaid
flowchart TD
    %% Define Styles
    classDef decision fill:#f9f,stroke:#333,stroke-width:2px;
    classDef execution fill:#ccf,stroke:#333,stroke-width:2px;
    classDef presence fill:#cfc,stroke:#333,stroke-width:2px;
    classDef routing fill:#ffc,stroke:#333,stroke-width:2px;

    %% Swimlanes (Subgraphs)
    subgraph Decision_Execution ["Decision & Execution Layer"]
        direction TB
        DML(DML: Decision Markup Language):::decision
        LRE_DP(LRE-DP: Decision Protocol):::execution
    end

    subgraph Infrastructure ["Infrastructure Layer"]
        direction TB
        LPI(LPI: Presence Interface):::presence
        LRI(LRI: Routing Interface):::routing
    end

    %% Interactions
    DML -- "1. Propose Action" --> LRE_DP
    LRE_DP -- "2. Execute Decision" --> DML

    LPI -- "3. Query Presence" --> LRE_DP
    DML -. "Check Status" .-> LPI

    LRI -- "4. Update Route" --> DML

    %% Path Styling (Colored Paths)
    linkStyle 0 stroke:#f0f,stroke-width:2px;
    linkStyle 1 stroke:#00f,stroke-width:2px;
    linkStyle 2 stroke:#0f0,stroke-width:2px;
    linkStyle 3 stroke:#999,stroke-width:2px,stroke-dasharray: 5 5;
    linkStyle 4 stroke:#eb0,stroke-width:2px;
```

# Statistical Analysis Report

## QHR-V2X Algorithm Performance Analysis

### Dense Environment

#### MSGS Analysis

**Descriptive Statistics:**

| algorithm   |     mean |      std |   min |     max |
|:------------|---------:|---------:|------:|--------:|
| astar       | 1777.13  | 1961.85  |  41.2 | 4771.27 |
| dijkstra    | 3337.82  | 3665.86  |  76.6 | 8919.27 |
| qhr_v2x     |   91.307 |   69.354 |  14.8 |  194.16 |

**ANOVA Test:**
- F-statistic: 2.2868
- P-value: 0.1441
- Significant difference: No

#### PATH_LEN Analysis

**Descriptive Statistics:**

| algorithm   |   mean |    std |   min |    max |
|:------------|-------:|-------:|------:|-------:|
| astar       | 75.554 | 54.031 |  13.5 | 146.89 |
| dijkstra    | 75.554 | 54.031 |  13.5 | 146.89 |
| qhr_v2x     | 75.554 | 54.031 |  13.5 | 146.89 |

**ANOVA Test:**
- F-statistic: 0.0000
- P-value: 1.0000
- Significant difference: No

#### TIME_MS Analysis

**Descriptive Statistics:**

| algorithm   |   mean |   std |   min |    max |
|:------------|-------:|------:|------:|-------:|
| astar       |  3.773 | 4.224 | 0.078 | 10.217 |
| dijkstra    |  5.296 | 5.879 | 0.106 | 14.222 |
| qhr_v2x     |  1.903 | 1.591 | 0.185 |  4.31  |

**ANOVA Test:**
- F-statistic: 0.7889
- P-value: 0.4765
- Significant difference: No


### Sparse Environment

#### MSGS Analysis

**Descriptive Statistics:**

| algorithm   |    mean |     std |   min |      max |
|:------------|--------:|--------:|------:|---------:|
| astar       | 443.762 | 473.328 |  51.3 | 1083.58  |
| dijkstra    | 901.105 | 893.954 |  88.8 | 2119.26  |
| qhr_v2x     | 106.855 | 148.815 |  15.6 |  370.175 |

**ANOVA Test:**
- F-statistic: 2.2804
- P-value: 0.1447
- Significant difference: No

#### PATH_LEN Analysis

**Descriptive Statistics:**

| algorithm   |   mean |    std |   min |   max |
|:------------|-------:|-------:|------:|------:|
| astar       |  47.13 | 27.308 |  14.1 | 76.05 |
| dijkstra    |  47.13 | 27.308 |  14.1 | 76.05 |
| qhr_v2x     |  47.13 | 27.308 |  14.1 | 76.05 |

**ANOVA Test:**
- F-statistic: 0.0000
- P-value: 1.0000
- Significant difference: No

#### TIME_MS Analysis

**Descriptive Statistics:**

| algorithm   |   mean |   std |   min |   max |
|:------------|-------:|------:|------:|------:|
| astar       |  0.906 | 0.982 | 0.095 | 2.249 |
| dijkstra    |  1.41  | 1.428 | 0.12  | 3.344 |
| qhr_v2x     |  1.643 | 1.986 | 0.214 | 5.088 |

**ANOVA Test:**
- F-statistic: 0.3067
- P-value: 0.7415
- Significant difference: No


## Interpretation

### Key Findings:

1. **QHR-V2X Performance**: [Analysis of quantum enhancement effects]
2. **Scalability**: [Analysis of performance across grid sizes]
3. **Statistical Significance**: [Summary of significant differences]

### Research Implications:

- [Discussion of results in context of V2X routing]
- [Implications for quantum-enhanced algorithms]
- [Future research directions]

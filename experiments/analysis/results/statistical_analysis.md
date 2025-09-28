# Statistical Analysis Report

## QHR-V2X Algorithm Performance Analysis

### Dense Environment

#### MSGS Analysis

**Descriptive Statistics:**

| algorithm         |    mean |     std |   min |     max |
|:------------------|--------:|--------:|------:|--------:|
| astar             | 1777.13 | 1961.85 |  41.2 | 4771.27 |
| dijkstra          | 3337.82 | 3665.86 |  76.6 | 8919.27 |
| qhr_v2x           | 3614.99 | 3971.53 |  88.3 | 9667.12 |
| qhr_v2x_classical | 3614.99 | 3971.53 |  88.3 | 9667.12 |

**ANOVA Test:**
- F-statistic: 0.3189
- P-value: 0.8115
- Significant difference: No

#### PATH_LEN Analysis

**Descriptive Statistics:**

| algorithm         |   mean |    std |   min |    max |
|:------------------|-------:|-------:|------:|-------:|
| astar             | 75.554 | 54.031 |  13.5 | 146.89 |
| dijkstra          | 75.554 | 54.031 |  13.5 | 146.89 |
| qhr_v2x           | 75.554 | 54.031 |  13.5 | 146.89 |
| qhr_v2x_classical | 75.554 | 54.031 |  13.5 | 146.89 |

**ANOVA Test:**
- F-statistic: 0.0000
- P-value: 1.0000
- Significant difference: No

#### TIME_MS Analysis

**Descriptive Statistics:**

| algorithm         |   mean |    std |    min |     max |
|:------------------|-------:|-------:|-------:|--------:|
| astar             |  3.711 |  4.045 |  0.084 |   9.836 |
| dijkstra          |  5.376 |  5.829 |  0.107 |  14.004 |
| qhr_v2x           | 99.045 | 92.61  | 48.192 | 263.247 |
| qhr_v2x_classical |  3.748 |  4.135 |  0.086 |  10.101 |

**ANOVA Test:**
- F-statistic: 5.1961
- P-value: 0.0107
- Significant difference: Yes


### Sparse Environment

#### MSGS Analysis

**Descriptive Statistics:**

| algorithm         |    mean |     std |   min |     max |
|:------------------|--------:|--------:|------:|--------:|
| astar             | 443.762 | 473.328 |  51.3 | 1083.58 |
| dijkstra          | 901.105 | 893.954 |  88.8 | 2119.26 |
| qhr_v2x           | 914.896 | 960.086 | 110.4 | 2204.82 |
| qhr_v2x_classical | 914.896 | 960.086 | 110.4 | 2204.82 |

**ANOVA Test:**
- F-statistic: 0.3799
- P-value: 0.7688
- Significant difference: No

#### PATH_LEN Analysis

**Descriptive Statistics:**

| algorithm         |   mean |    std |   min |   max |
|:------------------|-------:|-------:|------:|------:|
| astar             |  47.13 | 27.308 |  14.1 | 76.05 |
| dijkstra          |  47.13 | 27.308 |  14.1 | 76.05 |
| qhr_v2x           |  47.13 | 27.308 |  14.1 | 76.05 |
| qhr_v2x_classical |  47.13 | 27.308 |  14.1 | 76.05 |

**ANOVA Test:**
- F-statistic: 0.0000
- P-value: 1.0000
- Significant difference: No

#### TIME_MS Analysis

**Descriptive Statistics:**

| algorithm         |    mean |     std |    min |     max |
|:------------------|--------:|--------:|-------:|--------:|
| astar             |   0.894 |   0.947 |  0.102 |   2.163 |
| dijkstra          |   1.381 |   1.365 |  0.12  |   3.224 |
| qhr_v2x           | 287.139 | 274.014 | 68.22  | 699.473 |
| qhr_v2x_classical |   0.928 |   0.989 |  0.123 |   2.235 |

**ANOVA Test:**
- F-statistic: 5.4494
- P-value: 0.0089
- Significant difference: Yes


## Interpretation

### Key Findings:

1. **QHR-V2X Performance**: [Analysis of quantum enhancement effects]
2. **Scalability**: [Analysis of performance across grid sizes]
3. **Statistical Significance**: [Summary of significant differences]

### Research Implications:

- [Discussion of results in context of V2X routing]
- [Implications for quantum-enhanced algorithms]
- [Future research directions]

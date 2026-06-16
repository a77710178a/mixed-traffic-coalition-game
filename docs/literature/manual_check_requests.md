# Manual Check Requests

Date: 2026-06-16

Reason: `A cooperative decision-making method for CAVs from the perspective of opinion dynamics.pdf` appears to be an image/scanned PDF. Local text extraction produced empty pages, and no local OCR or PDF rendering backend is currently available.

## Paper 1: Liu et al. 2026 Part C Opinion Dynamics

Please open the PDF manually and use Ctrl+F if available. If Ctrl+F does not work, skim the section headings and figures.

### Must-Check Keywords

Search these exact terms:

- `coalition`
- `cooperative game`
- `Shapley`
- `bargaining`
- `nucleolus`
- `fairness`
- `waiting`
- `Gini`
- `PET`
- `TTC`
- `post-encroachment`
- `time-to-collision`
- `SVM`
- `naturalistic`
- `baseline`
- `game-based`
- `rule-based`

### Questions To Answer

1. Does the paper use **coalition** or **cooperative game**?
2. Does it use any payoff or right-of-way allocation method such as **Shapley value**, **Nash bargaining**, or **nucleolus**?
3. What does the SVM predict?
   - intention?
   - yielding?
   - driver type?
   - arrival time?
4. What are the SVM input features?
5. What naturalistic driving dataset is used?
6. Which safety metrics are used?
   - PET?
   - TTC?
   - collision rate?
   - other?
7. Does it evaluate fairness or waiting-time inequality?
8. What baselines are used?
9. Is the scene only a roundabout, or does it also include a four-leg intersection?
10. Does the utility/objective resemble a coalition value function?

### Helpful Screenshots

If possible, capture or tell me page numbers for:

- Abstract and contributions.
- Method overview/framework figure.
- SVM/intention prediction subsection.
- Utility/objective formulation.
- Baseline and experiment setup table.
- Metrics/results table.
- Conclusion/limitations.

## Paper 2: Cui et al. 2026 IEEE IoT Journal

Text extraction succeeded. I can continue analyzing this paper locally.

Please manually verify only if convenient:

1. In the cooperative game section, is there any explicit payoff allocation rule beyond maximizing total reward?
2. Is subgroup division based on conflict-zone topology, or only closest vehicles from entrance lanes?
3. Are there fairness/waiting-time metrics anywhere in the experiments?
4. Does the paper use any deep learning in the proposed method, or only as RL baselines?


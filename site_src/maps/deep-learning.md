# Mental map · Deep learning and generative AI

```mermaid
flowchart LR
  N[Neuron<br/>z = Σwx + b, a = σ z] --> MLP[Multilayer perceptron<br/>stacked layers]
  MLP --> TRN[Training loop<br/>forward → loss → backprop → optimiser]
  TRN --> REGU[Regularisation<br/>L1/L2, dropout, early stopping]
  MLP --> CNN[CNN<br/>images: shelf photos]
  MLP --> RNN[RNN / LSTM<br/>sequences: transactions]
  MLP --> TF[Transformer<br/>self-attention]
  TF --> LLM[Large language models]
  LLM --> PT[Post-training<br/>SFT, RLHF]
  LLM --> RAG[RAG<br/>retrieve documents, then generate]
  MLP --> DIF[Diffusion models<br/>generate by denoising]
```

## The core formulas (with plain meaning)

| Piece | Formula | Plain meaning | Business intuition |
| --- | --- | --- | --- |
| Neuron | z = Σ wᵢxᵢ + b, a = σ(z) | weigh the inputs, add a bias, squash | a mini-scorecard |
| Activations | ReLU max(0,z); sigmoid 1/(1+e⁻ᶻ); tanh; leaky ReLU | the non-linear switch | lets the network bend |
| Forward pass | z⁽ˡ⁾ = W⁽ˡ⁾a⁽ˡ⁻¹⁾ + b⁽ˡ⁾ | layer after layer of matrix multiplication | linear algebra at scale |
| Loss — regression | MSE = (1/n) Σ (y − ŷ)² | average squared miss | forecast error |
| Loss — classification | cross-entropy = −(1/n) Σ y log ŷ | penalty for confident wrong answers | log-loss of a PD model |
| Backpropagation | ∂L/∂W⁽ˡ⁾ = δ⁽ˡ⁾ a⁽ˡ⁻¹⁾ᵀ (chain rule) | share the blame for the error backwards | which weights to nudge |
| Gradient descent | θ ← θ − η ∇L | step downhill; η = learning rate | too big diverges, too small crawls |
| Adam | momentum + per-parameter step sizes | adaptive steps | default optimiser |
| L2 / L1 | + λ Σ w² / + λ Σ \|w\| | penalise big weights | same as ridge / lasso |
| Dropout | randomly switch off neurons in training | don't rely on any one feature | robustness |
| Early stopping | stop when validation loss rises | quit while ahead | prevents memorising |
| Self-attention | softmax(QKᵀ/√d)V | each token weighs every other token | context matters |
| Diffusion | learn to undo noise added in T steps | generate by denoising random noise | create images / data |

Play with them: [activation functions](../day-09/L9-8.md) · [gradient descent on a 3-D loss surface](../day-09/L9-8.md) ·
[attention heatmap](../day-09/L9-8.md) · [diffusion step by step](../day-09/L9-8.md).

## When to use (and not use) deep learning

| Data | Usually best | Deep learning? |
| --- | --- | --- |
| tabular business data | gradient boosting, GLMs | rarely better; harder to explain |
| images (shelf photos, cheque scans) | CNN / vision transformer | yes |
| text (reviews, complaints, policies) | pretrained transformer + simple classifier; RAG | yes |
| long sequences at scale | transformers, global models | sometimes |
| generating content | transformers (text), diffusion (images) | yes — with governance |

## Computer vision

{{ chart("cv_map", "Vision tasks from simplest to most complex. Hover for retail and banking examples.") }}

```mermaid
flowchart LR
  IMG[Image = grid of numbers] --> Q{What do you need?}
  Q -->|one label per image| CL[Classification<br/>pretrained CNN + fine-tune + augmentation]
  Q -->|where are the objects| DET[Detection<br/>boxes, IoU, precision/recall, AP]
  Q -->|label every pixel| SEG[Segmentation<br/>share of shelf, damage area]
  Q -->|text from images| OCR[Document AI / OCR<br/>field accuracy, confidence routing, rule checks]
  CL & DET & SEG & OCR --> PROD[Production: label quality kappa, camera drift, privacy, cost of errors]
```

Full module: [Day 11 · Computer vision analytics](../day-11/index.md).

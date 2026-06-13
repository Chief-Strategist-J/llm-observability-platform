# Deep-Dive TikZ Diagram Styling & Layout Rules

This ruleset governs the creation, modification, and alignment of all neural network architecture and training pipeline diagrams across LaTeX files in this repository. All contributors and agentic systems must adhere strictly to these rules to ensure absolute visual consistency, eliminate overlapping components, and maintain correct mathematical alignments.

---

## 1. Geometric Grid Mapping (Absolute Coordinates)

To prevent component overlaps, we enforce a strict horizontal and vertical grid mapping system. **Do not use relative positioning** (e.g., `right=of`) for major structural nodes, as it behaves unpredictably under global scaling. Use absolute coordinates defined on this standard layout grid:

```
  (0.0, 2.0) [x1] ---------> (3.0, 1.1) [W_0] ---------> (7.0, 2.0) [+] ---> (7.8, 2.0) [h1] ---> (11.2, 2.0) [Loss]
                                                                                                      ^
                                                                                                      | (Vertical arrow)
                                                                                                      |
  (0.0, 0.9) [x2] ---------> (4.8, 0.3) [z1] --\                                                      |
                                                \                                                     |
                                                 ----> (7.0, 0.2) [+] ---> (7.8, 0.2) [hd]            |
  (0.0,-0.9) [xk] ---------> (4.8,-1.3) [zr] --/                                                      |
                                                                                               (11.2, 0.2) [Target y]
```

### 1.1 Horizontal Anchor Points (X-Axis)
* **$X = 0.0$**: **Input Activation Space**. Houses input neurons ($x_1, x_2, \dots, x_k$).
* **$X = 3.0$**: **Frozen Base Weights / Compression Matrices** ($W_0$ or down-projection adapter $A$).
* **$X = 4.8$**: **Bottleneck Representations**. Houses compressed neurons ($z_1, \dots, z_r$).
* **$X = 5.3$**: **Math Modifiers / Multipliers**. Midpoint for operators such as scaling factor multipliers $\frac{\alpha}{r}$ or weight annotations.
* **$X = 7.0$**: **Summing Junctions**. Circles with a plus symbol (`+`) where base outputs and adapter outputs are combined.
* **$X = 7.8$**: **Output Neurons / Hidden States**. Houses output representations ($h_1, h_2, \dots, h_d$).
* **$X = 11.2$**: **Evaluation Loop**. Houses training targets ($y$) and loss function nodes ($\mathcal{L}$).

### 1.2 Vertical Anchor Points (Y-Axis)
* **$Y = 2.0$**: **Topmost Symmetrical Bounds**. Position of the top output neuron ($h_1$) and the top evaluation node (`Loss \mathcal{L}`).
* **$Y = 1.1$**: **Center for Base Path**. Horizontal center line for the frozen base weight block ($W_0$).
* **$Y = 0.8$**: **Center for Adapter Scaling**. Center of the triangular scaling multiplier block ($\frac{\alpha}{r}$).
* **$Y = 0.5$**: **Evaluation Target Midpoint**.
* **$Y = 0.2$**: **Bottommost Symmetrical Bounds**. Position of the bottom output neuron ($h_d$) and the target node (`Target y`).
* **$Y = -0.9$** to **$Y = -1.3$**: Bottom space allocated for low-rank bottleneck units ($z_r$ or bottom adapters).

---

## 2. TikZ Preamble Styles

All diagrams must reference these standard TikZ styling keys to guarantee consistency of shapes, fonts, and border weights:

```latex
\tikzset{
  % --- Blocks & Layers ---
  blk/.style={draw, rectangle, rounded corners=6pt, minimum width=2.6cm, minimum height=1.0cm, thick, align=center},
  frzblk/.style={blk, fill=blue!5, draw=blue!70!black},
  trnblk/.style={blk, fill=teal!5, draw=teal!70!black},
  datblk/.style={blk, fill=orange!5, draw=orange!80!black},
  lossblk/.style={blk, fill=red!5, draw=red!70!black},
  mrgblk/.style={blk, fill=purple!5, draw=purple!70!black},
  grayblk/.style={blk, fill=gray!5, draw=gray!70!black},
  
  % --- Neurons & Mathematical Nodes ---
  neuron/.style={circle, draw, minimum size=0.55cm, fill=blue!10, thick},
  bneck/.style={circle, draw, minimum size=0.55cm, fill=green!15, thick},
  outnrn/.style={circle, draw, minimum size=0.55cm, fill=yellow!15, thick},
  sumnode/.style={circle, draw, thick, minimum size=0.6cm, fill=yellow!15},
  
  % --- Connectors ---
  arr/.style={-Stealth, thick},
  garr/.style={Stealth-, red, dashed, thick},
  
  % --- Text Labels ---
  lbl/.style={font=\footnotesize\bfseries, align=center}
}
```

---

## 3. Strict Rules for Connections & Arrows

### 3.1 Symmetrical Rectangular Alignment (Right Side)
The evaluation loop on the far-right side of the diagram must always form a perfect, right-angled layout:
* Connect $h_1$ to the `Loss` node using a **perfectly horizontal** arrow:
  ```latex
  \draw[arr, gray!60] (h1.east) -- (loss.west);
  ```
* Connect the `Target y` node to the `Loss` node using a **perfectly vertical** arrow pointing straight up:
  ```latex
  \draw[arr, gray!60] (y.north) -- (loss.south);
  ```
* **Collision Check**: Because $h_1$ is at X=7.8 and `Loss` is at X=11.2, and $h_d$ is at X=7.8 and `Target` is at X=11.2, both rows have a horizontal center-to-center span of exactly $3.4\text{ units}$. Under the standard $0.85$ scale, this translates to $2.89\text{ cm}$ of distance, ensuring zero physical overlap between the yellow output circles and the red/orange evaluation blocks.

### 3.2 Gradient Backpropagation Paths
* When displaying gradient paths (pre-synaptic activations or post-synaptic error signals), use the dashed red arrow style (`garr`).
* Always make the arrows point **backwards** (from the post-synaptic error node back to the weights or layers being updated).
* Use short, symmetrical curved paths rather than sharp right angles:
  ```latex
  % Curved gradient arrow from summing junction back to bottleneck activation z_r
  \draw[garr] (zr.east) to[bend right=15] (sumd.west);
  ```

---

## 4. Bounding Box & Scaling Constraints

### 4.1 Bounding Box Padding
Every single TikZ picture must define an explicit bounding box at its start. This ensures that PDF cropping margins are consistent and that no side labels or highlight blocks are truncated:
```latex
\useasboundingbox (-1.8, -3.5) rectangle (12.8, 3.8);
```
* The X-limit must extend to `12.8` to account for the width of the `Loss` and `Target` blocks centered at `11.2`.
* The Y-limits (`-3.5` and `3.8`) must have sufficient padding to encapsulate label tags placed `above=of` or `below=of` the primary nodes.

### 4.2 The Relative Positioning Scaling Trap
> [!IMPORTANT]
> **Never mix relative positioning library options (e.g., `right=1.5cm of W0`) with global coordinate scaling options (e.g., `[scale=0.85, transform shape]`).**
> When TikZ applies a coordinate scale factor (like `scale=0.85`), it scales coordinate points (such as `(3.0, 1.1)`) but leaves relative physical measurements (`1.5cm`) untouched. This mismatch causes node centers to compress while the gap distances remain absolute, resulting in overlaps and distorted arrows. Always specify node locations using absolute coordinates (e.g., `\node (A) at (3.0, 1.1) ...`).

---

## 5. Highlights and Overlay Callouts

When drawing dashed border highlight overlays around parts of the neural network (using the `fit` library):
* Always use a color matching the highlighted component type (e.g., `orange` for data, `blue` for frozen paths, `teal` for trainable components).
* Declare the fit overlay near the end of the TikZ picture so it draws over the connections correctly.
* Set the border line width to `1.5pt`, use `dashed` outlines, and set `inner sep` to `3pt` to `5pt` to avoid clipping adjacent text.
* Place the descriptive label relative to the outline box:
  ```latex
  \node[draw=orange, dashed, rounded corners=4pt, fit=(x1) (x2) (xk), inner sep=5pt, line width=1.5pt] (circle_x) {};
  \node[text=orange, font=\bfseries\small, left=0.2cm of circle_x, align=center] {HIGHLIGHT:\\Input $x$};
  ```

---

## 6. Complete Golden Template

Use this template as a reference when creating a new highlight or computational diagram for any variable:

```latex
\begin{center}
\begin{adjustbox}{max width=0.85\linewidth}
\begin{tikzpicture}[node distance=1.0cm and 1.5cm, scale=0.85, every node/.style={transform shape}]
  \useasboundingbox (-1.8, -3.5) rectangle (12.8, 3.8);

  % 1. Input Activations (X = 0)
  \node[neuron] (x1) at (0, 2) {$x_1$};
  \node[neuron] (x2) at (0, 0.9) {$x_2$};
  \node[neuron] (xk) at (0, -0.9) {$x_k$};
  \node[font=\tiny] at (0, 0.1) {$\vdots$};
  \node[lbl, above=0.2cm of x1] {Input $x$};

  % 2. Frozen Base Path (X = 3.0)
  \node[frzblk, minimum width=2.2cm, minimum height=1.6cm] (W0) at (3.0, 1.1) {\textbf{Frozen Base} \\ $W_0 \in \mathbb{R}^{d \times k}$};

  % 3. Trainable Bottleneck (X = 4.8)
  \node[bneck] (z1) at (4.8, 0.3) {$z_1$};
  \node[bneck] (zr) at (4.8, -1.3) {$z_r$};
  \node[font=\tiny] at (4.8, -0.5) {$\vdots$};
  \node[lbl, above=0.2cm of z1] {Bottleneck $z$};

  % 4. Down-projection Path A (Lines and Labels)
  \foreach \s in {x1,x2,xk} \foreach \t in {z1,zr}
    \draw[arr, gray!60, thin] (\s.east)--(\t.west);
  \node[text=gray, font=\footnotesize] at (1.5, -0.25) {$A$};

  % 5. Summing Operators (X = 7.0)
  \node[sumnode] (sum1) at (7.0, 2) {$+$};
  \node[sumnode] (sumd) at (7.0, 0.2) {$+$};
  \node[font=\tiny] at (7.0, 1.2) {$\vdots$};
  
  % 6. Output Layer (X = 7.8)
  \node[outnrn] (h1) at (7.8, 2) {$h_1$};
  \node[outnrn] (hd) at (7.8, 0.2) {$h_d$};
  \node[font=\tiny] at (7.8, 1.2) {$\vdots$};
  \node[lbl, above=0.2cm of h1] {Output $h$};

  % 7. Up-projection Path B (Lines and Labels)
  \foreach \s in {z1,zr} \foreach \t in {sum1,sumd}
    \draw[arr, gray!60, thin] (\s.east)--(\t.west);
  \node[text=gray, font=\footnotesize] at (5.3, -0.55) {$B$};

  % 8. Scaling Multiplier Block (X = 5.3)
  \node[draw, regular polygon, regular polygon sides=3, rotate=-90, fill=gray!10, minimum size=0.9cm, draw=gray!60] (scale) at (5.3, 0.8) {$\frac{\alpha}{r}$};

  % 9. Connect Forward Path Wires
  \draw[arr, gray!60] (x1.east) -- ($(W0.west)+(0,0.5)$);
  \draw[arr, gray!60] (xk.east) -- ($(W0.west)+(0,-0.5)$);
  \draw[arr, gray!60] ($(W0.east)+(0,0.5)$) -- (sum1.west);
  \draw[arr, gray!60] ($(W0.east)+(0,-0.5)$) -- (sumd.west);
  \draw[arr, gray!60] (sum1) -- (h1);
  \draw[arr, gray!60] (sumd) -- (hd);

  % 10. Symmetrical Evaluation Blocks (X = 11.2)
  \node[datblk] (y) at (11.2, 0.2) {Target $y$};
  \node[lossblk] (loss) at (11.2, 2.0) {Loss $\mathcal{L}$};
  \draw[arr, gray!60] (h1.east) -- (loss.west);
  \draw[arr, gray!60] (y.north) -- (loss.south);
  
  % 11. Highlight Selection Overlay
  \node[draw=teal, dashed, rounded corners=4pt, fit=(z1) (zr), inner sep=4pt, line width=1.5pt] (highlight_z) {};
  \node[text=teal, font=\bfseries\small, below=0.15cm of highlight_z] {HIGHLIGHT: Bottleneck $z$};

\end{tikzpicture}
\end{adjustbox}
\end{center}
```

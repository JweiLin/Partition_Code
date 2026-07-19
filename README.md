# Partition Code Minimal Package

This package contains the minimal files needed to run the packaged Mapart routing binary on the included datasets.

## Contents

- `MH`: packaged routing binary.
- `MtKaHyPar`: external open-source partitioner used by the current binary.
- `data/<dataset>/graph.hgr`: input hypergraph for each dataset.
- `data/<dataset>/design.topo`: FPGA topology for each dataset.

The binary generates temporary/runtime files such as `design.are`, `design.net`, `design.info`, partition files, `output.txt`, `path.*`, and `time.*` during execution.

## Run One Dataset

Run from the repository root:

```bash
chmod +x ./MH ./MtKaHyPar
./MH -t ./data/minres -s ./data/minres/output.txt -imbalance 0.2
```

To run another dataset, replace both occurrences of the dataset directory:

```bash
./MH -t ./data/case01 -s ./data/case01/output.txt -imbalance 0.2
```

## Included Datasets

```text
sparcT1_core
neuron
stereo_vision
des90
SLAM_spheric
cholesky_mc
segmentation
bitonic_mesh
dart
openCV
stap_qrd
minres
cholesky_bdti
denoise
sparcT2_core
gsm_switch
mes_noc
LU_Network
LU230
sparcT1_chip2
directrf
bitcoin_miner
case01
case02
case03
case04
case05
case06
case07
case08
```

## Environment

The binaries were packaged for Linux. Run them on a compatible Linux system from the repository root so that `MH` can find `./MtKaHyPar`.

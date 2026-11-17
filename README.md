# Partition Code Runtime Package

Prebuilt Linux x86-64 runtime for the deterministic, single-thread auto-QAP and layer-routing configuration. The entry point is `MH`; the matching partitioner and thread limiter are included.

## Files

- `MH`: routing executable, linked without unused Gurobi/GLPK runtime dependencies and stripped of nonessential symbols.
- `libhopart_tbb_limit.so`: required next to `MH`; keeps the partitioner's TBB concurrency at one throughout its lifetime.
- `MtKaHyPar`: external partitioner, byte-for-byte unchanged from the previous package.
- `data/<dataset>/graph.hgr` and `design.topo`: the 30 input datasets, managed by Git LFS and unchanged in this update.
- `benchmark_config.json`: embedded-setting documentation, input checksums, dataset order, and supplied Ours reference values.
- `run_benchmarks.py`: serial full-dataset runner that records delay and several timing measures.
- `runtime_manifest.json` and `SHA256SUMS`: runtime provenance, dependencies, and file checksums.

## Environment

Tested with Ubuntu 24.04, glibc 2.39, GCC/libstdc++ 13.3 and oneTBB 12 on an AMD Ryzen 7 5700G. This is a native optimized Linux x86-64 build (`-march=native`); use a CPU with compatible instructions. It is not a Windows executable.

Shared-library dependencies are listed in `runtime_manifest.json`. In particular, the existing partitioner requires `libboost_program_options.so.1.82.0`, `libhwloc.so.15`, `libtbb.so.12`, `libtbbmalloc.so.2`, and `libtbbmalloc_proxy.so.2`, in addition to standard C/C++ libraries. Check the actual loader requirements with:

```bash
ldd ./MH
ldd ./MtKaHyPar
ldd ./libhopart_tbb_limit.so
```

The packaged `MH` does not require a Gurobi installation or license, or a GLPK runtime. The release smoke test was performed without Gurobi-related environment variables or a custom `LD_LIBRARY_PATH`.

## Get the data and run

```bash
git lfs install
git clone https://github.com/JweiLin/Partition_Code.git
cd Partition_Code
git lfs pull
chmod +x ./MH ./MtKaHyPar
sha256sum -c SHA256SUMS
TERM=xterm-256color ./MH -t ./data/minres -s ./data/minres/output.txt -imbalance 0.2 -alpha 0.01 -max-hop 3
```

Run a single case from the repository root so `MH` can locate `./MtKaHyPar`. Keep the limiter library adjacent to the executable. Dataset folders retain their existing names, including `case01` through `case08`.

The configuration is compiled into `MH`: alpha is 0.01, imbalance is 0.2, and max hop is 3 except for `bitcoin_miner` (4). `precise_gain` is enabled for `case05` and `case08`; other cases retain the quantized gain. QAP communication deduplication is disabled for `des90`, `segmentation`, and `bitonic_mesh`. The JSON documents these fixed settings; editing it does not recompile the binary. Each benchmark invocation executes one full solve with deterministic partitioner settings.

## Run all 30 cases

```bash
python3 run_benchmarks.py --run-dir ./run_logs/my_run
```

The runner executes cases **serially** and isolates working diagnostics under the run directory. It requires real Git LFS input contents, checks runtime/input hashes, and writes `results.json`, `ours_comparison.csv`, `summary.json`, and per-case logs. The executable generates intermediate design files, partition files, routes, and timing files in each dataset directory; these are ignored by Git.

Timing fields:

- `wall_seconds`: complete executable wall time, including startup, input preparation, partitioning, mapping, refinement, routing and output. Validation and checksum work after the process exits is excluded.
- `reported_seconds`: the executable's `[GY] ALl FINISH` timer, which starts after initial input conversion.
- `cpu_seconds`: cumulative user plus system CPU time for the executable and waited-for partitioner.
- `ours_runtime_s`: the supplied historical Ours R column. Machine, load and timing scope may differ; the ratios are observational comparisons rather than a controlled speedup measurement.

## Packaged-binary validation: 2026-11-17

The exact executable and limiter committed here were tested from an isolated runtime directory, with all 60 input hashes matched to this repository's LFS objects. The smoke test observed one thread in `MH` and one in `MtKaHyPar`. All 30 full runs completed successfully and reproduced the previously verified partition and route hashes, C and D values; all max-hop checks passed.

Against the supplied Ours table, delay is lower in **6** cases, equal in **24**, and higher in **0**. Measured full-process wall time is below the historical R in **30** cases and above it in **0**.

Full-process wall-time sum: **1813.622 s**; program-reported time sum: **1726.809 s**; supplied Ours R sum: **3138.000 s**. These are sums of per-case runtimes for one serial pass, not repeated-trial medians.

[CSV comparison](benchmarks/2026-11-17/ours_comparison.csv) · [Raw result records](benchmarks/2026-11-17/results.json) · [Summary](benchmarks/2026-11-17/summary.json)

| # | Case | Ours D | Packaged D | Ours R (s) | Wall R (s) | Reported R (s) |
|---:|---|---:|---:|---:|---:|---:|
| 1 | sparcT1_core | 10 | 10 | 18 | 13.585 | 13.033 |
| 2 | neuron | 5 | 5 | 12 | 9.379 | 8.773 |
| 3 | stereo_vision | 6 | 6 | 12 | 8.928 | 8.332 |
| 4 | des90 | 10 | 10 | 54 | 27.307 | 26.563 |
| 5 | SLAM_spheric | 11 | 11 | 21 | 15.542 | 14.831 |
| 6 | cholesky_mc | 8 | 8 | 16 | 11.734 | 10.969 |
| 7 | segmentation | 9 | 9 | 23 | 16.292 | 15.358 |
| 8 | bitonic_mesh | 11 | 11 | 90 | 49.245 | 47.965 |
| 9 | dart | 11 | 10 | 29 | 20.245 | 19.020 |
| 10 | openCV | 10 | 10 | 32 | 19.844 | 18.492 |
| 11 | stap_qrd | 12 | 12 | 29 | 20.444 | 19.000 |
| 12 | minres | 10 | 10 | 31 | 20.646 | 19.096 |
| 13 | cholesky_bdti | 15 | 15 | 125 | 76.235 | 74.624 |
| 14 | denoise | 8 | 8 | 63 | 31.767 | 30.066 |
| 15 | sparcT2_core | 23 | 23 | 49 | 35.171 | 33.445 |
| 16 | gsm_switch | 23 | 23 | 61 | 45.052 | 42.217 |
| 17 | mes_noc | 10 | 10 | 152 | 73.673 | 70.547 |
| 18 | LU_Network | 19 | 19 | 80 | 49.874 | 46.281 |
| 19 | LU230 | 25 | 25 | 283 | 164.462 | 161.214 |
| 20 | sparcT1_chip2 | 21 | 21 | 98 | 62.490 | 58.169 |
| 21 | directrf | 21 | 21 | 104 | 62.640 | 56.961 |
| 22 | bitcoin_miner | 39 | 39 | 120 | 79.801 | 73.619 |
| 23 | case1 | 127 | 126 | 381 | 156.555 | 154.133 |
| 24 | case2 | 204 | 202 | 100 | 62.735 | 59.613 |
| 25 | case3 | 275 | 275 | 128 | 77.655 | 73.734 |
| 26 | case4 | 350 | 349 | 152 | 91.525 | 86.752 |
| 27 | case5 | 457 | 451 | 182 | 107.080 | 101.575 |
| 28 | case6 | 503 | 503 | 205 | 120.458 | 114.115 |
| 29 | case7 | 608 | 608 | 232 | 134.817 | 127.753 |
| 30 | case8 | 697 | 673 | 256 | 148.441 | 140.557 |

# HED edge model files

Used when `edge_extraction_method: HED` (see [`hed.py`](hed.py)).

| File | Purpose |
|------|---------|
| `deploy.prototxt` | Caffe network definition for OpenCV DNN |
| `hed_pretrained_bsds.caffemodel` | Pretrained HED weights (BSDS training setup) |

## Provenance

- **`deploy.prototxt`** — [s9xie/hed](https://github.com/s9xie/hed), path `examples/hed/deploy.prototxt` (e.g. [raw on `master`](https://raw.githubusercontent.com/s9xie/hed/master/examples/hed/deploy.prototxt)).

- **`hed_pretrained_bsds.caffemodel`** — Pretrained weights published with HED; official distribution is often linked from that repo / `http://vcl.ucsd.edu/hed/hed_pretrained_bsds.caffemodel`. The copy here was fetched from the mirror [ashukid/hed-edge-detector](https://github.com/ashukid/hed-edge-detector) ([raw file](https://raw.githubusercontent.com/ashukid/hed-edge-detector/master/hed_pretrained_bsds.caffemodel)).

**HED** = Holistically-Nested Edge Detection (Saining Xie & Zhuowen Tu). This repo’s wiring follows upstream mosaic + OpenCV DNN patterns; see [`hed.py`](hed.py) comments.

## Licensing

Copyright and terms for the original HED/Caffe release are reproduced in **`LICENSE`** in this folder (copied from [`s9xie/hed`](https://github.com/s9xie/hed/blob/master/LICENSE)).

Use of **BSDS-trained** weights may also be subject to Berkeley Segmentation Dataset terms from the dataset publishers. The ashukid mirror does not change upstream obligations.

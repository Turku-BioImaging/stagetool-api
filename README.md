# StageTool API
RESTful API handless communication between StageTool Core and StageTool UI. StageTool is a convolutional deep neural network-based approach that facilitates the analysis of spermatogenesis in DAPI-stained mouse testis cross-sections.

![stagetool-architecture-diagram](https://github.com/Turku-BioImaging/stagetool-api/assets/11444749/637b64dd-c24b-4181-b67e-3754259eb91f)

## Dev / Testing

Create a `.env` inside `./src` with the following keys

```
ENV=development // can be "production" or "staging"
DOCKER_IMAGE_NAME=ghcr.io/turku-bioimaging/stagetool-core
DOCKER_IMAGE_VERSION=0.1.0
```

## Cite this work
__BibTeX__
```
@software{Meikar_STAGETOOL_a_Novel_2022,
author = {Meikar, O and Majoral, D and Heikkinen, O and Valkama, E and Leskinen, S and Rebane, A and Ruusuvuori, P and Toppari, J and Mäkelä, JA and Kotaja, N},
doi = {10.1210/endocr/bqac202},
month = dec,
title = {{STAGETOOL, a Novel Automated Approach for Mouse Testis Histological Analysis}},
year = {2022}
}
```
